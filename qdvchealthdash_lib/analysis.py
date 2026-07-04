"""Analytics: weekly aggregation and the main analyse() that produces the
data dictionary consumed by the HTML renderer."""

from __future__ import annotations

import datetime as dt
import statistics
from collections import defaultdict

from .config import (
    BEGIN_ARCHETYPES, END_ARCHETYPES,
    PERFECT_ASLEEP_TIME, TAT_TREND_FACTOR,
    TAT_WAKE_FACTOR, TAT_CLAMP,
)
from .data import Night, _minutes_since_noon, _fmt_clock_from_noon
from .archetypes import (
    begin_idx, end_idx, classify_begin, classify_end, classify_composite,
)
from .colors import _TOD_ANCHORS, _BEGIN_BG, _END_BG, _mix_hex, _text_on


def _clock_to_since_noon(hhmm: str) -> int:
    """Convert a 'HH:MM' clock time to minutes-since-noon (noon = 0), matching
    the frame used by bed_min/wake_min so JS can compute TAT in one space."""
    h, m = int(hhmm[:2]), int(hhmm[3:])
    return ((h * 60 + m) - 12 * 60) % (24 * 60)


def _tat_config() -> dict:
    """Targeted-Asleep-Time parameters passed to the client. All times are in
    minutes-since-noon so the JS shares one frame with the series data."""
    lo, hi = TAT_CLAMP
    return {
        "pat": _clock_to_since_noon(PERFECT_ASLEEP_TIME),
        "trend_factor": TAT_TREND_FACTOR,
        "wake_factor": TAT_WAKE_FACTOR,
        "clamp_lo": _clock_to_since_noon(lo),
        "clamp_hi": _clock_to_since_noon(hi),
    }


def _agg_group_stats(group: list[Night], dow_label: str, dm_label: str,
                     key: str) -> dict:
    """Mean/median bedtime, waketime (minutes-since-noon + clock) and derived
    duration for a group of nights. Shared by the weekly and monthly series."""
    beds = [_minutes_since_noon(n.start) for n in group]
    durs = [n.duration_h for n in group]
    mean_bed = statistics.mean(beds)
    med_bed = statistics.median(beds)
    mean_dur_min = statistics.mean(durs) * 60
    med_dur_min = statistics.median(durs) * 60
    return {
        "dow": dow_label,
        "dm": dm_label,
        "key": key,
        "nights": len(group),
        # Means
        "mean_bed_min": round(mean_bed, 1),
        "mean_wake_min": round(mean_bed + mean_dur_min, 1),
        "mean_dur": round(mean_dur_min / 60, 2),
        "mean_bed": _fmt_clock_from_noon(mean_bed),
        "mean_wake": _fmt_clock_from_noon(mean_bed + mean_dur_min),
        # Medians
        "med_bed_min": round(med_bed, 1),
        "med_wake_min": round(med_bed + med_dur_min, 1),
        "med_dur": round(med_dur_min / 60, 2),
        "med_bed": _fmt_clock_from_noon(med_bed),
        "med_wake": _fmt_clock_from_noon(med_bed + med_dur_min),
    }


def _weekly_series(nights: list[Night], weeks_back: int = 12) -> list[dict]:
    """Aggregate nights into ISO weeks, returning the last `weeks_back` weeks
    (chronological), each with mean/median bedtime, waketime, and duration."""
    by_week: dict[tuple[int, int], list[Night]] = defaultdict(list)
    for n in nights:
        iso = n.wake_date.isocalendar()
        by_week[(iso[0], iso[1])].append(n)

    out: list[dict] = []
    for (yr, wk) in sorted(by_week)[-weeks_back:]:
        monday = dt.date.fromisocalendar(yr, wk, 1)   # week-start date for label
        out.append(_agg_group_stats(
            by_week[(yr, wk)], "Week of", monday.strftime("%-d %b"),
            f"{yr}-W{wk:02d}"))
    return out


def _monthly_series(nights: list[Night], months_back: int = 12) -> list[dict]:
    """Aggregate nights into calendar months, returning the last `months_back`
    months (chronological), each with mean/median bedtime, waketime, duration."""
    by_month: dict[tuple[int, int], list[Night]] = defaultdict(list)
    for n in nights:
        by_month[(n.wake_date.year, n.wake_date.month)].append(n)

    out: list[dict] = []
    for (yr, mo) in sorted(by_month)[-months_back:]:
        first = dt.date(yr, mo, 1)
        out.append(_agg_group_stats(
            by_month[(yr, mo)], "Month of", first.strftime("%b %Y"),
            f"{yr}-{mo:02d}"))
    return out


