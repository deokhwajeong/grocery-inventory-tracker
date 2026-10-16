#!/usr/bin/env python3
"""
Measure receipt OCR and parsing accuracy against the synthetic dataset.

Two modes:

- text: feed the exact printed receipt text to the parser. This isolates the
  parser (items, prices, quantities, dates, receipt type) from OCR errors.
- ocr:  run the full pipeline on the rendered images (OpenCV preprocessing,
  Tesseract, parser). Needs Tesseract and the images from
  scripts/receipt_dataset.py. Also reports processing time per receipt.

Metrics:

- item recall / precision: ground-truth items matched by a parsed item, and
  parsed items that match a real item (the rest are header, total, savings or
  quantity lines that leaked through). Matching compares the parsed name to
  the printed and the plain product name and needs a similarity of 0.75.
- name accuracy: matched items whose name equals the plain product name after
  normalization (case, spacing and a trailing plural "s" ignored).
- quantity / price accuracy: matched items with the right count and the right
  line total (to the cent).
- date accuracy: receipts whose purchase date was read correctly.
- type accuracy: receipts whose layout type was detected correctly.

Usage:
    python scripts/ocr_accuracy.py --mode text
    python scripts/ocr_accuracy.py --mode ocr --limit 20 --json results.json
"""
import argparse
import json
import os
import statistics
import sys
import time
from difflib import SequenceMatcher

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import logging  # noqa: E402

logging.disable(logging.WARNING)

import ocr_processor  # noqa: E402
from inventory import normalize_name  # noqa: E402
from receipt_dataset import DEFAULT_OUT, generate  # noqa: E402

MATCH_THRESHOLD = 0.75


def similarity(a, b):
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


def match_items(truth, parsed):
    """Greedy one-to-one matching, best pairs first. Returns [(t_index, p_index)]."""
    pairs = []
    for ti, t in enumerate(truth):
        for pi, p in enumerate(parsed):
            score = max(similarity(p["name"], t["name"]), similarity(p["name"], t["printed"]))
            if score >= MATCH_THRESHOLD:
                pairs.append((score, ti, pi))
    pairs.sort(reverse=True)
    used_t, used_p, matches = set(), set(), []
    for _, ti, pi in pairs:
        if ti in used_t or pi in used_p:
            continue
        used_t.add(ti)
        used_p.add(pi)
        matches.append((ti, pi))
    return matches


def to_float(value):
    try:
        return float(str(value).replace(",", "").replace("$", ""))
    except (TypeError, ValueError):
        return None


def score_receipt(receipt, result):
    truth, parsed = receipt["items"], result["items"]
    matches = match_items(truth, parsed)
    names = qty = price = 0
    for ti, pi in matches:
        t, p = truth[ti], parsed[pi]
        names += normalize_name(p["name"]) == normalize_name(t["name"])
        qty += int(p.get("quantity") or 1) == t["quantity"]
        got = to_float(p.get("price"))
        price += got is not None and abs(got - t["price"]) < 0.005
    return {
        "truth_items": len(truth), "parsed_items": len(parsed), "matched": len(matches),
        "names": names, "quantity": qty, "price": price,
        "date": result.get("date") == receipt["date"],
        "type": result.get("receipt_type") == receipt["type"],
    }


def run_parser(text):
    """Parse receipt text with the app's pipeline."""
    return ocr_processor.parse_receipt(text)


def run_ocr(image_path):
    return ocr_processor.analyze_receipt_image(image_path, "eng")


def pct(n, d):
    return round(100.0 * n / d, 1) if d else 0.0


