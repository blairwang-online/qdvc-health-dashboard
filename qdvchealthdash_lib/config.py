"""Configuration: fonts, archetype thresholds, labels, and composite naming.

All user-tunable values live here. Editing labels, thresholds, subtitles,
bounds, composite names, or blurbs changes the dashboard without touching logic.
"""

from __future__ import annotations

# Font stack used throughout the dashboard. Customise freely; the first
# available family wins, falling back rightward.
FONT_STACK = "'Andika','Iowan Old Style','Palatino Linotype',Georgia,serif"

# Decision-support: the "Perfect Asleep Time" (PAT) that Targeted Asleep Time
# (TAT) tilts toward, as "HH:MM". TAT is nudged some fraction of the way from
# the user's habitual bedtime toward PAT (fraction chosen by the on-page slider).
PERFECT_ASLEEP_TIME = "22:00"

# TAT model weights (see analysis/JS notes). Habit is the anchor (a
# recency-weighted average of recent begin times); the trend and wake-time
# terms fine-tune it; the PAT pull is applied last as a fraction.
TAT_TREND_FACTOR  = 0.5   # apply half the day-over-day begin-time drift
TAT_WAKE_FACTOR   = 0.2   # nudge per minute today's wake deviates from typical
TAT_CLAMP = ("21:00", "03:00")   # hard floor/ceiling for TAT (9PM–3AM)


BEGIN_ARCHETYPES = [
    ("00:00", "Sleeps early"),           # before midnight
    ("03:00", "Sleeps around midnight"),  # 00:00–02:59
    (None,    "Sleeps super late"),       # 03:00 onward
]
END_ARCHETYPES = [
    ("06:00", "Warrior"),       # before 6 AM
    ("08:00", "Commuter"),      # 06:00–07:59
    (None,    "Philosopher"),   # 08:00 onward
]

# At-a-glance threshold subtitles shown under each archetype in the reference
# table (bounds are approximate; inclusivity is not indicated by design).
BEGIN_SUBTITLES = ["before midnight", "12AM–3AM", "after 3AM"]
END_SUBTITLES   = ["before 6AM", "6AM–8AM", "after 8AM"]

# Bounds (in minutes on a continuous night axis, midnight = 1440) used ONLY to
# estimate the range of hours slept per cell in the reference table. Open-ended
# buckets get an assumed practical floor/ceiling as specified:
#   sleeps-early: no earlier than 9PM;  sleeps-super-late: no later than 4AM;
#   warrior: wake no earlier than 5AM;  philosopher: wake no later than 10AM.
_H = 60
BEGIN_BOUNDS = [   # (earliest bedtime, latest bedtime)
    (21 * _H,       24 * _H),        # sleeps early: 21:00 – 24:00
    (24 * _H,       27 * _H),        # around midnight: 00:00 – 03:00
    (27 * _H,       28 * _H),        # super late: 03:00 – 04:00
]
END_BOUNDS = [     # (earliest wake, latest wake), on the +1 day axis
    (5 * _H + 1440, 6 * _H + 1440),  # warrior: 05:00 – 06:00
    (6 * _H + 1440, 8 * _H + 1440),  # commuter: 06:00 – 08:00
    (8 * _H + 1440, 10 * _H + 1440), # philosopher: 08:00 – 10:00
]

# Composite archetype for each (begin bucket index, end bucket index).
# Rows = begin (early, midnight, super late); columns = end (Warrior, Commuter, Philosopher).
COMPOSITE_ARCHETYPES = [
    # Warrior              Commuter             Philosopher
    ["Rested Archer",     "Stockholm Winter",  "Dreaming Kierkegaard"],  # Sleeps early
    ["Classic Warrior",   "Classic Commuter",  "Classic Philosopher"],   # Around midnight
    ["Besieged Defender", "Madrid Summer",     "Nocturnal Voltaire"],    # Super late
]

# Short descriptions for the reference table, same row/column layout as above.
COMPOSITE_BLURBS = [
    ["Early to bed, early to rise — fresh and ready.",
     "Sun sets early, so to bed early — but still up for the commute.",
     "In bed early, up late — long hours abed, sleep as the height of genius."],
    ["Down late, up early — the standard warrior's short rest.",
     "Moderate at both ends — the everyday rhythm.",
     "Sleeps around midnight, rises near noon — the classic thinker's clock."],
    ["Up past 3am, still up early — a city under siege, too few defenders to rest.",
     "Late timezone pushes bedtime back, but work still calls in the morning.",
     "Works in bed till noon, dictates deep into the night — fully nocturnal."],
]


def _sleep_hours_range(bi: int, ei: int) -> str:
    """Approximate range of hours slept for a composite cell, from the bucket
    bounds. Max = latest wake − earliest bedtime; min = earliest wake − latest
    bedtime. Rounded to whole hours."""
    be_early, be_late = BEGIN_BOUNDS[bi]
    en_early, en_late = END_BOUNDS[ei]
    lo = (en_early - be_late) / 60
    hi = (en_late - be_early) / 60
    return f"approx. {round(lo)}–{round(hi)} hours of sleep"
