import unittest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from plaid_fetch import fetch_transactions


class StubTransactions:
    def get(self, token, start_date=None, end_date=None):
        return {
            "transactions": [
                {"date": "2024-01-01", "name": "Test", "amount": 1.23},
            ]
        }


class StubClient:
    Transactions = StubTransactions()


class PlaidFetchTest(unittest.TestCase):
    def test_fetch_transactions(self):
        txns = fetch_transactions("token", "2024-01-01", "2024-01-31", client=StubClient())
        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0]["name"], "Test")
        self.assertEqual(txns[0]["amount"], 1.23)


if __name__ == "__main__":
    unittest.main()
