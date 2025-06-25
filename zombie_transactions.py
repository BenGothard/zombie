import csv
from collections import defaultdict
from datetime import datetime
from typing import List, Tuple, Dict, Iterable
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
    """Return a list of CSV dict rows from supported files."""
    lower = file_path.lower()
    if lower.endswith(".pdf"):
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
    elif lower.endswith(('.png', '.jpg', '.jpeg')):
        try:
            from PIL import Image
            import pytesseract
        except ImportError as e:
            raise RuntimeError(
                "Image support requires Pillow and pytesseract packages"
            ) from e

        text = pytesseract.image_to_string(Image.open(file_path))
        csv_io = io.StringIO(text)
        return list(csv.DictReader(csv_io))
    else:
        with open(file_path, newline="") as f:
            return list(csv.DictReader(f))


def find_recurring_transactions_from_rows(
    rows: Iterable[dict],
    months_threshold: int = 2,
    fuzzy: bool = False,
    ratio_threshold: float = 0.8,
) -> List[Tuple[str, float]]:
    """Return recurring (description, amount) pairs from an iterable of rows.

    When ``fuzzy`` is ``True`` descriptions that are very similar will be grouped
    together using :func:`difflib.SequenceMatcher`. The ``ratio_threshold``
    controls how close descriptions must be to be considered equal.
    """

    if fuzzy:
        from difflib import SequenceMatcher

    seen: Dict[Tuple[str, float], set] = defaultdict(set)

    def _match_key(desc: str, amount: float) -> Tuple[str, float] | None:
        if not fuzzy:
            return (desc, amount)
        lower_desc = desc.lower()
        for (known_desc, amt) in seen.keys():
            if amt != amount:
                continue
            ratio = SequenceMatcher(None, lower_desc, known_desc.lower()).ratio()
            if ratio >= ratio_threshold:
                return (known_desc, amt)
        return (desc, amount)

    for row in rows:
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

        key = _match_key(description, amount)
        seen[key].add(month)

    return [
        (desc, amt) for (desc, amt), months in seen.items() if len(months) >= months_threshold
    ]


def find_recurring_transactions(
    file_path: str,
    months_threshold: int = 2,
    fuzzy: bool = False,
    ratio_threshold: float = 0.8,
) -> List[Tuple[str, float]]:
    """Return a list of (description, amount) that appear in multiple months."""
    rows = _load_rows(file_path)
    return find_recurring_transactions_from_rows(
        rows,
        months_threshold=months_threshold,
        fuzzy=fuzzy,
        ratio_threshold=ratio_threshold,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Find recurring transactions across multiple months"
    )
    parser.add_argument(
        "csv_file", help="Transactions file (CSV, text, PDF or image)"
    )
    parser.add_argument(
        "-n",
        "--months",
        type=int,
        default=2,
        help="Minimum number of months for a transaction to be considered recurring",
    )
    parser.add_argument(
        "--fuzzy",
        action="store_true",
        help="Enable fuzzy matching of descriptions using simple AI heuristics",
    )
    parser.add_argument(
        "--ratio-threshold",
        type=float,
        default=0.8,
        help="Similarity required for descriptions to be grouped when --fuzzy is used",
    )
    args = parser.parse_args()
    for desc, amt in find_recurring_transactions(
        args.csv_file,
        args.months,
        fuzzy=args.fuzzy,
        ratio_threshold=args.ratio_threshold,
    ):
        print(f"{desc}: ${amt:.2f}")

