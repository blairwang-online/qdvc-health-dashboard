#!/usr/bin/env python3
"""
sleep_dashboard.py — entry point for the QDVC sleep-health dashboard.

Reads a sleep-tracking CSV and generates a self-contained HTML dashboard.

CSV format (header may contain spaces after commas):
    sleep_date, begin_hhmm, end_hhmm
    2026-07-02,0115,0915

Each row's `sleep_date` is the morning you woke. `begin_hhmm` is the clock time
you fell asleep, `end_hhmm` the clock time you woke. If begin > end, the sleep
crossed midnight and started the previous calendar day. Missing nights (equipment
failure) simply have no row and are handled gracefully.

Usage:
    python sleep_dashboard.py [path/to/sleep.csv] [-o dashboard.html]
Defaults: input "sleep.csv" in the current directory, output "sleep_dashboard.html".

The implementation lives in the qdvchealthdash_lib package; this file is only
the command-line entry point.
"""

from __future__ import annotations

import argparse
import sys

from qdvchealthdash_lib import load_nights, analyse, render_html


def main() -> None:
    p = argparse.ArgumentParser(description="Generate a sleep-health dashboard.")
    p.add_argument("csv", nargs="?", default="sleep.csv", help="input CSV (default: sleep.csv)")
    p.add_argument("-o", "--out", default="sleep_dashboard.html", help="output HTML file")
    args = p.parse_args()

    try:
        nights, warnings = load_nights(args.csv)
    except FileNotFoundError:
        sys.exit(f"File not found: {args.csv}")

    analysis = analyse(nights)
    doc = render_html(analysis, warnings, args.csv)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(doc)

    print(f"Read {analysis['recorded']} nights "
          f"({analysis['date_from']} → {analysis['date_to']}, "
          f"{analysis['coverage']}% coverage).")
    print(f"Sleep-health score: {analysis['score']}/100.")
    print(f"Dashboard written to {args.out}")


if __name__ == "__main__":
    main()
