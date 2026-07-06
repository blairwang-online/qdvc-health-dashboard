# Maintenance & Architecture Manual

A guide for anyone — human or AI — maintaining or extending the QDVC
Sleep‑Health Dashboard. Read this before making changes; several conventions
here are non‑obvious and easy to break.

---

## 1. What this program does

`sleep_dashboard.py` reads a CSV of nightly sleep records and emits **one
self‑contained HTML file**. All CSS and JavaScript are inlined into that file;
there are no external assets, no network calls, and no build step. The generated
page is fully static and works offline. (The CSS/JS/SVG *sources* live as
separate files under `qdvchealthdash_lib/assets/` for editability, but they are
read and inlined at generate time — see §2 and §4 — so the output is unchanged.)

The pipeline is deliberately linear:

```
CSV file ──load_nights──> [Night]         (parse + validate)
[Night]  ──analyse──────> analysis dict   (all metrics, JSON-serialisable)
analysis ──render_html──> HTML string     (page + inlined CSS/JS/SVG assets)
```

The entry point (`sleep_dashboard.py`) does only argument parsing and wiring;
all logic lives in the `qdvchealthdash_lib` package.

---

## 2. Repository layout

```
sleep_dashboard.py              CLI entry point (argparse → pipeline → write file)
qdvchealthdash_lib/
├── __init__.py                 Public API re-exports
├── config.py                   ALL tunable values (labels, thresholds, colours-as-anchors, copy)
├── colors.py                   Time-of-day colour function + helpers
├── data.py                     Night dataclass, CSV parsing, time helpers
├── archetypes.py               Bedtime/wake bucket classification + persona lookup
├── analysis.py                 analyse() and all metric/aggregation helpers
├── assets.py                   Loads the asset files below (via importlib.resources)
├── icons.py                    Maps persona names → assets/icons/*.svg + wraps them
├── render.py                   HTML template (f-string) + asset wiring
└── assets/                     Front-end sources, inlined at generate time
    ├── dashboard.css           All page CSS (placeholder: __FONT_STACK__)
    ├── dashboard.js            All chart/UI JS (placeholders: __DATA_JSON__, __PERSONA_CARDS_JSON__)
    └── icons/                  Nine persona SVGs (currentColor silhouettes), one file each
README.md                       User-facing cover page
MAINTENANCE.md                  This file
```

**Packaging note:** the files under `assets/` are package *data*. There is no
build config today (the tool runs in place), but if you ever add a
`pyproject.toml`/`setup.py`, declare `qdvchealthdash_lib/assets/**` as package
data so it ships with an installed wheel. `assets.py` reads them through
`importlib.resources`, so it works both in place and when installed.

**Public API** (`from qdvchealthdash_lib import ...`):

| Function | Signature | Purpose |
|---|---|---|
| `load_nights` | `(path: str) -> (list[Night], list[str])` | Parse CSV; returns nights + warning strings |
| `analyse` | `(nights: list[Night]) -> dict` | Compute every metric into a JSON-serialisable dict |
| `render_html` | `(analysis: dict, warnings: list[str], source: str) -> str` | Build the full HTML page |

---

## 3. The data model and time frames  (READ THIS FIRST)

### 3.1 `Night` (data.py)

```python
@dataclass
class Night:
    wake_date: dt.date       # the morning you woke (= the CSV sleep_date column)
    start: dt.datetime       # full datetime sleep began (may be the PREVIOUS day)
    end: dt.datetime         # full datetime sleep ended
    duration_h: float        # hours asleep
```

Each CSV row's `sleep_date` is **the morning you woke**, not the evening you went
to bed. If `begin_hhmm > end_hhmm`, the sleep crossed midnight, so `start` is set
to the previous calendar day. `load_nights` never raises on a bad row — it skips
it and appends a human‑readable message to the returned `warnings` list.

### 3.2 "Minutes since noon" — the critical convention

Bedtimes straddle midnight, which makes naive clock arithmetic wrong (00:30 is
"after" 23:30 but has a smaller clock value). To fix this, **all internal time
math uses "minutes since noon"**: minute‑of‑day with noon (12:00) as zero,
computed as `(minute_of_day - 720) mod 1440`.

In this frame, an evening/night progresses monotonically upward:

```
20:00 → 480     midnight → 720     03:00 → 900     06:00 → 1080
```

