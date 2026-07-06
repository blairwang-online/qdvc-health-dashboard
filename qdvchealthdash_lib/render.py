"""HTML rendering: the composite reference grid and the full dashboard page."""

from __future__ import annotations

import html
import json

from .config import (
    FONT_STACK, BEGIN_ARCHETYPES, END_ARCHETYPES,
    BEGIN_SUBTITLES, END_SUBTITLES,
    COMPOSITE_ARCHETYPES, COMPOSITE_BLURBS,
    COMPOSITE_DETAILS, COMPOSITE_HEALTH, _sleep_hours_range,
)
from .colors import _BEGIN_BG, _END_BG, _mix_hex, _pill_style, _text_on
from .data import _fmt_hm
from .icons import persona_icon_svg
from .assets import load_css, load_js


def _json_for_script(obj) -> str:
    """Serialise ``obj`` for safe embedding inside an HTML
    ``<script type="application/json">`` block.

    JSON is valid JS, but a literal ``</script`` (or ``<!--``) in the data could
    otherwise close the tag early, so the HTML-significant characters ``<``,
    ``>`` and ``&`` are escaped to their ``\\uXXXX`` forms. These remain valid
    JSON (``JSON.parse`` restores them), so the parsed value is unchanged."""
    return (
        json.dumps(obj)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def _reference_table_html() -> str:
    """Build the static composite-archetype reference grid. Rows are begin
    buckets, columns are end buckets; each cell blends the two spectrum colours
    and shows the composite name, a blurb, and an approximate hours-slept range."""
    end_heads = "".join(
        f'<th class="ref-endhead">'
        f'<span class="ref-tag" style="{_pill_style(_END_BG[ei])}">{html.escape(lbl)}</span>'
        f'<span class="ref-sub">{html.escape(sub)}</span></th>'
        for ei, (lbl, sub) in enumerate(
            zip([e[1] for e in END_ARCHETYPES], END_SUBTITLES)
        )
    )
    rows = ""
    for bi, begin_lbl in enumerate([b[1] for b in BEGIN_ARCHETYPES]):
        sub = BEGIN_SUBTITLES[bi]
        cells = ""
        for ei in range(len(END_ARCHETYPES)):
            bg = _mix_hex(_BEGIN_BG[bi], _END_BG[ei])
            name = html.escape(COMPOSITE_ARCHETYPES[bi][ei])
            blurb = html.escape(COMPOSITE_BLURBS[bi][ei])
            hours = html.escape(_sleep_hours_range(bi, ei))
            icon = persona_icon_svg(COMPOSITE_ARCHETYPES[bi][ei], cls="persona-icon ref-icon")
            cells += (
                f'<td class="ref-cell persona-open" role="button" tabindex="0" '
                f'data-bi="{bi}" data-ei="{ei}" style="{_pill_style(bg)}">'
                f'{icon}'
                f'<span class="ref-name">{name}</span>'
                f'<span class="ref-hours">{hours}</span>'
                f'<span class="ref-blurb">{blurb}</span></td>'
            )
        rows += (
            f'<tr><th class="ref-rowhead">'
            f'<span class="ref-tag ref-tag-begin" style="{_pill_style(_BEGIN_BG[bi])}">{html.escape(begin_lbl)}</span>'
            f'<span class="ref-sub">{html.escape(sub)}</span></th>{cells}</tr>'
        )
    return (
        '<table class="reference">'
        f'<thead><tr><th class="ref-corner"></th>{end_heads}</tr></thead>'
        f'<tbody>{rows}</tbody></table>'
    )


def _persona_cards() -> list[list[dict]]:
    """Static content for each composite persona's modal card, indexed [bi][ei]
    to match the reference grid and the table's bi/ei."""
    begin_lbls = [b[1] for b in BEGIN_ARCHETYPES]
    end_lbls = [e[1] for e in END_ARCHETYPES]
    cards = []
    for bi in range(len(BEGIN_ARCHETYPES)):
        row = []
        for ei in range(len(END_ARCHETYPES)):
            bg = _mix_hex(_BEGIN_BG[bi], _END_BG[ei])
            row.append({
                "name": COMPOSITE_ARCHETYPES[bi][ei],
                "hours": _sleep_hours_range(bi, ei),
                "begin_label": begin_lbls[bi], "begin_sub": BEGIN_SUBTITLES[bi],
                "end_label": end_lbls[ei], "end_sub": END_SUBTITLES[ei],
                "begin_bg": _BEGIN_BG[bi], "begin_fg": _text_on(_BEGIN_BG[bi]),
                "end_bg": _END_BG[ei], "end_fg": _text_on(_END_BG[ei]),
                "bg": bg, "fg": _text_on(bg),
                "detail": COMPOSITE_DETAILS[bi][ei],
                "health": COMPOSITE_HEALTH[bi][ei],
                "icon": persona_icon_svg(COMPOSITE_ARCHETYPES[bi][ei],
                                         cls="persona-icon modal-icon"),
            })
        cards.append(row)
    return cards


def render_html(a: dict, warnings: list[str], source: str) -> str:
    reference_table = _reference_table_html()
    # Payloads for the two <script type="application/json"> blocks the page's JS
    # reads on load (see the tags near the end of <body> and dashboard.js).
    data_json = _json_for_script(a)
    persona_cards_json = _json_for_script(_persona_cards())

    # Static front-end assets live in files under assets/ and are inlined here at
    # generate time. The CSS still carries one Python value (the font stack) via a
    # __PLACEHOLDER__ token; the JS is fully static (it reads its data from the
    # JSON script tags), so it needs no substitution — see MAINTENANCE.md §8.
    styles = load_css().replace("__FONT_STACK__", FONT_STACK).rstrip("\n")
    scripts = load_js().rstrip("\n")

    warn_html = ""
    if warnings:
        items = "".join(f"<li>{html.escape(w)}</li>" for w in warnings[:12])
        more = "" if len(warnings) <= 12 else f"<li>… and {len(warnings) - 12} more</li>"
        warn_html = f'<details class="warn"><summary>{len(warnings)} data note(s)</summary><ul>{items}{more}</ul></details>'

    score = a["score"]
    verdict = (
        "Well rested" if score >= 80 else
        "On track" if score >= 65 else
        "Room to improve" if score >= 50 else
        "Needs attention"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sleep Health Dashboard</title>
<style>
{styles}
</style>
</head>
<body>
<div class="page">
<main class="wrap">
  <section id="sec-overview" class="navsection">
  <header>
    <div class="eyebrow">Sleep Health · {a['date_from']} → {a['date_to']}</div>
    <h1>Your sleep, at a glance</h1>
    <div class="sub">{a['recorded']} nights recorded over {a['span_days']} days
      · {a['coverage']}% coverage</div>
  </header>

  <section class="hero">
    <div class="gauge">
      <svg viewBox="0 0 120 120" aria-hidden="true">
        <defs>
          <linearGradient id="arc" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="var(--dawn1)"/>
            <stop offset="0.5" stop-color="var(--dawn2)"/>
            <stop offset="1" stop-color="var(--dawn3)"/>
          </linearGradient>
        </defs>
        <circle cx="60" cy="60" r="50" fill="none" stroke="var(--line)" stroke-width="12"/>
        <circle id="scoreArc" class="arc-fg" cx="60" cy="60" r="50" fill="none"
                stroke="url(#arc)" stroke-width="12" stroke-linecap="round"
                transform="rotate(-90 60 60)"/>
      </svg>
      <div class="val"><span class="num">{score}</span><span class="of">/ 100</span></div>
    </div>
    <div>
      <p class="verdict">{verdict}
        <small>Blends sleep duration (50%), night-to-night consistency (25%),
        and schedule regularity (25%).</small></p>
      <div class="breakdown">
        <div><b>{a['dur_score']}</b>Duration</div>
        <div><b>{a['cons_score']}</b>Consistency</div>
        <div><b>{a['reg_score']}</b>Regularity</div>
      </div>
    </div>
  </section>

  <section class="grid">
    <div class="stat"><div class="k">Avg / night</div>
      <div class="v">{_fmt_hm(a['avg'])}</div>
      <div class="n">median {_fmt_hm(a['median'])}</div></div>
    <div class="stat"><div class="k">Typical bedtime</div>
      <div class="v">{a['avg_bed']}</div>
      <div class="n">± {a['bed_sd_min']/60:.1f}h swing</div></div>
    <div class="stat"><div class="k">Typical wake</div>
      <div class="v">{a['avg_wake']}</div>
      <div class="n">± {a['wake_sd_min']/60:.1f}h swing</div></div>
    <div class="stat"><div class="k">In 7–9h range</div>
      <div class="v">{round(100*a['nights_7_9']/a['recorded'])}%</div>
      <div class="n">{a['nights_7_9']} of {a['recorded']} nights</div></div>
  </section>
  </section>

  <section id="sec-decision" class="panel navsection">
    <h2>Decision support</h2>
    <p class="cap">A realistic wind-down plan for tonight, based on your recent
      sleep pattern. Times ease you toward sleep — no pressure, just a gentle guide.</p>
    <div class="ds-ambition">
      <label for="dsSlider">Ambition toward earlier sleep</label>
      <input type="range" id="dsSlider" min="0" max="2" step="1" value="1"
             list="dsTicks" aria-label="Ambition toward earlier sleep">
      <datalist id="dsTicks"><option value="0"></option><option value="1"></option><option value="2"></option></datalist>
      <div class="ds-ticks"><span>Gentle</span><span>Moderate</span><span>Strong</span></div>
    </div>
    <div class="ds-body">
      <div class="ds-timeline" id="dsTimeline"><!-- steps injected --></div>
      <div class="ds-notes" id="dsNotes"><!-- notes injected --></div>
    </div>
  </section>

  <section id="sec-timing" class="panel navsection">
    <h2>Sleep timing &amp; trend</h2>
    <p class="cap">Hours slept on the left; the same data as actual clock time on
      the right. Switch between recent nights, weekly, and monthly aggregates.</p>
    <div class="tabs" id="timingTabs" role="tablist">
      <button class="tab active" role="tab" data-view="last7">Last 7 days</button>
      <button class="tab" role="tab" data-view="means">Weekly Means</button>
      <button class="tab" role="tab" data-view="medians">Weekly Medians</button>
      <button class="tab" role="tab" data-view="mmeans">Monthly Means</button>
      <button class="tab" role="tab" data-view="mmedians">Monthly Medians</button>
    </div>

    <div class="chart-duo">
      <div class="chart-block">
        <div class="chart-title" id="durTitle">Hours slept &amp; 7-night trend</div>
        <div id="trend"></div>
      </div>
      <div class="chart-block">
        <div class="chart-title" id="clockTitle">When you slept (clock time)</div>
        <div id="clock"></div>
      </div>
    </div>
  </section>

  <section id="sec-punctuality" class="panel navsection">
    <h2>Bedtime punctuality</h2>
    <p class="cap">How often you were in bed by each target time; higher is
      better. The <strong>benchmarks</strong> tabs draw one line per rung of a
      ladder of 30-minute targets centred on your typical bedtime, so you can
      see how reliably you hit times just earlier or later than usual. The
      <strong>thresholds</strong> tabs instead draw just two lines, for the fixed
      bedtime-archetype boundaries (midnight and 3AM) that separate sleeping
      early, around midnight, and super late. Each variant is available by ISO
      week or calendar month.</p>
    <div class="tabs" id="punctTabs" role="tablist">
      <button class="tab ptab active" role="tab" data-pview="weekly">Weekly (benchmarks)</button>
      <button class="tab ptab" role="tab" data-pview="weekly_thr">Weekly (thresholds)</button>
      <button class="tab ptab" role="tab" data-pview="monthly">Monthly (benchmarks)</button>
      <button class="tab ptab" role="tab" data-pview="monthly_thr">Monthly (thresholds)</button>
    </div>
    <div class="chart-block">
      <div class="chart-title" id="punctTitle">Weekly success rate</div>
      <div id="punct"></div>
      <div class="punct-legend" id="punctLegend"></div>
    </div>
  </section>

  <section id="sec-archetypes" class="panel navsection">
    <h2>Archetypes &amp; personas — past 7 days</h2>
    <p class="cap">Each night classified by when you fell asleep and when you woke.</p>
    <table class="archetype" id="archetypeTable">
      <thead>
        <tr>
          <th>Date</th><th>Asleep</th><th>Awake</th>
          <th>Begin archetype</th><th>End archetype</th><th>Sleep persona</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
    <p class="tablenote">Each date's sleep record refers to the night before —
      e.g. the row for Mon 29 Jun covers the sleep that began on the evening of
      Sun 28 Jun.</p>

    <div class="ref-wrap">
      <div class="chart-title">Sleep persona reference — how the two archetypes combine</div>
      {reference_table}
    </div>
  </section>

  <section id="sec-misc" class="navsection">
  <div class="cols">
    <section class="panel">
      <h2>How long you sleep</h2>
      <p class="cap">Distribution of nightly duration.</p>
      <div id="hist"></div>
    </section>
    <section class="panel">
      <h2>By day of week</h2>
      <p class="cap">Average hours slept, grouped by the morning you woke.</p>
      <div id="weekday"></div>
    </section>
  </div>

  {warn_html}
  <footer>Generated from {html.escape(source)} · not medical advice.</footer>
  </section>
</main>

  <aside class="sidebar" aria-label="Page navigation">
    <div class="side-inner">
      <div class="side-title">On this page</div>
      <nav class="side-nav">
        <a href="#sec-overview"   data-target="sec-overview">Overview</a>
        <a href="#sec-decision"   data-target="sec-decision">Decision support</a>
        <a href="#sec-timing"     data-target="sec-timing">Sleep timing &amp; trend</a>
        <a href="#sec-punctuality" data-target="sec-punctuality">Bedtime punctuality</a>
        <a href="#sec-archetypes" data-target="sec-archetypes">Archetypes &amp; personas</a>
        <a href="#sec-misc"       data-target="sec-misc">Miscellaneous</a>
        <button id="paletteOpen" class="side-nav-btn" type="button">Colour Palette</button>
      </nav>
      <div class="side-theme">
        <span class="side-theme-label">Theme</span>
        <button id="themeToggle" class="theme-btn" type="button"
                aria-label="Toggle light and dark mode">
          <span class="theme-ico theme-ico-sun">☀</span>
          <span class="theme-ico theme-ico-moon">☾</span>
          <span class="theme-knob"></span>
        </button>
      </div>
    </div>
  </aside>
</div>

<div id="paletteModal" class="modal-overlay" hidden>
  <div class="modal" role="dialog" aria-modal="true" aria-labelledby="paletteTitle">
    <div class="modal-head">
      <h2 id="paletteTitle">Time-of-day colour scheme</h2>
      <button id="paletteClose" class="modal-close" type="button"
              aria-label="Close">✕</button>
    </div>
    <p class="modal-sub">The colour used for each hour of the day. Click any
      swatch or hex code to copy it.</p>
    <div class="modal-body">
      <table class="palette-table">
        <thead><tr><th>Time of day</th><th>Colour</th><th>Hex code</th></tr></thead>
        <tbody id="paletteRows"></tbody>
      </table>
    </div>
  </div>
</div>

<div id="personaModal" class="modal-overlay" hidden>
  <div class="modal" role="dialog" aria-modal="true" aria-labelledby="personaTitle">
    <div class="modal-head persona-head" id="personaHead">
      <div class="persona-head-main">
        <span class="persona-icon-slot" id="personaIcon"></span>
        <div>
          <div class="persona-eyebrow">Sleep persona</div>
          <h2 id="personaTitle">—</h2>
        </div>
      </div>
      <button id="personaClose" class="modal-close" type="button"
              aria-label="Close">✕</button>
    </div>
    <div class="modal-body">
      <div class="persona-tags" id="personaTags"></div>
      <div class="persona-hours" id="personaHours"></div>
      <div class="persona-section">
        <h3>About this persona</h3>
        <p id="personaDetail"></p>
      </div>
      <div class="persona-section">
        <h3>Health considerations</h3>
        <p id="personaHealth"></p>
        <p class="persona-disclaimer">General guidance based on your archetype —
          not medical advice. If sleep is regularly affecting how you feel, a
          clinician can offer personalised help.</p>
      </div>
    </div>
  </div>
</div>

<script type="application/json" id="dashboard-data">{data_json}</script>
<script type="application/json" id="persona-cards">{persona_cards_json}</script>
<script>
{scripts}
</script>
</body>
</html>"""
