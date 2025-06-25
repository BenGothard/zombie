# zombie

This repository contains a small Python utility for identifying recurring "zombie" credit card transactions. Forgotten cards often continue paying for services that are no longer used, wasting significant amounts of money.

## Usage
Prepare a CSV file with at least `Date`, `Description` and `Amount` columns. Run the script specifying the CSV file:

```bash
python zombie_transactions.py transactions.csv -n 3
```

The `-n`/`--months` option controls how many distinct months a charge must appear in to be reported.