So "earlier bedtime" = smaller number, and "in bed by X" = `bed_min <= X`. Every
bedtime/waketime value passed around in `analysis.py` and into the JS is in this
frame. Convert to a display clock string with `data._fmt_clock_from_noon(mins)`
(Python) or `clockFromNoon(mins)` (JS — defined in the render template). **If you
add any time-based feature, stay in this frame** and only convert to "HH:MM" at
the very end.

---

## 4. Module responsibilities

### config.py — the tuning surface
Nearly everything a non‑programmer would want to change lives here:
- `FONT_STACK`.
- `BEGIN_ARCHETYPES` / `END_ARCHETYPES` — `(upper_bound_HHMM_exclusive, label)`
  tuples defining the bedtime and wake‑time buckets (last entry's bound is `None`).
- `BEGIN_SUBTITLES` / `END_SUBTITLES` — the "bedtime 12AM–3AM" style captions.
- `BEGIN_BOUNDS` / `END_BOUNDS` — practical floors/ceilings (minutes‑since‑noon)
  used only to compute the "approx. N–M hours of sleep" range per persona.
- `COMPOSITE_ARCHETYPES` — the 3×3 grid of persona names, indexed `[begin][end]`.
- `COMPOSITE_BLURBS` / `COMPOSITE_DETAILS` / `COMPOSITE_HEALTH` — reference‑table
  blurb, modal long description, and modal health guidance, same `[begin][end]`
  indexing.
- `PERFECT_ASLEEP_TIME`, `TAT_TREND_FACTOR`, `TAT_WAKE_FACTOR`, `TAT_CLAMP` —
  Decision‑support tuning (see §6).
- `_sleep_hours_range(bi, ei)` — helper for the persona hours estimate.

The three composite grids **must stay the same shape** as `COMPOSITE_ARCHETYPES`
(currently 3×3). Adding a bucket means adding a row/column to every grid.

### colors.py — one palette to rule them all
Defines `_TOD_ANCHORS`: a list of `(minute_of_day, (r,g,b))` anchors describing a
continuous 24‑hour colour loop (baby‑blue evening → royal‑blue midnight → purple
→ crimson → amber dawn → pale‑yellow noon → back). `_tod_rgb(minute_of_day)`
interpolates between anchors; `_tod_hex` returns the hex.

**This palette is emitted as literal hex, never via CSS variables**, and is
mirrored in JS (`todRgb`/`todHex`/`todHexFromNoon`, fed by the `tod_anchors`
payload). That is deliberate: it means **dark mode cannot alter the time‑of‑day
colours** (see §7). Also here: `_mix_hex` (average two colours — used for persona
blends), `_text_on` (pick black/white for contrast by luminance), `_pill_style`.

Derived module‑level values `_BEGIN_BG` / `_END_BG` sample the palette at
representative bedtimes/waketimes; personas blend the two with `_mix_hex`.

### archetypes.py — classification
`begin_idx`/`end_idx` map a datetime to a bucket index via the config thresholds
(on the minutes‑since‑noon frame); `classify_begin/end/composite` return labels.

### analysis.py — all metrics
`analyse(nights)` returns one flat, **JSON‑serialisable** dict consumed by the
renderer. Notable helpers:
- `_weekly_series` / `_monthly_series` (via shared `_agg_group_stats`) — up to 12
  ISO weeks / 12 calendar months, each with mean & median bedtime, waketime,
  duration (both as minutes‑since‑noon and formatted strings).
- `_bedtime_benchmarks(mean_bed_min)` — the punctuality benchmark ladder (§5).
- `_bedtime_thresholds()` — the fixed archetype-boundary punctuality lines (§5).
- `_punctuality_series` / `_punctuality` — per‑period success rates (§5).
- `_tat_config` — exports Decision‑support constants to JS (§6).
The returned dict also carries `tod_anchors` (for the JS palette) and `table7`
(the per‑night persona table, newest first, with precomputed colours).

### assets.py — front-end asset loader
The page's CSS, JS, and persona SVGs live as files under `assets/` (see §2), not
embedded in Python. `assets.py` reads them at generate time via
`importlib.resources` (so it works in place or installed) and caches the results.
`load_css()` / `load_js()` return the raw text (still containing their
`__PLACEHOLDER__` tokens); `load_icon_inner(slug)` returns just the inner markup
of an icon file (stripping the outer `<svg>` wrapper) so callers can re-wrap it
with a chosen CSS class. Nothing here is fetched at runtime by the generated
page — it's all inlined, preserving the offline guarantee.

### icons.py — persona illustrations
`persona_icon_svg(name, cls)` maps a persona name to its file
(`assets/icons/<slug>.svg`, slug = lower‑cased name with spaces → hyphens) via
`assets.load_icon_inner`, then wraps the inner markup in an `<svg>` with the given
class. Each icon is drawn **entirely in `currentColor` at varying opacity**,
inside a faint medallion circle. Because the icon inherits `currentColor` (set to
the card's auto‑contrast text colour) and uses translucent fills, the same icon
reads on any tint, light or dark, and the underlying tint shows through. Keep the
`0 0 100 100` viewBox and the currentColor‑only rule for new icons; add a new icon
by dropping a `<slug>.svg` into `assets/icons/` (no Python change needed as long
as the persona name maps to that slug).

### render.py — the page
Holds the HTML document skeleton as one f‑string with `{styles}` and `{scripts}`
slots; `render_html()` loads the CSS/JS from `assets.py`, fills their
`__PLACEHOLDER__` tokens (`__FONT_STACK__` in CSS; `__DATA_JSON__` and
`__PERSONA_CARDS_JSON__` in JS), and drops them into those slots. Only the HTML
body remains an f‑string (see §8 for the brace gotcha — it no longer applies to
the CSS/JS, which are now plain files). `_reference_table_html()` builds the
static persona grid; `_persona_cards()` builds the JSON the modal reads;
`render_html()` assembles everything.

---

## 5. Bedtime punctuality (benchmarks and thresholds)

Bedtime punctuality is its **own top-level section** (`#sec-punctuality`, in the
sidebar nav), rendered by `renderPunctuality(pview)` in render.py. It has two
families of target lines, each available by ISO week or calendar month, giving
four tabs: **Weekly (benchmarks)**, **Weekly (thresholds)**,
**Monthly (benchmarks)**, **Monthly (thresholds)**. The `data-pview` values are
`weekly` / `weekly_thr` / `monthly` / `monthly_thr`.

### Benchmarks
The benchmark ladder is derived from **the typical (mean) bedtime**, which is the
same value shown as "Typical bedtime" in the overview (`analysis` computes it as
`statistics.mean(bed_mins)` in minutes‑since‑noon).

`_bedtime_benchmarks(mean_bed_min)` rounds the mean to the nearest minute, then:
- **If it lands exactly on a half‑hour** → that time is `BENCHMARK_C`; `B = C−30`,
  `D = C+30` (five benchmarks total).
- **Otherwise** → the nearest half‑hours below/above are `B` and `D`; there is no
  `C` (four benchmarks total).
- In both cases `A = B−30` and `E = D+30`.

It returns a chronological list of `{code, minutes, label}`, where `label` is the
**user‑facing** string (`"In bed by 01:00"`). The internal `code` (A–E) is never
shown to the user.

### Thresholds
`_bedtime_thresholds()` returns the **fixed bedtime-archetype boundaries** from
`BEGIN_ARCHETYPES` (the finite upper bounds — currently midnight and 3AM; the
open-ended last bucket contributes none). These give exactly **two** target lines
regardless of the user's habits. Same `{code, minutes, label}` shape (codes
`T0`/`T1`), so they flow through the identical series/render path as benchmarks.

### Series and chart
`_punctuality_series(nights, marks, grouping)` groups nights by ISO week or
calendar month and, for each mark, computes the percentage of that period's
nights with `bed_min <= mark.minutes` ("in bed by"). Because later marks are
strictly easier, their lines should always sit at or above earlier ones — a
useful sanity check that holds for both benchmarks and thresholds. `_punctuality`
runs it for all four (benchmarks/thresholds × weekly/monthly) and packs them into
the payload as `weekly` / `monthly` / `weekly_thr` / `monthly_thr` alongside the
`benchmarks` and `thresholds` mark lists.

### Line colours (derived from the time-of-day palette)
Series lines are coloured from the **time-of-day palette**, sampled at each
target's clock time, so a line's hue matches the time it represents (midnight
lines blue, 3AM lines purple, etc.). Because every target clusters near one
bedtime, the raw samples would be near-identical, so `punctColor(mins, idx,
total)` in the JS keeps each sample's **hue** but spreads **both saturation and
lightness across the ladder** by the line's position: the earliest/hardest target
is darkest and most saturated (`PUNCT_LIGHT_LO`, `PUNCT_SAT_HI`), the
latest/easiest is lightest and softest (`PUNCT_LIGHT_HI`, `PUNCT_SAT_LO`), with
`PUNCT_SAT_FLOOR` guarding against fully washing out a low-saturation sample. The
ranges are bounded so adjacent same-hue lines separate strongly while every line
still reads on **both** the light and dark themes. The lines are smoothed with a
Catmull-Rom spline (`smoothPath(pts, yMin, yMax)`); its Bézier control points are
clamped to the plot band `[y(100), y(0)]` so a curve between two data points can
never bow below 0% or above 100% (the data anchors are already in range). This
still
respects the §7 invariant — the colours derive from the literal-hex palette (via
`todRgb`), never from a themed CSS variable, so they don't shift between themes.

---

## 6. Decision support (Targeted Asleep Time)

TAT is computed client‑side (it reacts to the ambition slider). The recipe, all
in minutes‑since‑noon:
1. **Habit anchor** — recency‑weighted average of the last 7 begin times (newest
   weighted most: weight `i+1`).
2. **Trend** — add `TAT_TREND_FACTOR ×` the least‑squares slope of recent begin
   times (follow drift, don't fight it).
3. **Wake adjust** — add `TAT_WAKE_FACTOR ×` how far today's wake deviates from
   the typical wake (earlier wake ⇒ earlier target).
4. **Pull to PAT** — move a slider‑chosen fraction (15% / 30% / 50%) of the
   remaining distance toward `PERFECT_ASLEEP_TIME`.
5. **Clamp** to `TAT_CLAMP`, round to the nearest 30 min.

TAT itself is **never displayed** (to avoid pressure). Only the three wind‑down
steps are shown, at TAT−90 / TAT−60 / TAT−30. Constants live in config.py and
are shipped to JS via `_tat_config()`.

---

## 7. Theming (light / dark) — and what must NOT be themed

Dark mode is implemented purely as CSS‑variable overrides under
`html[data-theme="dark"]` (see the `:root` and dark blocks near the top of
`assets/dashboard.css`). The theme defaults by local hour (dark 21:00–05:59,
light otherwise) and can be toggled from the sidebar.

**Invariant to preserve:** the time‑of‑day colour scheme must look identical in
both themes. This holds only because those colours are emitted as literal hex
from the palette (Python and the `dashboard.js` mirror), never through a CSS
variable. If you ever route a time‑of‑day colour through a `var(--…)`, dark mode
will corrupt it. Keep semantic surface colours (`--ink`, `--paper`, `--card`,
`--line`, `--inset`, `--body-2`, etc.) themed, and keep the palette literal.

---

## 8. render.py f‑string gotcha (the #1 way to break the build)

**Scope note:** since the CSS and JS now live in `assets/dashboard.css` and
`assets/dashboard.js` as plain files, they use **ordinary single braces** — edit
them like any normal CSS/JS. The gotcha below applies **only to the HTML body
that remains inside the f‑string in `render.py`**.

The HTML skeleton in `render.py` is still a single Python f‑string. Therefore,
within that string:

- **Every literal brace must be doubled**: `{` → `{{` and `}` → `}}`. A single
  unescaped brace either throws at generate time or, worse, silently interpolates
  a stray Python name. (In practice the HTML body has very few literal braces.)
- **Real interpolations use single braces**: `{styles}`, `{scripts}`,
  `{reference_table}`, `{warn_html}`, `{score}`, `{a['avg_bed']}`, etc. Anything
  substituted from Python is single‑braced.
- The `{styles}` and `{scripts}` slots receive the loaded asset text (with its
  `__PLACEHOLDER__` tokens already filled by `render_html`). Because that text is
  injected *after* f‑string evaluation, its braces are **not** subject to the
  doubling rule — another reason the CSS/JS files stay brace‑clean.

Placeholder substitution in the assets uses plain `str.replace` on distinctive
`__UPPER_SNAKE__` tokens (`__FONT_STACK__`, `__DATA_JSON__`,
`__PERSONA_CARDS_JSON__`). If you add a new Python→asset value, invent a new such
token and fill it in `render_html`; don't reintroduce f‑string interpolation into
the asset files.

After editing `render.py` **or** an asset file, **always** regenerate and run the
JS through a syntax check (see §9). `node --check` on the inlined script catches
both a stray brace in the HTML body and a plain syntax slip in `dashboard.js`.

Related: multiple tab bars exist (timing tabs `#timingTabs`, punctuality tabs
`#punctTabs` — the latter now has four tabs: benchmarks/thresholds × weekly/
monthly, keyed by `data-pview`). Tab wiring is **scoped by container id** so the
bars don't interfere. If you add another tab group, scope its click handler the
same way — never bind on a bare `.tab` selector.

---

## 9. Testing & verification workflow

There is no formal test suite; verification is done by generating and inspecting.
The standard loop after any change:

```bash
# 1. Generate from a demo CSV
python sleep_dashboard.py sleep_demo.csv -o out.html

# 2. Extract the inlined <script> and syntax-check it (needs node)
python -c "import re;open('/tmp/d.js','w').write(re.search(r'<script>(.*?)</script>',open('out.html').read(),re.S).group(1))"
node --check /tmp/d.js
#    (For a quick check of the source before generating, you can also lint
#     assets/dashboard.js directly after stubbing its two __…__ placeholders.)

# 3. (Optional) screenshot with Playwright to eyeball layout, both themes
#    document.documentElement.setAttribute('data-theme','dark'|'light')
```

Also verify the **edge cases** that have bitten past changes:
- A tiny input (e.g. 3 nights spanning one week/one month) — aggregations must
  not divide by zero or crash; `analyse` raises `SystemExit` only on *zero* valid
  rows.
- Both light and dark themes render (and the time‑of‑day colours are unchanged
  between them).
- Any new interactive control works from a fresh page load and after theme flips.

Handy invariants to assert: `len(COMPOSITE_*)==3` and each row length 3; a
`.svg` exists in `assets/icons/` for every persona name (so `persona_icon_svg`
never returns `""` for a real persona); punctuality rates are monotonic across
the ladder (benchmarks) and across the two thresholds.

---

## 10. Common change recipes

- **Reword a persona / blurb / health note** → edit the grids in `config.py`
  only. No code change.
- **Move a bucket boundary** (e.g. "super late" starts at 02:30) → edit the
  threshold in `BEGIN_ARCHETYPES`/`END_ARCHETYPES` and, if the displayed range
  changed, the matching `*_SUBTITLES` and `*_BOUNDS`.
- **Add a persona bucket** (make it 4×N) → extend `BEGIN_ARCHETYPES`, every
  `COMPOSITE_*` grid, `BEGIN_SUBTITLES`/`BEGIN_BOUNDS`, `_BEGIN_BG` sampling, and
  add an icon file per new persona under `assets/icons/`. This is the most
  invasive change; touch all grids together.
- **Redraw / add a persona icon** → edit or add `assets/icons/<slug>.svg`
  (slug = persona name lower‑cased, spaces → hyphens); keep the `0 0 100 100`
  viewBox and currentColor‑only rule. No Python change if the name→slug holds.
- **Restyle the page** → edit `assets/dashboard.css` (plain CSS, single braces).
- **Change chart/UI behaviour** → edit `assets/dashboard.js` (plain JS, single
  braces). Use the `__DATA_JSON__` / `__PERSONA_CARDS_JSON__` tokens for data.
- **Retune the colour scheme** → edit `_TOD_ANCHORS` in colors.py (Python) — the
  JS mirror is fed automatically from `tod_anchors`, so no JS edit needed.
- **Change Decision‑support behaviour** → edit the `TAT_*` constants in config.py;
  they flow to JS via `_tat_config`.
- **Adjust chart height / ordering** → in `assets/dashboard.js`,
  `renderDuration`/`renderClock` use `rowH` for per‑row height and receive
  newest‑first items from `buildView` (which `.reverse()`s the series).

---

## 11. Conventions & gotchas checklist

- Times are **minutes‑since‑noon** internally; convert to "HH:MM" only for
  display.
- The time‑of‑day palette is **literal hex**, defined once in `_TOD_ANCHORS`,
  mirrored to JS via the payload — never themed, never a CSS var.
- The `render.py` HTML body is an f‑string: **double literal braces there**. The
  CSS/JS in `assets/` are plain files (single braces); data flows in via
  `__UPPER_SNAKE__` placeholders filled in `render_html`.
- Persona icons are **`currentColor` only**, `0 0 100 100` viewBox, one `.svg`
  per persona under `assets/icons/`.
- The `analyse()` return dict must stay **JSON‑serialisable** (it is `json.dumps`‑ed
  straight into the page).
- Scope any new tab group's JS by container id.
- Internal benchmark codes (A–E) and TAT are **never shown to the user**.
- Standard library only — do not add third‑party runtime dependencies.
