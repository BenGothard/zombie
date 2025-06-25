import csv
from collections import defaultdict
from datetime import datetime
from typing import List, Tuple, Dict
import io


def _get_month(date_str: str) -> str | None:
    """Return YYYY-MM for a date string or ``None`` if parsing fails."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m")
        except ValueError:
            continue
    return None


def _load_rows(file_path: str):
    """Return a list of CSV dict rows from a CSV or PDF file."""
    if file_path.lower().endswith(".pdf"):
        try:
            from PyPDF2 import PdfReader
        except ImportError as e:
            raise RuntimeError("PDF support requires PyPDF2 package") from e

        text = ""
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        csv_io = io.StringIO(text)
        return list(csv.DictReader(csv_io))
    else:
        with open(file_path, newline="") as f:
            return list(csv.DictReader(f))


def find_recurring_transactions(
    file_path: str, months_threshold: int = 2
) -> List[Tuple[str, float]]:
    """Return a list of (description, amount) that appear in multiple months."""
    seen: Dict[Tuple[str, float], set] = defaultdict(set)
    for row in _load_rows(file_path):
        description = (row.get("Description") or row.get("Payee") or "").strip()
        amount_str = row.get("Amount")
        date_str = row.get("Date") or row.get("Transaction Date") or ""

        try:
            amount = float(amount_str)
        except (TypeError, ValueError):
            continue

        month = _get_month(date_str)
        if not description or month is None:
            continue

        seen[(description, amount)].add(month)
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