def analyse(nights: list[Night]) -> dict:
    if not nights:
        raise SystemExit("No valid sleep records found.")

    durations = [n.duration_h for n in nights]
    span_days = (nights[-1].wake_date - nights[0].wake_date).days + 1
    recorded = len(nights)

    # Regularity: stdev of bedtime and wake time (minutes-since-noon frame).
    bed_mins = [_minutes_since_noon(n.start) for n in nights]
    wake_mins = [_minutes_since_noon(n.end) for n in nights]
    bed_sd = statistics.pstdev(bed_mins) if len(bed_mins) > 1 else 0.0
    wake_sd = statistics.pstdev(wake_mins) if len(wake_mins) > 1 else 0.0

    # A simple sleep-health score (0-100) built from three components:
    #   duration adequacy, duration consistency, and schedule regularity.
    avg = statistics.mean(durations)
    dur_sd = statistics.pstdev(durations) if len(durations) > 1 else 0.0

    def clamp(x, lo=0.0, hi=1.0):
        return max(lo, min(hi, x))

    # Duration score: full marks for 7-9h, tapering outside.
    if 7 <= avg <= 9:
        dur_score = 1.0
    elif avg < 7:
        dur_score = clamp(1 - (7 - avg) / 3)      # 0 at ~4h
    else:
        dur_score = clamp(1 - (avg - 9) / 3)      # 0 at ~12h

    # Consistency score: smaller night-to-night duration swing is better.
    cons_score = clamp(1 - dur_sd / 2.0)          # 0 when sd >= 2h

    # Regularity score: smaller bedtime swing is better.
    reg_score = clamp(1 - bed_sd / 120.0)         # 0 when sd >= 2h

    score = round(100 * (0.5 * dur_score + 0.25 * cons_score + 0.25 * reg_score))

    # Distribution buckets.
    buckets = {"<5h": 0, "5–6h": 0, "6–7h": 0, "7–8h": 0, "8–9h": 0, "9h+": 0}
    for d in durations:
        if d < 5:
            buckets["<5h"] += 1
        elif d < 6:
            buckets["5–6h"] += 1
        elif d < 7:
            buckets["6–7h"] += 1
        elif d < 8:
            buckets["7–8h"] += 1
        elif d < 9:
            buckets["8–9h"] += 1
        else:
            buckets["9h+"] += 1

    # Weekday averages (0=Mon).
    by_wd = defaultdict(list)
    for n in nights:
        by_wd[n.wake_date.weekday()].append(n.duration_h)
    weekday_avg = [
        round(statistics.mean(by_wd[i]), 2) if by_wd[i] else None
        for i in range(7)
    ]

    # 7-night rolling average of duration, for the trend line.
    series = []
    window: list[float] = []
    for n in nights:
        window.append(n.duration_h)
        if len(window) > 7:
            window.pop(0)
        bed_m = _minutes_since_noon(n.start)
        wake_m = _minutes_since_noon(n.end)
        series.append(
            {
                "date": n.wake_date.isoformat(),
                "dow": n.wake_date.strftime("%A"),          # e.g. "Sunday"
                "dm": n.wake_date.strftime("%-d %b"),       # e.g. "28 Jun"
                "duration": round(n.duration_h, 2),
                "rolling": round(statistics.mean(window), 2),
                "bed": _fmt_clock_from_noon(bed_m),
                "wake": _fmt_clock_from_noon(bed_m + n.duration_h * 60),
                "bed_min": round(bed_m, 1),
                # End expressed on the same continuous axis as bed_min, so the
                # clock-time bar spans exactly the duration even past midnight.
                "wake_min": round(bed_m + n.duration_h * 60, 1),
            }
        )

    # Weekly aggregations (mean & median) for the last 8 ISO weeks present.
    weekly = _weekly_series(nights, weeks_back=12)
    monthly = _monthly_series(nights, months_back=12)

    # Last-7-nights archetype table (newest first).
    table7 = []
    for n in reversed(nights[-7:]):
        bi, ei = begin_idx(n.start), end_idx(n.end)
        comp_bg = _mix_hex(_BEGIN_BG[bi], _END_BG[ei])
        table7.append({
            "date": n.wake_date.strftime("%a %-d %b"),   # e.g. "Sun 28 Jun"
            "begin": n.start.strftime("%H:%M"),
            "end": n.end.strftime("%H:%M"),
            "begin_type": classify_begin(n.start),
            "end_type": classify_end(n.end),
            "composite": classify_composite(n.start, n.end),
            "bi": bi, "ei": ei,
            "begin_bg": _BEGIN_BG[bi], "begin_fg": _text_on(_BEGIN_BG[bi]),
            "end_bg": _END_BG[ei],     "end_fg": _text_on(_END_BG[ei]),
            "comp_bg": comp_bg,        "comp_fg": _text_on(comp_bg),
        })

    return {
        "recorded": recorded,
        "span_days": span_days,
        "missing": span_days - recorded,
        "coverage": round(100 * recorded / span_days, 1) if span_days else 0,
        "date_from": nights[0].wake_date.isoformat(),
        "date_to": nights[-1].wake_date.isoformat(),
        "avg": avg,
        "median": statistics.median(durations),
        "min": min(durations),
        "max": max(durations),
        "dur_sd": dur_sd,
        "avg_bed": _fmt_clock_from_noon(statistics.mean(bed_mins)),
        "avg_wake": _fmt_clock_from_noon(statistics.mean(wake_mins)),
        "bed_sd_min": bed_sd,
        "wake_sd_min": wake_sd,
        "score": score,
        "dur_score": round(dur_score * 100),
        "cons_score": round(cons_score * 100),
        "reg_score": round(reg_score * 100),
        "buckets": buckets,
        "weekday_avg": weekday_avg,
        "series": series,
        "weekly": weekly,
        "monthly": monthly,
        "table7": table7,
        "begin_labels": [lbl for _, lbl in BEGIN_ARCHETYPES],
        "end_labels": [lbl for _, lbl in END_ARCHETYPES],
        "tod_anchors": [[m, list(c)] for m, c in _TOD_ANCHORS],
        "tat_config": _tat_config(),
        "nights_7_9": sum(1 for d in durations if 7 <= d <= 9),
    }
