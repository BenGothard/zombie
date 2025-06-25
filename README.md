# zombie

This repository contains a small Python utility for identifying recurring "zombie" credit card transactions. Forgotten cards often continue paying for services that are no longer used, wasting significant amounts of money.

## Usage
Prepare a CSV file with at least `Date`, `Description` and `Amount` columns. Run the script specifying the CSV file:

```bash
python zombie_transactions.py transactions.csv -n 3
```

The `-n`/`--months` option controls how many distinct months a charge must appear in to be reported.

## Web interface
A basic web interface is available under `docs/`. GitHub Pages can serve this directory so the analysis can be run directly in the browser:

1. Commit the contents of the `docs/` folder.
2. In your repository settings on GitHub, enable **GitHub Pages** and choose the **docs/** folder as the source.
3. Visit the provided URL to upload a CSV file and see recurring charges without installing anything locally.

