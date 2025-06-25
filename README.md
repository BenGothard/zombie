# zombie

This repository contains a small Python utility for identifying recurring "zombie" credit card transactions. Forgotten cards often continue paying for services that are no longer used, wasting significant amounts of money.

## Usage
Prepare a CSV file with at least `Date`, `Description` and `Amount` columns. Run the script specifying the CSV file:

```bash
python zombie_transactions.py transactions.csv -n 3
```

PDF statements can also be analyzed if the optional `PyPDF2` dependency is installed.  
Text files (`.txt`) and image files containing statement screenshots (`.png`, `.jpg`) are supported when `pytesseract` and `Pillow` are available:

```bash
python zombie_transactions.py statement.pdf -n 3
python zombie_transactions.py statement.png -n 3
```

The `-n`/`--months` option controls how many distinct months a charge must appear in to be reported.

Rows with missing or malformed data are ignored so you can analyze statements that contain occasional inconsistencies without errors.

## Web interface
A basic web interface is available under `docs/`. GitHub Pages can serve this directory so the analysis can be run directly in the browser:

1. Commit the contents of the `docs/` folder.
2. In your repository settings on GitHub, enable **GitHub Pages** and choose the **docs/** folder as the source.
3. Visit the provided URL to upload a CSV file and see recurring charges without installing anything locally.

The web interface is now completely self contained. You can open
`docs/index.html` directly in your browser without an internet connection and
analyze CSV files or simple PDF statements. PDF parsing is best effort and
may fail on heavily compressed documents.

The page now supports dark mode automatically and features an improved layout for an epic experience.

Your last analysis results are stored in your browser so you can reopen
`docs/index.html` later and review them even without an internet
connection.


## Local upload server
If you prefer a minimal server-based approach, run `upload_server.py`:

```bash
python upload_server.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser to upload a CSV, text, PDF or image file and view recurring transactions. PDF and image parsing require the optional `PyPDF2`, `pytesseract` and `Pillow` packages.
