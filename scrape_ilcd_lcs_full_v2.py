#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Scrape ILCD XML processes into:
#  1) a processes CSV with required headers (user's schema)
#  2) an exchanges CSV with per-flow amounts needed for LCIA
#
# USAGE
# -----
# python3 scrape_ilcd_lcs_full_v2.py \
#   --root /path/to/PEF_AI/data/ilcd/processes \
#   --out  /path/to/PEF_AI/output/ilcd_scraped_processes_v2.csv \
#   --sample 50
#
# Outputs:
#   - <out> (processes)
#   - <out_basename>_exch.csv (exchanges)

import argparse
import csv
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

def has(s: str, pattern: str) -> bool:
    s = s or ""
    try:
        return bool(re.search(pattern, s, flags=re.IGNORECASE))
    except re.error:
        return False

def classify_lcs(path: Path, dataset_name: str, process_type_hint: str = "") -> Tuple[str, str]:
    p = str(path.as_posix()).lower()
    ds = (dataset_name or "").lower()
    pt = (process_type_hint or "").lower()
    if any([
        "/eol/" in p or "/end-of-life/" in p,
        has(ds, r"\beol\b|incinerat|landfill|recycl"),
        has(pt, r"eol|end[-_ ]?of[-_ ]?life|waste"),
    ]):
        return ("LCS3","eol")
    if any([
        "/use/" in p or "/laundry/" in p,
        has(ds, r"washing|laundry|tumble dry|ironing|line dry|air dry"),
        has(pt, r"use|washing|laundry|dry|iron"),
    ]):
        return ("LCS3","use")
    if any([
        "/transport/" in p or "/distribution/" in p or "/logistics/" in p,
        has(ds, r"\btransport\b|distribution|truck|lorry|train|rail|barge|ship|sea|ocean|air( |-)freight|road"),
    ]):
        return ("LCS3","distribution")
    if any([
        "/packag" in p,
        has(ds, r"pack|carton|cardboard|corrugat|polybag|hangtag|film|box|label"),
    ]):
        return ("LCS2","packaging")
    if any([
        "/textile/" in p or "/process/" in p or "/manufactur" in p,
        has(ds, r"spinning|textile (finishing|production)|yarn production|fabric production|dye|weav|knit|sew|sewing|stitch"),
        has(pt, r"manufactur|textile|spinning|dye|weav|knit|sew"),
    ]):
        return ("LCS2","manufacturing")
    return ("LCS1","materials")

def get_text_first(root: ET.Element, xpaths: List[str]) -> str:
    for xp in xpaths:
        el = root.find(xp)
        if el is not None:
            if el.text and el.text.strip():
                return el.text.strip()
            txt = "".join(el.itertext()).strip()
            if txt:
                return txt
    return ""

def get_attr_any_ns(el: Optional[ET.Element], suffix: str) -> Optional[str]:
    if el is None:
        return None
    for k, v in el.attrib.items():
        if k.lower().endswith(suffix.lower()):
            return v
    return None

def extract_reference_flow_uuid(root: ET.Element, exchanges: List[ET.Element]) -> str:
    # 1) direct attribute on <referenceToReferenceFlow ... refObjectId="...">
    ref_el = root.find(".//{*}referenceToReferenceFlow")
    rid = get_attr_any_ns(ref_el, "refObjectId")
    if rid:
        return rid.strip()

    # 2) match by dataSetInternalID -> exchange -> referenceToFlowDataSet/@refObjectId
    ref_internal_id = get_text_first(root, [
        ".//{*}modellingAndValidation/{*}LCIMethodAndAllocation/{*}referenceToReferenceFlow/{*}dataSetInternalID",
        ".//{*}LCIMethodAndAllocation/{*}referenceToReferenceFlow/{*}dataSetInternalID",
        ".//{*}referenceToReferenceFlow/{*}dataSetInternalID",
    ])
    if not ref_internal_id:
        return ""

    for ex in exchanges:
        ex_int_id = get_text_first(ex, [".//{*}dataSetInternalID"]).strip()
        if ex_int_id and ex_int_id == ref_internal_id.strip():
            ref_flow_el = ex.find(".//{*}referenceToFlowDataSet")
            rid2 = get_attr_any_ns(ref_flow_el, "refObjectId")
            if rid2:
                return rid2.strip()
    return ""