def summarize(scores, timings=None):
    tot = {k: sum(s[k] for s in scores) for k in ("truth_items", "parsed_items", "matched", "names", "quantity", "price", "date", "type")}
    summary = {
        "receipts": len(scores),
        "items": tot["truth_items"],
        "item_recall": pct(tot["matched"], tot["truth_items"]),
        "item_precision": pct(tot["matched"], tot["parsed_items"]),
        "name_accuracy": pct(tot["names"], tot["matched"]),
        "quantity_accuracy": pct(tot["quantity"], tot["matched"]),
        "price_accuracy": pct(tot["price"], tot["matched"]),
        "date_accuracy": pct(tot["date"], len(scores)),
        "type_accuracy": pct(tot["type"], len(scores)),
    }
    if timings:
        ordered = sorted(timings)
        p95_index = max(0, int(round(0.95 * len(ordered))) - 1)
        summary["seconds_mean"] = round(statistics.mean(ordered), 2)
        summary["seconds_median"] = round(statistics.median(ordered), 2)
        summary["seconds_p95"] = round(ordered[p95_index], 2)
        summary["seconds_max"] = round(ordered[-1], 2)
    return summary


def per_type(receipts, scores):
    out = {}
    for kind in sorted({r["type"] for r in receipts}):
        subset = [s for r, s in zip(receipts, scores) if r["type"] == kind]
        out[kind] = summarize(subset)
    return out


def evaluate(mode="text", limit=None, dataset_dir=DEFAULT_OUT, receipts=None, verbose=False):
    if receipts is None:
        if mode == "ocr":
            with open(os.path.join(dataset_dir, "ground_truth.json"), encoding="utf-8") as fh:
                receipts = json.load(fh)["receipts"]
        else:
            receipts = generate()
    receipts = receipts[:limit] if limit else receipts
    scores, timings = [], []
    for r in receipts:
        if mode == "ocr":
            start = time.perf_counter()
            result = run_ocr(os.path.join(dataset_dir, r["image"]))
            timings.append(time.perf_counter() - start)
        else:
            result = run_parser(r["text"])
        s = score_receipt(r, result)
        scores.append(s)
        if verbose:
            print(f"{r['id']} {r['type']:<12} items {s['matched']}/{s['truth_items']} (+{s['parsed_items'] - s['matched']} extra) "
                  f"price {s['price']} qty {s['quantity']} name {s['names']} date {'ok' if s['date'] else result.get('date')}"
                  + (f" {timings[-1]:.2f}s" if timings else ""))
    return {"mode": mode, "overall": summarize(scores, timings), "by_type": per_type(receipts, scores)}


def markdown(report):
    o = report["overall"]
    rows = [("Item recall", o["item_recall"]), ("Item precision", o["item_precision"]),
            ("Name accuracy (matched items)", o["name_accuracy"]), ("Quantity accuracy (matched items)", o["quantity_accuracy"]),
            ("Price accuracy (matched items)", o["price_accuracy"]), ("Date accuracy", o["date_accuracy"]),
            ("Receipt type accuracy", o["type_accuracy"])]
    lines = [f"Mode: {report['mode']}, {o['receipts']} receipts, {o['items']} items", "",
             "| Metric | Value |", "|---|---|"]
    lines += [f"| {k} | {v}% |" for k, v in rows]
    if "seconds_mean" in o:
        lines += [f"| Seconds per receipt (mean / median / p95 / max) | "
                  f"{o['seconds_mean']} / {o['seconds_median']} / {o['seconds_p95']} / {o['seconds_max']} |"]
    lines += ["", "| Type | Recall | Precision | Price | Qty | Date |", "|---|---|---|---|---|---|"]
    for kind, s in report["by_type"].items():
        lines.append(f"| {kind} | {s['item_recall']}% | {s['item_precision']}% | {s['price_accuracy']}% | "
                     f"{s['quantity_accuracy']}% | {s['date_accuracy']}% |")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["text", "ocr"], default="text")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dataset", default=DEFAULT_OUT, help="directory written by receipt_dataset.py (ocr mode)")
    parser.add_argument("--json", help="also write the report as JSON to this path")
    parser.add_argument("-v", "--verbose", action="store_true", help="print one line per receipt")
    args = parser.parse_args()
    if args.mode == "ocr" and not os.path.exists(os.path.join(args.dataset, "ground_truth.json")):
        sys.exit("No dataset found. Run: python scripts/receipt_dataset.py")
    report = evaluate(args.mode, args.limit, args.dataset, verbose=args.verbose)
    print(markdown(report))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1)
