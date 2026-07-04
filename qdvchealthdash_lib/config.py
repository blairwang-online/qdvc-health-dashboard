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
BEGIN_SUBTITLES = ["bedtime before midnight", "bedtime 12AM–3AM", "bedtime after 3AM"]
END_SUBTITLES   = ["wakeup before 6AM", "wakeup 6AM–8AM", "wakeup after 8AM"]

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

# Longer explanation shown in the persona modal card (one per composite).
COMPOSITE_DETAILS = [
    [  # Sleeps early + …
        "The Rested Archer is in bed before midnight and up before dawn — the "
        "textbook 'early to bed, early to rise' rhythm. With an early bedtime "
        "and an early rise, sleep tends to land squarely in the body's natural "
        "night-time window, so nights are usually full and mornings start sharp.",
        "Stockholm Winter goes down early — as if the sun set at 3pm and took "
        "the evening with it — yet still rises for the morning commute. The "
        "early bedtime buys a comfortably long night despite the ordinary wake time.",
        "Dreaming Kierkegaard is in bed early and rises late, spending long "
        "unhurried hours abed. In the spirit of the philosopher who prized "
        "staying under the covers, this pattern maximises time asleep — often "
        "well beyond what the body strictly needs.",
    ],
    [  # Around midnight + …
        "The Classic Warrior falls asleep around midnight but is up early for "
        "duty — a deliberately short night. It's a disciplined, front-loaded "
        "schedule that trades hours in bed for an early start.",
        "The Classic Commuter sleeps around midnight and wakes in the normal "
        "working-hours window — the most common, middle-of-the-road rhythm, "
        "moderate at both ends.",
        "The Classic Philosopher drifts off near midnight and rises toward "
        "late morning — the unhurried thinker's clock, shifted a little later "
        "than the commuter but with a comfortably full night.",
    ],
    [  # Super late + …
        "The Besieged Defender is up past 3am yet still rises early — like a "
        "city under siege with too few defenders to allow a full night's rest. "
        "It's the shortest pattern of all, with very few hours between lights-out "
        "and reveille.",
        "Madrid Summer keeps late hours — a late-running clock pushes bedtime "
        "well past midnight — but work still calls in the morning, so the night "
        "is squeezed from the front.",
        "Nocturnal Voltaire is fully shifted into the night: down in the small "
        "hours, up toward late morning, working and resting on a clock offset "
        "from the daylight world.",
    ],
]

# Health considerations if sleep is *regularly* classified to this composite.
# Framed as general, non-alarming guidance — not medical advice.
COMPOSITE_HEALTH = [
    [  # Sleeps early + …
        "This pattern generally supports good sleep: an early, consistent "
        "bedtime aligned with darkness tends to protect deep sleep. If you feel "
        "sleepy well before your planned bedtime or wake much earlier than "
        "intended, gentle evening light exposure can help nudge the clock later.",
        "A long, early-anchored night usually leaves you well rested. Keep an "
        "eye on very early bedtimes creeping earlier over time; a little evening "
        "activity or light can keep your schedule from drifting too far forward.",
        "Regularly spending very long stretches in bed can sometimes mean "
        "lighter, more fragmented sleep rather than more restorative sleep. If "
        "you're in bed 10+ hours but still feel unrefreshed, it's worth reflecting "
        "on sleep quality, and a clinician can help if daytime tiredness persists.",
    ],
    [  # Around midnight + …
        "Waking early after a midnight bedtime can add up to a short night. If "
        "you regularly get under ~7 hours and feel the deficit, protecting an "
        "earlier bedtime — even by 30 minutes — is usually the highest-leverage "
        "change.",
        "This balanced, moderate rhythm is a sustainable middle ground for most "
        "people. Consistency day to day (including weekends) tends to matter more "
        "for how you feel than the exact times themselves.",
        "A midnight-to-late-morning rhythm can be perfectly healthy when it's "
        "consistent and fits your life. If a late rise clashes with daytime "
        "commitments, gradually shifting both ends earlier is gentler than forcing "
        "an abrupt change.",
    ],
    [  # Super late + …
        "Very late nights with early rises make for a persistently short sleep "
        "window, and regularly running on little sleep is worth taking seriously "
        "— it can affect mood, focus, and health over time. If this is your usual "
        "pattern, prioritising a longer window when you can, and speaking with a "
        "clinician if it's unavoidable or exhausting, are both reasonable steps.",
        "Consistently late bedtimes against a fixed morning alarm tend to build "
        "a sleep debt across the week. Winding down earlier, and limiting bright "
        "screens and stimulants late in the evening, can help bedtime arrive sooner.",
        "A fully night-shifted schedule can be workable, but living offset from "
        "daylight can affect mood, metabolism, and social rhythm over the long run. "
        "Anchoring consistent sleep and wake times, and getting daylight during "
        "your waking hours, help; a clinician can advise if it's affecting how you feel.",
    ],
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
