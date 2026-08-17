# plot_excel.py
# Usage: python plot_excel.py VN_CFO_LNST.xlsx
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid")

def find_time_cols(cols):
    keys = ["date","year","period","quarter","time","ngay","thang","nam"]
    return [c for c in cols if any(k in c.lower() for k in keys)]

def find_symbol_col(cols):
    keys = ["symbol","ticker","ma","code","company","name","ten"]
    for c in cols:
        if any(k in c.lower() for k in keys):
            return c
    return None

def numeric_columns(df):
    nums = []
    for c in df.columns:
        coerced = pd.to_numeric(df[c], errors="coerce")
        if coerced.notna().sum() >= max(1, len(df)//4):
            nums.append(c)
    return nums

def parse_time(df, col):
    res = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True)
    if res.notna().sum() == 0:
        coerced = pd.to_numeric(df[col], errors="coerce").dropna().astype(int)
        if len(coerced) > 0:
            return pd.to_datetime(coerced.astype(str) + "-01-01")
    return res

def plot_timeseries(df, time_col, symbol_col, value_cols, outdir, sheet_name):
    df2 = df.copy()
    df2[time_col] = parse_time(df2, time_col)
    if df2[time_col].isna().all():
        print(f"  Couldn't parse dates in {time_col} for sheet {sheet_name}")
        return
    df2 = df2.dropna(subset=[time_col]).sort_values(time_col)
    groups = [None]
    if symbol_col and symbol_col in df2.columns:
        groups = df2[symbol_col].dropna().unique().tolist()
    for g in groups:
        sub = df2 if g is None else df2[df2[symbol_col] == g]
        label = "all" if g is None else str(g)
        for col in value_cols:
            if col not in sub.columns: continue
            series = pd.to_numeric(sub[col], errors="coerce")
            if series.dropna().empty: continue
            plt.figure(figsize=(10,4))
            plt.plot(sub[time_col], series, marker="o")
            plt.title(f"{col} over time ({label}) - {sheet_name}")
            plt.xlabel(time_col)
            plt.ylabel(col)
            plt.tight_layout()
            out = outdir / f"{sheet_name}__{label}__{col}.png"
            plt.savefig(out)
            plt.close()
            print("  Saved:", out)

def scatter_and_hist(df, cols, outdir, sheet_name, symbol_col=None):
    if len(cols) >= 2:
        x, y = cols[0], cols[1]
        try:
            df2 = df[[x,y]].dropna()
            df2[x] = pd.to_numeric(df2[x], errors="coerce")
            df2[y] = pd.to_numeric(df2[y], errors="coerce")
            df2 = df2.dropna()
            if not df2.empty:
                plt.figure(figsize=(6,6))
                sns.scatterplot(x=x, y=y, data=df2)
                sns.regplot(x=x, y=y, data=df2, scatter=False, color='r', ci=None)
                plt.title(f"{y} vs {x} - {sheet_name}")
                plt.tight_layout()
                out = outdir / f"{sheet_name}__scatter__{x}_vs_{y}.png"
                plt.savefig(out); plt.close(); print("  Saved:", out)
        except Exception as e:
            print("  scatter error:", e)
    for c in cols:
        try:
            ser = pd.to_numeric(df[c], errors="coerce").dropna()
            if ser.empty: continue
            plt.figure(figsize=(8,4))
            sns.histplot(ser, kde=True)
            plt.title(f"Distribution: {c} - {sheet_name}")
            out = outdir / f"{sheet_name}__hist__{c}.png"
            plt.tight_layout(); plt.savefig(out); plt.close(); print("  Saved:", out)
        except Exception as e:
            print("  hist error for", c, e)

def main(path):
    p = Path(path)
    outdir = Path("output")
    outdir.mkdir(exist_ok=True)
    xls = pd.ExcelFile(p, engine="openpyxl")
    for sheet in xls.sheet_names:
        print("\nProcessing sheet:", sheet)
        df = pd.read_excel(xls, sheet_name=sheet, engine="openpyxl")
        if df.empty:
            print("  empty, skip"); continue
        cols = df.columns.tolist()
        print("  columns:", cols)
        time_candidates = find_time_cols(cols)
        symbol_col = find_symbol_col(cols)
        nums = numeric_columns(df)
        print("  numeric-like columns:", nums)
        time_col = None
        if time_candidates:
            for c in time_candidates:
                if parse_time(df, c).notna().sum() > 0:
                    time_col = c; break
            if time_col is None:
                time_col = time_candidates[0]
        else:
            for c in cols:
                if parse_time(df, c).notna().sum() > 0:
                    time_col = c; break
        preferred = [c for c in nums if any(k in c.lower() for k in ["cfo","cash","operat","lnst","lnt","profit","net","eps","roe"])]
        if not preferred:
            preferred = nums[:3]
        print("  chosen time_col:", time_col, "symbol_col:", symbol_col, "value_cols:", preferred)
        if time_col:
            plot_timeseries(df, time_col, symbol_col, preferred, outdir, sheet)
        else:
            print("  no time col — will create hist/box/scatter from latest values")
            scatter_and_hist(df, preferred, outdir, sheet, symbol_col)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plot_excel.py VN_CFO_LNST.xlsx")
        raise SystemExit(1)
    main(sys.argv[1])
