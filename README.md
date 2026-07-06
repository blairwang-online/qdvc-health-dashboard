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
- A separate **mobile summary** (`sleep-mobile.html`) — a phone-friendly digest
  that keeps the same colours and personas but shows only the essentials:
  a simplified Decision support, the when‑you‑slept clock chart (last 7 days /
  weekly / monthly means), weekly & monthly punctuality benchmarks, and the
  past‑7‑nights persona list (with the reference grid in a pop‑up).

## Setup

The generator needs Python 3.9+ and one third‑party package (Jinja2, used to
render the HTML templates). Install it into a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

The *generated* dashboard is still a single self‑contained HTML file with no
runtime dependencies — Jinja is only used while producing it.

## Quick start

```bash
python sleep_dashboard.py path/to/sleep.csv -o sleep-desktop.html -m sleep-mobile.html
```

Then open `sleep-desktop.html` (full dashboard) or `sleep-mobile.html` (phone
summary) in your browser. With no arguments it looks for `sleep.csv` in the
current directory and writes `sleep-desktop.html` and `sleep-mobile.html`.

## CSV format

A header row followed by one row per night:

```csv
sleep_date,begin_hhmm,end_hhmm
2026-07-02,0115h,0915h
2026-07-03,2330h,0623h
```

- `sleep_date` — the morning you woke (ISO `YYYY-MM-DD`).
- `begin_hhmm` — clock time you fell asleep (`HHMMh`, e.g. `2330h`).
- `end_hhmm` — clock time you woke (`HHMMh`, e.g. `0623h`).

The trailing `h` on the time columns is a marker so spreadsheet software keeps
them as text (rather than stripping the leading zero or reformatting them as
numbers). The older suffix-less form (`2330`) is still accepted, as is an
optional colon (`23:30h`).

If `begin_hhmm` is later than `end_hhmm`, the night is assumed to cross midnight.
Missing nights are fine — just leave the row out; gaps are handled gracefully.

## Requirements

Python 3.10+ and Jinja2 (see [Setup](#setup) — `pip install -r requirements.txt`).
The *generated* HTML has no runtime dependencies and works fully offline. Not
medical advice — it's a personal insight tool.
