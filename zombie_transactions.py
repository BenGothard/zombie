import csv
from collections import defaultdict
from datetime import datetime
from typing import List, Tuple, Dict


def _get_month(date_str: str) -> str:
    """Return YYYY-MM for a date string."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m")
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {date_str}")


def find_recurring_transactions(
    file_path: str, months_threshold: int = 2
) -> List[Tuple[str, float]]:
    """Return a list of (description, amount) that appear in multiple months."""
    seen: Dict[Tuple[str, float], set] = defaultdict(set)
    with open(file_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            description = row.get("Description") or row.get("Payee") or ""
            amount = float(row.get("Amount"))
            date_str = row.get("Date") or row.get("Transaction Date") or ""
            month = _get_month(date_str)
            seen[(description.strip(), amount)].add(month)
    return [
        (desc, amt) for (desc, amt), months in seen.items() if len(months) >= months_threshold
    ]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Find recurring transactions across multiple months"
    )
    parser.add_argument("csv_file", help="CSV file of credit card transactions")
    parser.add_argument(
        "-n",
        "--months",
        type=int,
        default=2,
        help="Minimum number of months for a transaction to be considered recurring",
    )
    args = parser.parse_args()
    for desc, amt in find_recurring_transactions(args.csv_file, args.months):
        print(f"{desc}: ${amt:.2f}")