def extract_flow_rows(root: ET.Element, process_uuid: str, xml_path: Path, process_geo: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for ex in root.findall(".//{*}exchange"):
        ref_flow = ex.find(".//{*}referenceToFlowDataSet")
        rid = get_attr_any_ns(ref_flow, "refObjectId")
        if not rid:
            continue
        amt_txt = get_text_first(ex, [".//{*}meanAmount", ".//{*}resultingAmount", ".//{*}amount"]).replace(",", ".").strip()
        try:
            amount = float(amt_txt) if amt_txt != "" else 0.0
        except ValueError:
            amount = 0.0
        loc = get_text_first(ex, [".//{*}location"]) or process_geo or ""
        rows.append({
            "process_uuid": process_uuid,
            "xml_file": str(xml_path),
            "flow_uuid": rid.strip(),
            "amount_per_FU": amount,
            "location": loc
        })
    return rows

def parse_name(root: ET.Element) -> str:
    return get_text_first(root, [
        ".//{*}dataSetInformation/{*}name/{*}baseName",
        ".//{*}name/{*}baseName",
        ".//{*}name/{*}shortName",
        ".//{*}name",
        ".//{*}shortName",
    ])

def parse_category(root: ET.Element) -> str:
    return get_text_first(root, [
        ".//{*}classification/{*}classificationItem/{*}className",
        ".//{*}classification/{*}classificationItem/{*}name",
    ])

def parse_uuid(root: ET.Element) -> str:
    return get_text_first(root, [
        ".//{*}dataSetInformation/{*}UUID",
        ".//{*}UUID",
    ])

def parse_reference_unit(root: ET.Element) -> str:
    return get_text_first(root, [
        ".//{*}quantitativeReference/{*}referenceToReferenceFlowProperty/{*}unitName",
        ".//{*}referenceToReferenceFlowProperty/{*}unitName",
    ])

def parse_geography(root: ET.Element) -> str:
    return get_text_first(root, [
        ".//{*}geography/{*}shortname",
        ".//{*}geography/{*}shortName",
    ])

def guess_process_type(name: str) -> str:
    if has(name, r"wash|laundry|iron|dry"):
        return "use"
    if has(name, r"incinerat|landfill|recycl|waste"):
        return "eol"
    if has(name, r"pack|carton|cardboard|corrugat|polybag|hangtag|film|box|label"):
        return "packaging"
    if has(name, r"spin|weav|knit|sew|stitch|dye|finish"):
        return "manufacturing"
    return "materials"

def parse_ilcd_process(xml_path: Path) -> Optional[Tuple[Dict[str, Any], List[Dict[str, Any]]]]:
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception:
        return None

    uuid = parse_uuid(root)
    name = parse_name(root)
    category = parse_category(root)
    reference_unit = parse_reference_unit(root)
    geography = parse_geography(root)

    exchanges_el = root.findall(".//{*}exchange")
    reference_flow_uuid = extract_reference_flow_uuid(root, exchanges_el) if exchanges_el else ""

    # exchanges rows (with amounts)
    exch_rows = extract_flow_rows(root, uuid, xml_path, geography)
    flow_uuids = [r["flow_uuid"] for r in exch_rows]
    flow_count = len(flow_uuids)

    pt_hint = guess_process_type(name)
    lcs_stage, lcs_block = classify_lcs(xml_path, name, pt_hint)

    row: Dict[str, Any] = {
        "uuid": uuid,
        "name": name,
        "category": category,
        "reference_unit": reference_unit,
        "geography": geography,
        "material_code": xml_path.stem,
        "material_code_confidence": "",
        "kg_per_m2": "",
        "temp_c": "",
        "transport_km": "",
        "flow_uuids": ";".join(flow_uuids),
        "flow_count": flow_count,
        "reference_flow_uuid": reference_flow_uuid,
        "keywords": "",
        "text_excerpt": "",
        "xml_file": str(xml_path),
        "lcs_stage": lcs_stage,
        "lcs_block": lcs_block,
        "exchanges_count": flow_count,
    }
    return row, exch_rows

def collect_xml_files(root: Path) -> List[Path]:
    return sorted([p for p in root.rglob("*.xml") if p.is_file()])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Root directory with ILCD process XML files")
    ap.add_argument("--out",  required=True, help="Output CSV file (processes)")
    ap.add_argument("--sample", type=int, default=0, help="If >0, randomly sample N XML files")
    args = ap.parse_args()

    root = Path(args.root)
    out  = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    exch_out = out.with_name(out.stem.replace(".csv","") + "_exch.csv") if out.suffix == ".csv" else out.with_suffix(out.suffix + "_exch.csv")
    # If simpler: just use suffix _exch.csv next to out
    exch_out = out.with_name(out.stem + "_exch.csv")

    xml_files = collect_xml_files(root)
    if not xml_files:
        print("No XML files found under:", root)
        return

    if args.sample and 0 < args.sample < len(xml_files):
        xml_files = random.sample(xml_files, args.sample)
        print(f"Sampling {len(xml_files)} XML files for quick test...")
    else:
        print(f"Processing all XML files: {len(xml_files)}")

    proc_rows: List[Dict[str, Any]] = []
    exch_rows_all: List[Dict[str, Any]] = []

    for i, xp in enumerate(xml_files, 1):
        parsed = parse_ilcd_process(xp)
        if parsed:
            row, exrows = parsed
            proc_rows.append(row)
            exch_rows_all.extend(exrows)
        if i % 50 == 0:
            print(f"Parsed {i}/{len(xml_files)} ...")

    proc_fields = [
        "uuid","name","category","reference_unit","geography",
        "material_code","material_code_confidence","kg_per_m2","temp_c","transport_km",
        "flow_uuids","flow_count","reference_flow_uuid","keywords","text_excerpt",
        "xml_file","lcs_stage","lcs_block","exchanges_count"
    ]
    exch_fields = ["process_uuid","xml_file","flow_uuid","amount_per_FU","location"]

    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=proc_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(proc_rows)

    with exch_out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=exch_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(exch_rows_all)

    print(f"Done. Wrote {len(proc_rows)} process rows -> {out}")
    print(f"Done. Wrote {len(exch_rows_all)} exchange rows -> {exch_out}")

if __name__ == "__main__":
    main()
