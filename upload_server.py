import http.server
import cgi
import tempfile
import os
from zombie_transactions import (
    find_recurring_transactions,
    find_recurring_transactions_from_rows,
    _load_rows,
    _get_month,
)

FORM = """<!doctype html>
<html>
<head>
<title>Zombie Transactions Uploader</title>
<style>
:root {
  --bg: #fff;
  --fg: #000;
  --pre-bg: #f4f4f4;
  color-scheme: light dark;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #121212;
    --fg: #eee;
    --pre-bg: #1e1e1e;
  }
}
body {
  font-family: Arial, sans-serif;
  margin: 0;
  min-height: 100vh;
  background: var(--bg);
  color: var(--fg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 1em;
}
pre {
  background: var(--pre-bg);
  padding: 1em;
}
button {
  padding: 0.5em 1.5em;
  font-size: 1em;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
</head>
<body>
<h1>Upload Transaction File</h1>
<form method="post" enctype="multipart/form-data">
<input type="file" name="csv_file" accept=".csv,.txt,.pdf,.png,.jpg,.jpeg" multiple><br>
<button type="submit">Analyze</button>
</form>
<pre>{output}</pre>
</body>
</html>"""

class UploadHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(FORM.format(output="").encode())

    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers.get("content-type"))
        if ctype != "multipart/form-data":
            self.send_error(400, "Expected multipart/form-data")
            return
        pdict["boundary"] = pdict["boundary"].encode()
        pdict["CONTENT-LENGTH"] = int(self.headers.get("content-length", 0))
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"}, keep_blank_values=True)
        fileitem = form.getlist("csv_file") if "csv_file" in form else []
        if not isinstance(fileitem, list):
            fileitem = [fileitem]
        output = "No file uploaded"
        rows = []
        for item in fileitem:
            if not getattr(item, "file", None):
                continue
            data = item.file.read()
            filename = item.filename or ""
            ext = os.path.splitext(filename)[1].lower()
            binary_exts = (".pdf", ".png", ".jpg", ".jpeg")
            mode = "wb" if ext in binary_exts else "w+"
            with tempfile.NamedTemporaryFile(mode=mode, delete=False) as tf:
                if mode == "wb":
                    tf.write(data)
                else:
                    tf.write(data.decode())
                path = tf.name
            rows.extend(_load_rows(path))
        if rows:
            threshold = self._guess_threshold_rows(rows)
            results = find_recurring_transactions_from_rows(
                rows, months_threshold=threshold, fuzzy=True
            )
            if results:
                output = "\n".join(f"{d}: ${a:.2f}" for d, a in results)
            else:
                output = "No recurring transactions found."
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(FORM.format(output=output).encode())

    def _guess_threshold(self, path: str) -> int:
        rows = _load_rows(path)
        months = set()
        for row in rows:
            month = _get_month(row.get("Date") or row.get("Transaction Date") or "")
            if month:
                months.add(month)
        return max(2, (len(months) + 1) // 2)

    def _guess_threshold_rows(self, rows) -> int:
        months = set()
        for row in rows:
            month = _get_month(row.get("Date") or row.get("Transaction Date") or "")
            if month:
                months.add(month)
        return max(2, (len(months) + 1) // 2)

def run(server_class=http.server.HTTPServer, handler_class=UploadHandler, port=8000):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Serving on http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
