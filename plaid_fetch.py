import os
import csv
from datetime import date, timedelta
from typing import Iterable, List, Dict, Optional
try:
    from plaid import Client
except Exception:  # pragma: no cover - optional dependency
    Client = None  # type: ignore


def create_client() -> Client:
    if Client is None:
        raise ImportError("plaid package is required for Plaid integration")
    return Client(
        client_id=os.environ["PLAID_CLIENT_ID"],
        secret=os.environ["PLAID_SECRET"],
        environment=os.getenv("PLAID_ENV", "sandbox"),
    )


def fetch_transactions(
    access_token: str,
    start_date: str,
    end_date: str,
    client: Optional[Client] = None,
) -> List[Dict]:
    client = client or create_client()
    if client is None:
        raise ImportError("plaid package is required for Plaid integration")
    resp = client.Transactions.get(access_token, start_date=start_date, end_date=end_date)
    return resp.get("transactions", [])


def save_csv(transactions: Iterable[Dict], path: str) -> None:
    rows = [
        [t["date"], t["name"], t["amount"]]
        for t in transactions
    ]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Description", "Amount"])
        writer.writerows(rows)


def main() -> None:
    import argparse

    default_start = (date.today() - timedelta(days=90)).isoformat()
    parser = argparse.ArgumentParser(
        description="Fetch transactions from Plaid and analyze recurring charges"
    )
    parser.add_argument("access_token", help="Plaid access token or path to token file")
    parser.add_argument("--start", default=default_start, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default=date.today().isoformat(), help="End date YYYY-MM-DD")
    parser.add_argument("--csv", help="Optional CSV output file")
    parser.add_argument("--analyze", action="store_true", help="Analyze recurring transactions")
    args = parser.parse_args()

    token = args.access_token
    if os.path.isfile(token):
        with open(token) as f:
            token = f.read().strip()

    transactions = fetch_transactions(token, args.start, args.end)
    if args.csv:
        save_csv(transactions, args.csv)
    if args.analyze:
        rows = [
            {"Date": t["date"], "Description": t["name"], "Amount": t["amount"]}
            for t in transactions
        ]
        from zombie_transactions import find_recurring_transactions_from_rows, guess_threshold

        threshold = guess_threshold(rows)
        results = find_recurring_transactions_from_rows(rows, months_threshold=threshold, fuzzy=True)
        if results:
            for desc, amt in results:
                print(f"{desc}: ${amt:.2f}")
        else:
            print("No recurring transactions found.")
    else:
        print(f"Fetched {len(transactions)} transactions")


if __name__ == "__main__":
    main()
