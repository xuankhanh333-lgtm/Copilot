# Inspect Excel script
# Usage: python inspect_excel.py VN_CFO_LNST.xlsx
import sys
import pandas as pd
from pathlib import Path


def preview(path):
    xls = pd.ExcelFile(path, engine="openpyxl")
    print("Sheets:", xls.sheet_names)
    for name in xls.sheet_names:
        print("\n--- Sheet:", name, "---")
        df = pd.read_excel(xls, sheet_name=name, nrows=10, engine="openpyxl")
        print("Shape:", df.shape)
        print("Columns and dtypes:")
        print(df.dtypes)
        print("\nFirst rows:")
        print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_excel.py VN_CFO_LNST.xlsx")
        sys.exit(1)
    p = Path(sys.argv[1])
    if not p.exists():
        print("File not found:", p)
        sys.exit(1)
    preview(p)
