import csv
from collections import defaultdict
from datetime import datetime
from typing import List, Tuple, Dict, Iterable
import io
import math

_SPACY_NLP = None


def _load_spacy():
    """Return a loaded spaCy model or ``None`` if unavailable."""
    global _SPACY_NLP
    if _SPACY_NLP is not None:
        return _SPACY_NLP or None
    try:
        import spacy  # type: ignore
        try:
            _SPACY_NLP = spacy.load("en_core_web_md")
        except Exception:
            _SPACY_NLP = spacy.load("en_core_web_sm")
    except Exception:
        _SPACY_NLP = False
    return _SPACY_NLP or None


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
        text = ""
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except ImportError:
            reader = None
        except Exception:
            # PyPDF2 is present but failed to parse; fall back to other methods
            pass

        if not text.strip():
            try:
                import pdfplumber

                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text() or ""
                        if page_text:
                            text += page_text + "\n"
            except Exception:
                text = ""

        if not text.strip():
            try:
                from pdfminer.high_level import extract_text

                text = extract_text(file_path) or ""
            except Exception:
                text = ""

        if not text.strip():
            try:
                from pdf2image import convert_from_path
                from PIL import Image
                import pytesseract

                images = convert_from_path(file_path)
                for img in images:
                    text += pytesseract.image_to_string(
                        img, config="--oem 3 --psm 6"
                    ) + "\n"
            except Exception:
                pass

        if not text.strip():
            raise RuntimeError("Unable to extract text from PDF")

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

        text = pytesseract.image_to_string(
            Image.open(file_path), config="--oem 3 --psm 6"
        )
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
    together using spaCy embeddings when available. If spaCy or its language
    model cannot be loaded, a fallback based on :func:`difflib.SequenceMatcher`
    is used. The ``ratio_threshold`` controls how close descriptions must be to
    be considered equal.
    """

    nlp = _load_spacy() if fuzzy else None
    if fuzzy and nlp is None:
        from difflib import SequenceMatcher

    seen: Dict[Tuple[str, float], set] = defaultdict(set)
    vectors: Dict[Tuple[str, float], list] = {}

    def _match_key(desc: str, amount: float) -> Tuple[str, float] | None:
        if not fuzzy:
            return (desc, amount)
        if nlp is not None:
            vec = nlp(desc).vector
            for (known_desc, amt), known_vec in vectors.items():
                if amt != amount:
                    continue
                dot = sum(a * b for a, b in zip(vec, known_vec))
                norm1 = math.sqrt(sum(a * a for a in vec))
                norm2 = math.sqrt(sum(a * a for a in known_vec))
                sim = dot / norm1 / norm2 if norm1 and norm2 else 0.0
                if sim >= ratio_threshold:
                    return (known_desc, amt)
            vectors[(desc, amount)] = vec
            return (desc, amount)
        else:
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

