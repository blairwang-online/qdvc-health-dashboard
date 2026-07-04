"""Sleep-archetype classification: map bedtimes and wake times to buckets,
and combine them into composite archetypes."""

from __future__ import annotations

import datetime as dt

from .config import BEGIN_ARCHETYPES, END_ARCHETYPES, COMPOSITE_ARCHETYPES


def _classify_idx(minutes: float, table) -> int:
    """Return the bucket index for a clock time (minutes) given a
    (upper_bound, label) threshold table."""
    for i, (bound, _label) in enumerate(table):
        if bound is None:
            return i
        bh, bm = map(int, bound.split(":"))
        if minutes < bh * 60 + bm:
            return i
    return len(table) - 1


def _classify(minutes_after_midnight: float, table) -> str:
    return table[_classify_idx(minutes_after_midnight, table)][1]


def _begin_minutes_for_class(start: dt.datetime) -> float:
    """Sleep-begin time as minutes after midnight for classification.
    Evening times (>= 18:00) count as 'before midnight' — represented as a
    negative offset so they sort below 00:00 and land in the first bucket."""
    m = start.hour * 60 + start.minute
    if m >= 18 * 60:          # 18:00–23:59 -> before midnight
        return m - 24 * 60    # e.g. 23:00 -> -60  (< 0, i.e. first bucket)
    return m                  # 00:00–~12:00 kept as-is


def begin_idx(start: dt.datetime) -> int:
    return _classify_idx(_begin_minutes_for_class(start), BEGIN_ARCHETYPES)


def end_idx(end: dt.datetime) -> int:
    return _classify_idx(end.hour * 60 + end.minute, END_ARCHETYPES)


def classify_begin(start: dt.datetime) -> str:
    return BEGIN_ARCHETYPES[begin_idx(start)][1]


def classify_end(end: dt.datetime) -> str:
    return END_ARCHETYPES[end_idx(end)][1]


def classify_composite(start: dt.datetime, end: dt.datetime) -> str:
    return COMPOSITE_ARCHETYPES[begin_idx(start)][end_idx(end)]
