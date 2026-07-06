# QDVC Sleep‑Health Dashboard

A **quick and dirty, vibe-coded (QDVC)** tool that turns a simple sleep log into a single, self‑contained HTML dashboard you can open in any browser — no server, no build step, no internet connection required.

Point it at a CSV of when you fell asleep and woke up, and it produces a polished
page summarising how much you sleep, how consistent your schedule is, when you
tend to sleep, and which "sleep persona" your nights fall into.

- Vibe-coding logs in [vibe-coding/](vibe-coding/).
- See [`MAINTENANCE.md`](MAINTENANCE.md) for the architecture and a guide to
extending or modifying the dashboard.

## What you get

- **Overview & sleep‑health score** — a 0–100 score blending sleep duration,
  night‑to‑night consistency, and schedule regularity, plus at‑a‑glance stats.
- **Decision support** — a realistic, gentle wind‑down plan for tonight, with an
  ambition slider that shifts your target bedtime earlier or later.
- **Sleep timing & trend** — horizontal bar charts of hours slept and actual
  clock time, for the last 7 days or weekly/monthly aggregates.
- **Bedtime punctuality** — a line chart tracking how often you hit bedtime
  targets, with *benchmarks* (a 30-minute ladder around your typical bedtime)
  and *thresholds* (the fixed midnight / 3AM archetype boundaries) variants,
  each by week or month.
- **Archetypes & personas** — every night classified by bedtime and wake time
  into nine illustrated "sleep personas" (from *Rested Archer* to
  *Nocturnal Voltaire*), each with its own explanation and health notes.
- A cohesive **time‑of‑day colour scheme**, **light/dark mode** (auto by hour),
  and a right‑hand navigation sidebar.

## Quick start

```bash
python sleep_dashboard.py path/to/sleep.csv -o dashboard.html
```

Then open `dashboard.html` in your browser. With no arguments it looks for
`sleep.csv` in the current directory and writes `sleep_dashboard.html`.

## CSV format

A header row followed by one row per night:

```csv
sleep_date, begin_hhmm, end_hhmm
2026-07-02,0115,0915
2026-07-03,2330,0623
```

- `sleep_date` — the morning you woke (ISO `YYYY-MM-DD`).
- `begin_hhmm` — clock time you fell asleep (`HHMM`).
- `end_hhmm` — clock time you woke (`HHMM`).

If `begin_hhmm` is later than `end_hhmm`, the night is assumed to cross midnight.
Missing nights are fine — just leave the row out; gaps are handled gracefully.

## Requirements

Python 3.10+ (standard library only). The generated HTML has no runtime
dependencies. Not medical advice — it's a personal insight tool.
