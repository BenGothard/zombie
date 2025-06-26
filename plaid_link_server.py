import os
from flask import Flask, request, jsonify, render_template_string
from plaid import Client


app = Flask(__name__)


def _create_client() -> Client:
    return Client(
        client_id=os.environ["PLAID_CLIENT_ID"],
        secret=os.environ["PLAID_SECRET"],
        environment=os.getenv("PLAID_ENV", "sandbox"),
    )


HTML_TEMPLATE = """<!doctype html>
<html>
<head>
  <title>Connect Bank Account</title>
  <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
</head>
<body>
<button id="link-button">Connect Bank</button>
<script>
fetch('/create-link-token').then(r => r.json()).then(data => {
  var handler = Plaid.create({
    token: data.link_token,
    onSuccess: function(public_token) {
      fetch('/exchange', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({public_token: public_token})})
        .then(() => alert('Access token saved to plaid_access_token.txt')); 
    }
  });
  document.getElementById('link-button').onclick = function() { handler.open(); };
});
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/create-link-token")
def create_link_token():
    client = _create_client()
    response = client.LinkToken.create(
        {
            "user": {"client_user_id": "user"},
            "client_name": "Zombie Transactions",
            "products": ["transactions"],
            "country_codes": ["US"],
            "language": "en",
        }
    )
    return jsonify({"link_token": response["link_token"]})


@app.route("/exchange", methods=["POST"])
def exchange():
    public_token = request.json.get("public_token")
    client = _create_client()
    exchange = client.Item.public_token.exchange(public_token)
    access_token = exchange["access_token"]
    with open("plaid_access_token.txt", "w") as f:
        f.write(access_token)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5000)
