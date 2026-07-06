"""Data model, CSV parsing, and low-level time helpers."""

from __future__ import annotations

import csv
import datetime as dt
from dataclasses import dataclass


@dataclass
class Night:
    wake_date: dt.date          # the morning you woke (= sleep_date column)
    start: dt.datetime          # full datetime sleep began
    end: dt.datetime            # full datetime sleep ended
    duration_h: float           # hours asleep


def _parse_hhmm(value: str) -> dt.time:
    """Parse a time-of-day cell into a ``dt.time``.

    Accepts the current format with a trailing ``h`` marker (e.g. ``'2203h'``,
    ``'0617h'``) — the ``h`` is a guard so spreadsheet software doesn't strip the
    leading zero or reinterpret the value as a number. Also accepts the older
    bare form (``'0130'``, ``'2330'``) and tolerates a colon (``'H:MM'`` /
    ``'HH:MM'``, optionally with the ``h`` suffix). Matching is case-insensitive.
    """
    v = value.strip().lower()
    if v.endswith("h"):
        v = v[:-1]
    v = v.replace(":", "")
    if not v.isdigit() or len(v) > 4:
        raise ValueError(f"bad time {value!r}")
    v = v.zfill(4)
    h, m = int(v[:2]), int(v[2:])
    if h > 23 or m > 59:
        raise ValueError(f"time out of range {value!r}")
    return dt.time(h, m)


def load_nights(path: str) -> tuple[list[Night], list[str]]:
    """Read the CSV, return (nights sorted by date, list of warning strings)."""
    nights: list[Night] = []
    warnings: list[str] = []

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if header is None:
            raise SystemExit(f"'{path}' is empty.")
        # Normalise header names (strip whitespace) to find columns robustly.
        cols = {name.strip().lower(): i for i, name in enumerate(header)}
        try:
            i_date = cols["sleep_date"]
            i_begin = cols["begin_hhmm"]
            i_end = cols["end_hhmm"]
        except KeyError:
            # Fall back to positional order if header names differ.
            i_date, i_begin, i_end = 0, 1, 2
            warnings.append("Header not recognised; assumed columns date,begin,end.")

        for lineno, row in enumerate(reader, start=2):
            if not row or all(not c.strip() for c in row):
                continue  # blank line
            try:
                wake_date = dt.date.fromisoformat(row[i_date].strip())
                t_begin = _parse_hhmm(row[i_begin])
                t_end = _parse_hhmm(row[i_end])
            except (ValueError, IndexError) as exc:
                warnings.append(f"Line {lineno}: skipped ({exc}).")
                continue

            end_dt = dt.datetime.combine(wake_date, t_end)
            # If begin time is later in the clock than end time, sleep began the
            # previous calendar day (crossed midnight).
            if t_begin > t_end:
                start_dt = dt.datetime.combine(
                    wake_date - dt.timedelta(days=1), t_begin
                )
            else:
                start_dt = dt.datetime.combine(wake_date, t_begin)

            duration_h = (end_dt - start_dt).total_seconds() / 3600.0
            if not (0 < duration_h <= 24):
                warnings.append(
                    f"Line {lineno}: implausible duration {duration_h:.1f}h, skipped."
                )
                continue

            nights.append(Night(wake_date, start_dt, end_dt, duration_h))

    nights.sort(key=lambda n: n.wake_date)
    # Deduplicate by wake_date (keep last).
    seen: dict[dt.date, Night] = {}
    for n in nights:
        seen[n.wake_date] = n
    return list(seen.values()), warnings


# --------------------------------------------------------------------------- #
# Time helpers
# --------------------------------------------------------------------------- #

def _minutes_since_noon(t: dt.datetime) -> float:
    """Clock time expressed as minutes since noon, so late-night bedtimes
    (e.g. 01:00) sort naturally after evening ones (e.g. 23:00)."""
    m = t.hour * 60 + t.minute
    ref = m - 12 * 60
    if ref < 0:
        ref += 24 * 60
    return ref


def _fmt_clock_from_noon(minutes: float) -> str:
    total = int(round(minutes)) + 12 * 60
    total %= 24 * 60
    return f"{total // 60:02d}:{total % 60:02d}"


def _fmt_hm(hours: float) -> str:
    h = int(hours)
    m = int(round((hours - h) * 60))
    if m == 60:
        h, m = h + 1, 0
    return f"{h}h {m:02d}m"
