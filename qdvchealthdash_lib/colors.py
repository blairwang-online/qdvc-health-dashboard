"""Time-of-day colour scheme.

A single continuous function maps any clock time (0–1440 min) to a colour,
forming a smooth loop over 24 hours. Anchors (minute-of-day -> colour):
  20:00 light baby blue -> 00:00 royal blue -> 03:00 purple -> 05:00 crimson
  -> 07:00 amber/orange -> 12:00 pale yellow -> (loop back to baby blue at 20:00)
Everything colour-coded by time (the clock chart, archetype tags, composites)
samples this one function, so the whole dashboard shares a consistent palette.
The JS side mirrors this via the tod_anchors payload, so the two never drift.
"""

from __future__ import annotations


_TOD_ANCHORS = [
    (20 * 60, (0xBF, 0xDD, 0xF5)),   # 20:00 light baby blue
    (24 * 60, (0x2A, 0x3C, 0xA8)),   # 24:00 royal blue
    (27 * 60, (0x6B, 0x3F, 0xB0)),   # 03:00 (as 27:00) purple
    (29 * 60, (0xC6, 0x2F, 0x45)),   # 05:00 (as 29:00) crimson red
    (31 * 60, (0xF2, 0x8A, 0x2E)),   # 07:00 (as 31:00) amber/orange
    (36 * 60, (0xF7, 0xEC, 0xB8)),   # 12:00 (as 36:00) pale yellow
    (44 * 60, (0xBF, 0xDD, 0xF5)),   # 20:00 (as 44:00) back to baby blue
]


def _tod_rgb(minute_of_day: float) -> tuple[int, int, int]:
    """Interpolate the time-of-day colour for a clock time in minutes (0–1440).
    The anchor table runs on a 20:00-based axis (evening → next midday → evening)
    so the curve is monotonic to interpolate; times before 20:00 are lifted by
    24h to land in the correct segment."""
    m = minute_of_day % 1440
    if m < 20 * 60:          # 00:00–19:59 belongs to the +24h part of the loop
        m += 1440
    for (m0, c0), (m1, c1) in zip(_TOD_ANCHORS, _TOD_ANCHORS[1:]):
        if m0 <= m <= m1:
            t = (m - m0) / (m1 - m0)
            return tuple(round(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))
    return _TOD_ANCHORS[-1][1]


def _rgb_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _tod_hex(minute_of_day: float) -> str:
    return _rgb_hex(_tod_rgb(minute_of_day))


def _clock(hhmm: str) -> int:
    h, m = int(hhmm[:2]), int(hhmm[3:])
    return h * 60 + m


# Representative clock time for each archetype bucket, used to sample the
# time-of-day palette so tags/composites match the clock chart's colours.
_BEGIN_SAMPLE = ["22:00", "01:30", "04:00"]   # early / around midnight / super late
_END_SAMPLE   = ["05:30", "07:00", "09:00"]   # Warrior / Commuter / Philosopher

_BEGIN_BG = [_tod_hex(_clock(t)) for t in _BEGIN_SAMPLE]
_END_BG   = [_tod_hex(_clock(t)) for t in _END_SAMPLE]


def _mix_hex(c1: str, c2: str) -> str:
    """Average two #rrggbb colours."""
    def comp(c):
        return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
    r1, g1, b1 = comp(c1)
    r2, g2, b2 = comp(c2)
    return f"#{(r1+r2)//2:02x}{(g1+g2)//2:02x}{(b1+b2)//2:02x}"


def _text_on(bg: str) -> str:
    """Pick a readable text colour (near-black or white) for a given
    background, using perceived luminance."""
    r, g, b = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#1a2238" if lum > 0.6 else "#ffffff"


def _pill_style(bg: str) -> str:
    return f"background:{bg};color:{_text_on(bg)}"
