#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import pandas as pd

EU_CODES = {
    "AT","BE","BG","HR","CY","CZ","DE","DK","EE","ES","FI","FR","GR","HU","IE","IT",
    "LT","LU","LV","MT","NL","PL","PT","RO","SE","SI","SK"
}

def map_region(loc: str) -> str:
    if not loc or str(loc).strip().upper() in {"", "NA", "N/A", "NONE"}:
        return "GLO"
    s = str(loc).strip().upper()
    if s in {"EU","RER"}:  # already generic EU
        return s
    if len(s) == 2 and s in EU_CODES:
        return "RER"
    # keep as-is for other regions (CH, CN, US, GLO, etc.) but Postman logic should still fallback to GLO if CF miss
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exch_csv", required=True, help="Path to *_exch.csv produced by the scraper")
    ap.add_argument("--out_csv", required=True, help="Path to write the prepared/aggregated exchanges")
    args = ap.parse_args()

    df = pd.read_csv(args.exch_csv)
    # normalize location
    df["location_norm"] = df["location"].astype(str).fillna("").map(map_region)
    # aggregate duplicates
    grp = df.groupby(["process_uuid","flow_uuid","location_norm"], as_index=False)["amount_per_FU"].sum()
    grp.rename(columns={"location_norm":"location"}, inplace=True)
    grp.to_csv(args.out_csv, index=False)
    print(f"Wrote {len(grp)} rows -> {args.out_csv}")

if __name__ == "__main__":
    main()
