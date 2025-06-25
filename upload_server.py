import http.server
import cgi
import tempfile
from zombie_transactions import find_recurring_transactions

FORM = """<!doctype html>
<html>
<head><title>Zombie Transactions Uploader</title></head>
<body>
<h1>Upload CSV</h1>
<form method="post" enctype="multipart/form-data">
<input type="file" name="csv_file" accept=".csv"><br>
Months threshold: <input type="number" name="months" value="2" min="1"><br>
<input type="submit" value="Analyze">
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
        fileitem = form["csv_file"] if "csv_file" in form else None
        months = int(form.getfirst("months", "2"))
        output = "No file uploaded"
        if fileitem is not None and fileitem.file:
            data = fileitem.file.read().decode()
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tf:
                tf.write(data)
                path = tf.name
            results = find_recurring_transactions(path, months_threshold=months)
            if results:
                output = "\n".join(f"{d}: ${a:.2f}" for d, a in results)
            else:
                output = "No recurring transactions found."
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(FORM.format(output=output).encode())

def run(server_class=http.server.HTTPServer, handler_class=UploadHandler, port=8000):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Serving on http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
