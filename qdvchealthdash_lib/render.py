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
    data_json = json.dumps(a)
    reference_table = _reference_table_html()
    persona_cards_json = json.dumps(_persona_cards())
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
  :root {{
    --ink:#1a2238; --muted:#6b7394; --line:#e3e6f0;
    --paper:#fbfbfd; --card:#ffffff;
    --dawn1:#3a4a8c; --dawn2:#8a6bd1; --dawn3:#f2a65a;
    --good:#4c9a7a; --warn:#d98443; --bad:#c65f5f;
    --shadow:0 1px 2px rgba(26,34,56,.05),0 8px 24px rgba(26,34,56,.06);
    /* semantic surfaces (themed) */
    --inset:#eef0f7;            /* recessed controls: tab track, notes */
    --inset-border:var(--line);
    --body-2:#4a5170;           /* secondary body text */
    --hero-grad:linear-gradient(135deg,#f4f2fb,#fdf6ef);
    --hover-veil:rgba(255,255,255,.55);
    --sidebar-bg:#ffffff;
  }}
  html[data-theme="dark"] {{
    --ink:#e8ebf5; --muted:#9aa3c4; --line:#2b3350;
    --paper:#0f1320; --card:#171c2c;
    /* dawn accents nudged brighter so they read on dark surfaces; these are
       UI accents only — the time-of-day palette is emitted as literal hex in
       JS and is deliberately never routed through these variables. */
    --dawn1:#7d8ce0; --dawn2:#a189e0; --dawn3:#f2a65a;
    --good:#5cb894; --warn:#e0996a; --bad:#d97b7b;
    --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px rgba(0,0,0,.35);
    --inset:#1e2436; --inset-border:#2b3350;
    --body-2:#b9c0dc;
    --hero-grad:linear-gradient(135deg,#1c2036,#241c2b);
    --hover-veil:rgba(255,255,255,.06);
    --sidebar-bg:#131826;
  }}
  * {{ box-sizing:border-box; }}
  html {{ scroll-behavior:smooth; }}
  body {{
    margin:0; background:var(--paper); color:var(--ink);
    font-family:{FONT_STACK};
    -webkit-font-smoothing:antialiased;
    transition:background .35s ease, color .35s ease;
  }}
  /* page = main column + right sidebar */
  .page {{
    display:grid; grid-template-columns:minmax(0,1fr) 264px;
    gap:0; max-width:1380px; margin:0 auto; align-items:start;
  }}
  .wrap {{ max-width:1040px; margin:0 auto; padding:40px 24px 72px; }}
  html {{ scroll-padding-top:24px; }}

  /* Sidebar */
  .sidebar {{ position:sticky; top:0; height:100vh; padding:40px 22px 24px; }}
  .side-inner {{
    background:var(--sidebar-bg); border:1px solid var(--line);
    border-radius:16px; padding:18px 16px; box-shadow:var(--shadow);
  }}
  .side-title {{
    font-family:ui-monospace,'SF Mono',Menlo,monospace; font-size:10.5px;
    letter-spacing:.14em; text-transform:uppercase; color:var(--muted);
    margin:0 6px 12px;
  }}
  .side-nav {{ display:flex; flex-direction:column; gap:2px; }}
  .side-nav a {{
    display:block; padding:8px 12px; border-radius:9px; text-decoration:none;
    font-size:13.5px; color:var(--muted); border-left:2px solid transparent;
    transition:background .15s, color .15s, border-color .15s;
  }}
  .side-nav a:hover {{ color:var(--ink); background:var(--inset); }}
  .side-nav a.active {{
    color:var(--dawn1); font-weight:600; background:var(--inset);
    border-left-color:var(--dawn2);
  }}
  .side-nav-btn {{
    display:block; width:100%; text-align:left; margin-top:4px;
    padding:8px 12px; border-radius:9px; cursor:pointer;
    background:transparent; border:1px solid transparent; border-left:2px solid transparent;
    font-family:{FONT_STACK}; font-size:13.5px; color:var(--muted);
    transition:background .15s, color .15s;
  }}
  .side-nav-btn:hover {{ color:var(--dawn1); background:var(--inset); }}
  .side-nav-btn::before {{
    content:""; display:inline-block; width:9px; height:9px; border-radius:50%;
    margin-right:8px; vertical-align:middle;
    background:linear-gradient(90deg,#2a3ca8,#c62f45,#f2a65a);
  }}
  .side-theme {{
    margin-top:16px; padding-top:14px; border-top:1px solid var(--line);
    display:flex; align-items:center; justify-content:space-between; padding-left:6px;
  }}
  .side-theme-label {{
    font-family:ui-monospace,monospace; font-size:10.5px; letter-spacing:.12em;
    text-transform:uppercase; color:var(--muted);
  }}
  .theme-btn {{
    position:relative; width:56px; height:28px; border-radius:999px; cursor:pointer;
    border:1px solid var(--line); background:var(--inset); padding:0;
    display:inline-flex; align-items:center; justify-content:space-between;
    transition:background .3s;
  }}
  .theme-ico {{ font-size:13px; line-height:1; z-index:1; pointer-events:none;
    width:28px; text-align:center; }}
  .theme-ico-sun {{ color:var(--dawn3); }}
  .theme-ico-moon {{ color:var(--dawn2); }}
  .theme-knob {{
    position:absolute; top:2px; left:2px; width:22px; height:22px; border-radius:50%;
    background:var(--card); box-shadow:0 1px 3px rgba(0,0,0,.3);
    transition:transform .3s ease;
  }}
  html[data-theme="dark"] .theme-knob {{ transform:translateX(28px); }}
  .theme-btn:focus-visible {{ outline:2px solid var(--dawn2); outline-offset:2px; }}

  /* Colour-palette modal */
  .modal-overlay {{
    position:fixed; inset:0; z-index:100; display:flex;
    align-items:flex-start; justify-content:center; padding:6vh 20px;
    background:rgba(10,14,24,.55); backdrop-filter:blur(2px);
    animation:fadein .18s ease;
  }}
  .modal-overlay[hidden] {{ display:none; }}
  @keyframes fadein {{ from {{ opacity:0; }} }}
  .modal {{
    background:var(--card); color:var(--ink); border:1px solid var(--line);
    border-radius:18px; box-shadow:0 20px 60px rgba(0,0,0,.35);
    width:min(520px,100%); max-height:86vh; display:flex; flex-direction:column;
  }}
  .modal-head {{
    display:flex; align-items:center; justify-content:space-between;
    padding:20px 24px 6px;
  }}
  .modal-head h2 {{ margin:0; font-size:20px; font-weight:600; }}
  .modal-close {{
    appearance:none; border:0; background:transparent; cursor:pointer;
    font-size:18px; line-height:1; color:var(--muted); padding:6px; border-radius:8px;
  }}
  .modal-close:hover {{ color:var(--ink); background:var(--inset); }}
  .modal-sub {{ margin:0; padding:0 24px 12px; color:var(--muted); font-size:13px; }}
  .modal-body {{ overflow-y:auto; padding:0 24px 22px; }}
  table.palette-table {{ width:100%; border-collapse:collapse; }}
  table.palette-table th {{
    position:sticky; top:0; background:var(--card);
    font-family:ui-monospace,monospace; font-size:10.5px; letter-spacing:.1em;
    text-transform:uppercase; color:var(--muted); font-weight:600;
    text-align:left; padding:8px 10px; border-bottom:1px solid var(--line);
  }}
  table.palette-table td {{
    padding:7px 10px; border-bottom:1px solid var(--line); font-size:14px;
    vertical-align:middle;
  }}
  table.palette-table td.pal-time {{ font-family:ui-monospace,monospace; }}
  .swatch {{
    width:26px; height:26px; border-radius:50%; border:0; cursor:pointer; padding:0;
    box-shadow:0 0 0 1px var(--line), 0 1px 3px rgba(0,0,0,.25);
    transition:box-shadow .15s ease, transform .1s ease;
  }}
  .swatch:hover {{
    box-shadow:0 0 0 1px var(--line), 0 4px 12px rgba(0,0,0,.4); transform:translateY(-1px);
  }}
  .hexbtn {{
    appearance:none; border:1px solid var(--line); background:var(--inset);
    cursor:pointer; font-family:ui-monospace,monospace; font-size:13px;
    color:var(--ink); padding:5px 10px; border-radius:8px; transition:box-shadow .15s;
  }}
  .hexbtn:hover {{ box-shadow:0 3px 10px rgba(0,0,0,.3); }}
  .hexbtn.copied {{ color:var(--good); border-color:var(--good); }}

  /* Persona-card affordance + modal */
  .persona-open {{ cursor:pointer; transition:box-shadow .15s ease, transform .1s ease; }}
  .ref-cell.persona-open:hover {{
    box-shadow:0 6px 18px rgba(0,0,0,.28); transform:translateY(-2px);
  }}
  .pill.persona-open:hover {{ box-shadow:0 3px 10px rgba(0,0,0,.3); transform:translateY(-1px); }}
  .persona-open:focus-visible {{ outline:2px solid var(--dawn2); outline-offset:2px; }}
  .persona-head {{
    align-items:flex-start; border-radius:18px 18px 0 0; padding:20px 24px;
    margin:-1px -1px 0;  /* cover the modal border under the tinted header */
  }}
  .persona-eyebrow {{
    font-family:ui-monospace,monospace; font-size:10.5px; letter-spacing:.14em;
    text-transform:uppercase; opacity:.8; margin-bottom:4px;
  }}
  .persona-head h2 {{ font-size:24px; }}
  .persona-tags {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap;
    margin:18px 0 8px; }}
  .persona-tag {{
    display:inline-flex; flex-direction:column; align-items:flex-start;
    padding:6px 12px; border-radius:12px; font-weight:600; font-size:13.5px;
    line-height:1.25;
  }}
  .persona-tag small {{ font-weight:400; font-size:10.5px; opacity:.85;
    font-family:ui-monospace,monospace; margin-top:2px; }}
  .persona-plus {{ color:var(--muted); font-weight:600; }}
  .persona-hours {{
    font-family:ui-monospace,monospace; font-size:12.5px; color:var(--muted);
    margin-bottom:6px;
  }}
  .persona-section {{ margin-top:18px; }}
  .persona-section h3 {{
    font-family:ui-monospace,monospace; font-size:11px; letter-spacing:.1em;
    text-transform:uppercase; color:var(--muted); margin:0 0 8px;
  }}
  .persona-section p {{ margin:0; font-size:14.5px; line-height:1.55; color:var(--ink); }}
  .persona-disclaimer {{ margin-top:10px !important; font-size:12px !important;
    color:var(--muted) !important; font-style:italic; }}

  /* Persona icons (currentColor silhouettes; inherit the element's text colour) */
  .persona-icon {{ display:block; color:inherit; }}
  td.ref-cell {{ position:relative; }}
  .ref-icon {{ position:absolute; top:9px; right:9px; width:46px; height:46px; opacity:.9; }}
  td.ref-cell .ref-name, td.ref-cell .ref-hours, td.ref-cell .ref-blurb {{
    padding-right:52px;  /* keep text clear of the corner icon */
  }}
  .persona-head-main {{ display:flex; align-items:center; gap:16px; }}
  .persona-icon-slot {{ flex:0 0 auto; }}
  .modal-icon {{ width:68px; height:68px; color:inherit; }}

  @media (max-width:900px) {{
    .page {{ grid-template-columns:1fr; }}
    .sidebar {{ position:static; height:auto; padding:0 24px 8px;
      max-width:1040px; margin:0 auto; }}
    .side-inner {{ display:flex; align-items:center; gap:14px;
      overflow-x:auto; }}
    .side-title {{ display:none; }}
    .side-nav {{ flex-direction:row; flex:1; }}
    .side-nav a {{ border-left:0; border-bottom:2px solid transparent; white-space:nowrap; }}
    .side-nav a.active {{ border-left:0; border-bottom-color:var(--dawn2); }}
    .side-theme {{ margin:0; padding:0 0 0 10px; border-top:0;
      border-left:1px solid var(--line); }}
    .side-theme-label {{ display:none; }}
  }}
  header {{ margin-bottom:8px; }}
  .eyebrow {{
    font-family:ui-monospace,'SF Mono',Menlo,monospace; font-size:12px;
    letter-spacing:.18em; text-transform:uppercase; color:var(--muted);
  }}
  h1 {{ font-size:38px; line-height:1.1; margin:6px 0 4px; font-weight:600; }}
  .sub {{ color:var(--muted); font-size:15px; }}

  /* Hero: the sleep-health score as an arc */
  .hero {{
    display:grid; grid-template-columns:auto 1fr; gap:36px;
    align-items:center; margin:32px 0 28px; padding:28px 32px;
    background:var(--hero-grad);
    border:1px solid var(--line); border-radius:20px; box-shadow:var(--shadow);
  }}
  .gauge {{ position:relative; width:184px; height:184px; }}
  .gauge .val {{
    position:absolute; inset:0; display:flex; flex-direction:column;
    align-items:center; justify-content:center;
  }}
  .gauge .num {{ font-size:52px; font-weight:600; line-height:1; }}
  .gauge .of {{ font-size:13px; color:var(--muted); margin-top:4px;
    font-family:ui-monospace,monospace; }}
  .verdict {{ font-size:26px; margin:0 0 6px; }}
  .verdict small {{ display:block; font-size:14px; color:var(--muted);
    font-family:ui-monospace,monospace; letter-spacing:.04em; margin-top:8px;}}
  .breakdown {{ margin-top:14px; display:flex; gap:22px; flex-wrap:wrap; }}
  .breakdown div {{ font-size:13px; color:var(--muted); }}
  .breakdown b {{ display:block; font-size:22px; color:var(--ink); font-weight:600; }}

  .grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:26px; }}
  .stat {{
    background:var(--card); border:1px solid var(--line); border-radius:14px;
    padding:18px 18px 16px; box-shadow:var(--shadow);
  }}
  .stat .k {{ font-family:ui-monospace,monospace; font-size:11px;
    letter-spacing:.1em; text-transform:uppercase; color:var(--muted); }}
  .stat .v {{ font-size:30px; font-weight:600; margin-top:6px; }}
  .stat .n {{ font-size:12.5px; color:var(--muted); margin-top:2px; }}

  .panel {{
    background:var(--card); border:1px solid var(--line); border-radius:16px;
    padding:22px 24px; box-shadow:var(--shadow); margin-bottom:22px;
  }}
  .panel h2 {{ font-size:19px; margin:0 0 2px; font-weight:600; }}
  .panel p.cap {{ margin:0 0 16px; color:var(--muted); font-size:13.5px; }}

  .tabs {{
    display:flex; flex-wrap:wrap; gap:4px; margin:6px 0 22px; padding:4px;
    background:var(--inset); border:1px solid var(--inset-border);
    border-radius:12px; width:max-content; max-width:100%;
  }}
  .tab {{
    appearance:none; border:1px solid transparent; background:transparent; cursor:pointer;
    font-family:ui-monospace,'SF Mono',Menlo,monospace; font-size:12.5px;
    letter-spacing:.02em; color:var(--muted); padding:8px 16px;
    border-radius:9px; transition:all .15s ease; white-space:nowrap;
  }}
  .tab:hover {{ color:var(--ink); background:var(--hover-veil); }}
  .tab.active {{
    color:var(--dawn1); font-weight:600; background:var(--card);
    border-color:var(--line);
    box-shadow:0 1px 2px rgba(26,34,56,.08), 0 2px 6px rgba(58,74,140,.10);
  }}
  .tab.active::before {{
    content:""; display:inline-block; width:7px; height:7px; border-radius:50%;
    margin-right:7px; vertical-align:middle;
    background:linear-gradient(135deg,var(--dawn2),var(--dawn3));
  }}
  .tab:focus-visible {{ outline:2px solid var(--dawn2); outline-offset:2px; }}
  /* Dark mode: the active tab must read as raised/selected, and inactive tabs
     should recede rather than glow. */
  html[data-theme="dark"] .tabs {{ background:#10141f; }}
  html[data-theme="dark"] .tab {{ color:var(--muted); }}
  html[data-theme="dark"] .tab:hover {{ color:var(--ink); background:rgba(255,255,255,.05); }}
  html[data-theme="dark"] .tab.active {{
    color:#dfe4ff; background:#2a3358; border-color:#3b4675;
    box-shadow:0 1px 3px rgba(0,0,0,.5);
  }}

  /* two charts side by side */
  .chart-duo {{ display:grid; grid-template-columns:1fr 1fr; gap:26px; margin-top:8px; }}
  .chart-block {{ min-width:0; }}
  .chart-title {{
    font-family:ui-monospace,monospace; font-size:11px; letter-spacing:.1em;
    text-transform:uppercase; color:var(--muted); margin-bottom:10px;
  }}
  @media (max-width:720px) {{ .chart-duo {{ grid-template-columns:1fr; gap:22px; }} }}

  /* Decision support */
  .ds-ambition {{ margin:4px auto 24px; max-width:420px; text-align:center; }}
  .ds-ambition label {{
    display:block; font-family:ui-monospace,monospace; font-size:11px;
    letter-spacing:.08em; text-transform:uppercase; color:var(--muted);
    margin-bottom:8px;
  }}
  .ds-ambition input[type=range] {{ width:100%; accent-color:var(--dawn2); }}
  .ds-ticks {{ display:flex; justify-content:space-between; margin-top:4px;
    font-family:ui-monospace,monospace; font-size:11px; color:var(--muted); }}
  .ds-body {{ display:grid; grid-template-columns:1.05fr 0.95fr; gap:28px; }}
  .ds-timeline {{ position:relative; }}
  .ds-step {{
    position:relative; display:grid; grid-template-columns:52px 22px 1fr;
    gap:10px; align-items:start; padding:0 0 22px 0;
  }}
  .ds-step:last-child {{ padding-bottom:0; }}
  /* vertical connector line runs through the dot column (middle column) */
  .ds-step::before {{
    content:""; position:absolute; left:72px; top:20px; bottom:-2px; width:2px;
    background:var(--line); transform:translateX(-50%);
  }}
  .ds-step:last-child::before {{ display:none; }}
  .ds-time {{
    font-family:ui-monospace,monospace; font-size:14px; font-weight:600;
    color:var(--ink); text-align:right; padding-top:1px; white-space:nowrap;
  }}
  .ds-dot {{
    display:block; width:15px; height:15px; border-radius:50%; margin:2px auto 0;
    border:3px solid var(--card); box-shadow:0 0 0 1px var(--line);
    position:relative; z-index:1;
  }}
  .ds-steptitle {{ font-weight:600; font-size:14.5px; margin-bottom:2px; }}
  .ds-stepbody {{ font-size:13px; color:var(--body-2); line-height:1.4; }}
  .ds-notes {{
    background:var(--inset); border:1px solid var(--inset-border); border-radius:14px;
    padding:18px 20px; align-self:start;
  }}
  .ds-notes h3 {{
    font-family:ui-monospace,monospace; font-size:11px; letter-spacing:.1em;
    text-transform:uppercase; color:var(--muted); margin:0 0 12px;
  }}
  .ds-notes ul {{ margin:0; padding-left:18px; }}
  .ds-notes li {{ font-size:13px; line-height:1.5; color:var(--body-2); margin-bottom:9px; }}
  .ds-notes li:last-child {{ margin-bottom:0; }}
  .ds-notes b {{ color:var(--ink); }}
  @media (max-width:720px) {{ .ds-body {{ grid-template-columns:1fr; gap:22px; }} }}

  .cols {{ display:grid; grid-template-columns:1fr 1fr; gap:22px; }}
  svg {{ display:block; width:100%; height:auto; overflow:visible; }}
  .axis {{ font-family:ui-monospace,monospace; font-size:10.5px; fill:var(--muted); }}
  .axis-top {{ font-weight:600; fill:var(--ink); }}
  .axis-date {{ fill:var(--muted); }}

  table.archetype {{ width:100%; border-collapse:collapse; margin-top:4px; }}
  table.archetype th {{
    text-align:left; font-family:ui-monospace,monospace; font-size:10.5px;
    letter-spacing:.1em; text-transform:uppercase; color:var(--muted);
    font-weight:600; padding:0 12px 10px; border-bottom:1px solid var(--line);
  }}
  table.archetype td {{
    padding:12px; border-bottom:1px solid var(--line); font-size:15px;
    vertical-align:middle;
  }}
  table.archetype tr:last-child td {{ border-bottom:0; }}
  table.archetype td.date {{ font-weight:600; white-space:nowrap; }}
  table.archetype td.time {{ font-family:ui-monospace,monospace; font-size:14px;
    color:var(--ink); }}
  .pill {{
    display:inline-block; padding:4px 12px; border-radius:999px;
    font-size:13px; font-weight:600; line-height:1.3; white-space:nowrap;
  }}
  .tablenote {{ margin:16px 0 0; color:var(--muted); font-size:12.5px;
    font-style:italic; }}

  .ref-wrap {{ margin-top:28px; padding-top:22px; border-top:1px dashed var(--line);
    overflow-x:auto; }}
  table.reference {{ width:100%; border-collapse:separate; border-spacing:6px;
    table-layout:fixed; min-width:560px; }}
  table.reference th.ref-corner {{ width:130px; }}
  table.reference th.ref-endhead, table.reference th.ref-rowhead {{
    text-align:left; padding:6px 8px; vertical-align:middle;
  }}
  table.reference .ref-tag {{
    display:inline-block; padding:4px 12px; border-radius:999px;
    font-family:ui-monospace,monospace; font-size:12px; font-weight:600;
    line-height:1.3;
  }}
  /* Begin-archetype tag: forward-pointing pentagon ("|||>") whose point aims
     at the persona cells to its right. Block-level so multi-line labels form a
     consistent shape (a rectangle with a point) rather than an uneven pill. */
  table.reference .ref-tag-begin {{
    display:block; border-radius:8px; padding:7px 20px 7px 12px;
    clip-path:polygon(0 0, calc(100% - 12px) 0, 100% 50%, calc(100% - 12px) 100%, 0 100%);
    text-align:left; white-space:normal;
  }}
  table.reference .ref-sub {{
    display:block; font-family:ui-monospace,monospace; font-size:10px;
    font-weight:400; letter-spacing:.04em; color:var(--muted); margin-top:4px;
  }}
  table.reference th.ref-endhead {{ text-align:center; }}
  td.ref-cell {{
    border-radius:10px; padding:11px 12px; vertical-align:top;
    border:1px solid rgba(26,34,56,.08);
  }}
  td.ref-cell .ref-name {{ display:block; font-weight:700; font-size:14px;
    color:inherit; }}
  td.ref-cell .ref-hours {{ display:block; font-family:ui-monospace,monospace;
    font-size:10.5px; font-weight:600; letter-spacing:.02em; margin-top:3px;
    color:inherit; opacity:.8; }}
  td.ref-cell .ref-blurb {{ display:block; font-size:11.5px; line-height:1.35;
    color:inherit; opacity:.85; margin-top:6px; }}
  @media (max-width:640px) {{
    table.archetype th:nth-child(2), table.archetype td:nth-child(2),
    table.archetype th:nth-child(3), table.archetype td:nth-child(3) {{
      display:none;  /* hide raw times on very narrow screens */
    }}
  }}
  .warn {{ font-size:13px; color:var(--muted); margin-top:8px; }}
  .warn summary {{ cursor:pointer; }}
  .warn ul {{ margin:8px 0 0; padding-left:18px; }}
  footer {{ color:var(--muted); font-size:12px; margin-top:28px;
    font-family:ui-monospace,monospace; }}
  @media (max-width:760px) {{
    .hero {{ grid-template-columns:1fr; text-align:center; justify-items:center; }}
    .grid {{ grid-template-columns:repeat(2,1fr); }}
    .cols {{ grid-template-columns:1fr; }}
  }}
  @media (prefers-reduced-motion:no-preference) {{
    .arc-fg {{ animation:draw 1.1s ease-out forwards; }}
    @keyframes draw {{ from {{ stroke-dashoffset:var(--circ); }} }}
  }}
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
    <div class="tabs" role="tablist">
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

  <section id="sec-archetypes" class="panel navsection">
    <h2>Archetypes and personas — past 7 days</h2>
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
        <a href="#sec-archetypes" data-target="sec-archetypes">Archetypes and personas</a>
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

<script>
const A = {data_json};
const PERSONA_CARDS = {persona_cards_json};

// Animate the score arc.
(function(){{
  const r=50, circ=2*Math.PI*r, arc=document.getElementById('scoreArc');
  const frac=Math.max(0,Math.min(1,A.score/100));
  arc.style.setProperty('--circ', circ);
  arc.setAttribute('stroke-dasharray', circ);
  arc.setAttribute('stroke-dashoffset', circ*(1-frac));
}})();

const SVGNS='http://www.w3.org/2000/svg';
function el(tag,attrs){{const e=document.createElementNS(SVGNS,tag);
  for(const k in attrs)e.setAttribute(k,attrs[k]);return e;}}
function css(v){{return getComputedStyle(document.documentElement).getPropertyValue(v).trim();}}

// Band scale: each item gets an equal-width slot; bars are centred in their
// slot and never exceed it. Endpoints stay fully inside the plot area (unlike
// point spacing, which pins the first/last item to the margins and lets wide
// bars bleed out when there are few items).
function bandScale(n, mL, iw){{
  const slot = iw / Math.max(1, n);
  return {{
    slot,
    center: i => mL + slot * (i + 0.5),
    barWidth: Math.max(2, Math.min(slot * 0.62, 64)),  // capped so 1–2 items look sane
  }};
}}

// Two-line x-axis tick: weekday/"Week of" on top, date beneath.
function twoLineLabel(svg, cx, yBase, top, bottom){{
  const t1 = el('text', {{x:cx, y:yBase, 'text-anchor':'middle'}});
  t1.setAttribute('class','axis axis-top'); t1.textContent = top;
  svg.appendChild(t1);
  const t2 = el('text', {{x:cx, y:yBase + 13, 'text-anchor':'middle'}});
  t2.setAttribute('class','axis axis-date'); t2.textContent = bottom;
  svg.appendChild(t2);
}}

// Vertical band scale for horizontal bar charts: each item gets an equal-height
// row slot; bars are centred within their slot.
function bandScaleY(n, mT, ih){{
  const slot = ih / Math.max(1, n);
  return {{
    slot,
    center: i => mT + slot * (i + 0.5),
    barHeight: Math.max(6, Math.min(slot * 0.62, 26)),
  }};
}}

// Two-line row label (left of a horizontal chart), right-aligned to the axis.
function rowLabel(svg, xRight, yMid, top, bottom){{
  const t1 = el('text', {{x:xRight, y:yMid-2, 'text-anchor':'end'}});
  t1.setAttribute('class','axis axis-top'); t1.textContent = top;
  svg.appendChild(t1);
  const t2 = el('text', {{x:xRight, y:yMid+11, 'text-anchor':'end'}});
  t2.setAttribute('class','axis axis-date'); t2.textContent = bottom;
  svg.appendChild(t2);
}}

// ---- Clock helpers (minutes-since-noon -> "HH:MM") ---------------------- //
function clockFromNoon(mins){{
  let total=Math.round(mins)+720; total=((total%1440)+1440)%1440;
  return String(Math.floor(total/60)).padStart(2,'0')+':'+String(total%60).padStart(2,'0');
}}

// Time-of-day colour: mirrors the Python _tod_rgb. Anchors come from A.tod_anchors
// (minute-of-day on a 20:00-based axis -> [r,g,b]). Input is minute-of-day 0–1440.
function todRgb(minuteOfDay){{
  const A0=A.tod_anchors;
  let m=((minuteOfDay%1440)+1440)%1440;
  if(m < 20*60) m+=1440;
  for(let i=0;i<A0.length-1;i++){{
    const [m0,c0]=A0[i], [m1,c1]=A0[i+1];
    if(m>=m0 && m<=m1){{
      const t=(m-m0)/(m1-m0);
      return [0,1,2].map(k=>Math.round(c0[k]+(c1[k]-c0[k])*t));
    }}
  }}
  return A0[A0.length-1][1];
}}
function todHex(minuteOfDay){{
  const c=todRgb(minuteOfDay);
  return '#'+c.map(x=>x.toString(16).padStart(2,'0')).join('');
}}
// Axis value is minutes-since-noon; convert to minute-of-day for the palette.
function todHexFromNoon(minsSinceNoon){{
  return todHex(((Math.round(minsSinceNoon)+720)%1440+1440)%1440);
}}

// Normalise the active tab into a common item shape.
function buildView(view){{
  if(view==='last7'){{
    const s=A.series.slice(-7);
    return {{
      hasRolling:true,
      items:s.map(d=>({{
        dow:d.dow, dm:d.dm, duration:d.duration, rolling:d.rolling,
        bed_min:d.bed_min, wake_min:d.wake_min, bed:d.bed, wake:d.wake
      }}))
    }};
  }}
  const stat = (view==='means' || view==='mmeans') ? 'mean' : 'med';
  const src  = (view==='means' || view==='medians') ? A.weekly : A.monthly;
  const agg = {{ b:stat+'_bed_min', w:stat+'_wake_min', d:stat+'_dur',
                bc:stat+'_bed', wc:stat+'_wake' }};
  return {{
    hasRolling:false,
    items:src.map(w=>({{
      dow:w.dow, dm:w.dm, duration:w[agg.d], rolling:null,
      bed_min:w[agg.b], wake_min:w[agg.w], bed:w[agg.bc], wake:w[agg.wc],
      nights:w.nights
    }}))
  }};
}}

// ---- Duration chart (hours) — horizontal bars --------------------------- //
function renderDuration(v){{
  const s=v.items, host=document.getElementById('trend');
  host.innerHTML='';
  if(!s.length){{ host.innerHTML='<p class="axis">No data.</p>'; return; }}
  const rowH=Math.max(26, Math.min(40, 300/s.length));
  const mL=104, mR=18, mT=10, mB=30;
  const H=mT+mB+rowH*s.length, W=480, iw=W-mL-mR, ih=H-mT-mB;
  const svg=el('svg',{{viewBox:`0 0 ${{W}} ${{H}}`}});
  const maxD=Math.max(10, Math.ceil(Math.max(...s.map(d=>d.duration))));
  const B=bandScaleY(s.length, mT, ih);
  const cy=i=>B.center(i);
  const x=val=> mL + (val/maxD)*iw;   // hours -> horizontal position
  // target band 7-9h (vertical strip)
  svg.appendChild(el('rect',{{x:x(7),y:mT,width:x(9)-x(7),height:ih,
    fill:css('--good'),opacity:0.12}}));
  // vertical gridlines every 2h
  for(let h=0;h<=maxD;h+=2){{
    svg.appendChild(el('line',{{x1:x(h),y1:mT,x2:x(h),y2:mT+ih,
      stroke:css('--line'),'stroke-width':1}}));
    const t=el('text',{{x:x(h),y:H-12,'text-anchor':'middle'}});
    t.setAttribute('class','axis'); t.textContent=h+'h'; svg.appendChild(t);
  }}
  // bars (uniform styling across all tabs)
  s.forEach((d,i)=>{{
    svg.appendChild(el('rect',{{x:mL,y:cy(i)-B.barHeight/2,
      width:Math.max(1,x(d.duration)-mL),height:B.barHeight,
      fill:css('--dawn2'),opacity:0.85,rx:3}}));
  }});
  // last7 rolling trend line connecting bar ends down the rows
  if(v.hasRolling){{
    let path='';
    s.forEach((d,i)=>{{ path+=(i?'L':'M')+x(d.rolling)+' '+cy(i); }});
    svg.appendChild(el('path',{{d:path,fill:'none',stroke:css('--dawn1'),
      'stroke-width':2,'stroke-linejoin':'round',opacity:.9}}));
    s.forEach((d,i)=>{{ svg.appendChild(el('circle',{{cx:x(d.rolling),cy:cy(i),
      r:2.5,fill:css('--dawn1'),opacity:.9}})); }});
  }}
  // row labels (left)
  s.forEach((d,i)=>{{ rowLabel(svg, mL-10, cy(i), d.dow, d.dm); }});
  host.appendChild(svg);
}}

// ---- Clock-time chart (when sleep happened) — horizontal bars ----------- //
function renderClock(v){{
  const s=v.items, host=document.getElementById('clock');
  host.innerHTML='';
  if(!s.length){{ host.innerHTML='<p class="axis">No data.</p>'; return; }}
  const rowH=Math.max(26, Math.min(40, 300/s.length));
  const mL=104, mR=18, mT=10, mB=30;
  const H=mT+mB+rowH*s.length, W=480, iw=W-mL-mR, ih=H-mT-mB;
  const svg=el('svg',{{viewBox:`0 0 ${{W}} ${{H}}`}});
  // x domain from data (minutes-since-noon), padded to whole 2-hour marks.
  let lo=Math.min(...s.map(d=>d.bed_min)), hi=Math.max(...s.map(d=>d.wake_min));
  lo=Math.floor((lo-30)/120)*120; hi=Math.ceil((hi+30)/120)*120;
  const x=m=> mL + ((m-lo)/(hi-lo))*iw;   // earlier -> left, later -> right
  // Gradient anchored to the x-axis in user space, so a given clock time is the
  // same colour on every bar. Colours come from the shared time-of-day palette.
  const defs=el('defs',{{}});
  const lg=el('linearGradient',{{id:'barGrad',gradientUnits:'userSpaceOnUse',
    x1:x(lo),y1:'0',x2:x(hi),y2:'0'}});
  const STEP=15;
  for(let m=lo; m<=hi; m+=STEP){{
    const off=(x(m)-x(lo))/(x(hi)-x(lo));   // 0 at left (lo), 1 at right (hi)
    lg.appendChild(el('stop',{{offset:off.toFixed(4),'stop-color':todHexFromNoon(m)}}));
  }}
  defs.appendChild(lg); svg.appendChild(defs);
  // vertical gridlines + time labels every 2h
  for(let m=lo;m<=hi;m+=120){{
    svg.appendChild(el('line',{{x1:x(m),y1:mT,x2:x(m),y2:mT+ih,
      stroke:css('--line'),'stroke-width':1}}));
    const t=el('text',{{x:x(m),y:H-12,'text-anchor':'middle'}});
    t.setAttribute('class','axis'); t.textContent=clockFromNoon(m); svg.appendChild(t);
  }}
  const B=bandScaleY(s.length, mT, ih);
  const cy=i=>B.center(i);
  s.forEach((d,i)=>{{
    const xL=x(d.bed_min), xR=x(d.wake_min);
    svg.appendChild(el('rect',{{x:xL,y:cy(i)-B.barHeight/2,
      width:Math.max(1,xR-xL),height:B.barHeight,rx:3,
      fill:'url(#barGrad)',opacity:0.92}}));
  }});
  // row labels (left)
  s.forEach((d,i)=>{{ rowLabel(svg, mL-10, cy(i), d.dow, d.dm); }});
  host.appendChild(svg);
}}

// ---- Tab wiring --------------------------------------------------------- //
function showView(view){{
  const v=buildView(view);
  const durWord = view==='last7' ? 'Hours slept & 7-night trend'
    : (view==='means'  ? 'Mean hours slept per week'
    : (view==='medians'? 'Median hours slept per week'
    : (view==='mmeans' ? 'Mean hours slept per month'
    :                    'Median hours slept per month')));
  const clockWord = 'When you slept — ' + (
      view==='last7'  ? 'nightly clock time'
    : (view==='means' ? 'weekly mean clock time'
    : (view==='medians'?'weekly median clock time'
    : (view==='mmeans'? 'monthly mean clock time'
    :                   'monthly median clock time'))));
  document.getElementById('durTitle').textContent = durWord;
  document.getElementById('clockTitle').textContent = clockWord;
  renderDuration(v);
  renderClock(v);
}}
document.querySelectorAll('.tab').forEach(btn=>{{
  btn.addEventListener('click',()=>{{
    document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    showView(btn.dataset.view);
  }});
}});
showView('last7');

// ---- Archetype table ---------------------------------------------------- //
(function(){{
  const tbody=document.querySelector('#archetypeTable tbody');
  if(!A.table7.length){{
    tbody.innerHTML='<tr><td colspan="6" class="axis">No recent data.</td></tr>';
    return;
  }}
  const pill=(txt,bg,fg)=>
    '<span class="pill" style="background:'+bg+';color:'+fg+'">'+txt+'</span>';
  const compPill=(txt,bg,fg,bi,ei)=>
    '<span class="pill persona-open" role="button" tabindex="0" '
    + 'data-bi="'+bi+'" data-ei="'+ei+'" '
    + 'style="background:'+bg+';color:'+fg+'">'+txt+'</span>';
  A.table7.forEach(r=>{{
    const tr=document.createElement('tr');
    tr.innerHTML =
      '<td class="date">'+r.date+'</td>'+
      '<td class="time">'+r.begin+'</td>'+
      '<td class="time">'+r.end+'</td>'+
      '<td>'+pill(r.begin_type, r.begin_bg, r.begin_fg)+'</td>'+
      '<td>'+pill(r.end_type,   r.end_bg,   r.end_fg)+'</td>'+
      '<td>'+compPill(r.composite, r.comp_bg, r.comp_fg, r.bi, r.ei)+'</td>';
    tbody.appendChild(tr);
  }});
}})();

// ---- Decision support (Targeted Asleep Time) ---------------------------- //
(function(){{
  const cfg = A.tat_config;
  const PULL = [0.15, 0.30, 0.50];          // gentle / moderate / strong
  const PULL_LABEL = ['gentle', 'moderate', 'strong'];
  const slider = document.getElementById('dsSlider');
  const tl = document.getElementById('dsTimeline');
  const notesEl = document.getElementById('dsNotes');

  // Last up-to-7 nights, oldest→newest, on the minutes-since-noon frame.
  const last7 = A.series.slice(-7);
  const begins = last7.map(d => d.bed_min);
  const wakes  = last7.map(d => d.wake_min);

  function mean(a){{ return a.reduce((s,x)=>s+x,0)/a.length; }}
  // Recency-weighted average: newest night weighted most (a is oldest→newest,
  // so index i gets weight i+1: 1,2,3,…,n).
  function recencyWeighted(a){{
    let num=0, den=0;
    for(let i=0;i<a.length;i++){{ const w=i+1; num+=w*a[i]; den+=w; }}
    return den ? num/den : 0;
  }}
  // Least-squares slope of begin-time vs. day index (min per day).
  function slope(a){{
    const n=a.length; if(n<2) return 0;
    const xm=(n-1)/2, ym=mean(a);
    let num=0, den=0;
    for(let i=0;i<n;i++){{ num+=(i-xm)*(a[i]-ym); den+=(i-xm)*(i-xm); }}
    return den ? num/den : 0;
  }}

  function computeTAT(pull){{
    // Rule 2 — habit anchor: recency-weighted average of recent begin times
    // (last night counts most, tapering back over the window).
    const habit = recencyWeighted(begins);
    // Rule 3 — follow part of the day-over-day drift.
    const trend = cfg.trend_factor * slope(begins);
    // Rule 4 — earlier-than-usual wake today => earlier TAT (and vice versa).
    const wakeDev = wakes[wakes.length-1] - mean(wakes);
    const wake = cfg.wake_factor * wakeDev;
    let tat = habit + trend + wake;
    // Rule 5 — tilt toward Perfect Asleep Time by the slider fraction.
    tat = tat + pull*(cfg.pat - tat);
    // Rule 1 + clamp — keep within [floor, ceiling], round to 30 min.
    tat = Math.max(cfg.clamp_lo, Math.min(cfg.clamp_hi, tat));
    return {{ tat: Math.round(tat/30)*30, habit, trend, wake, wakeDev }};
  }}

  const STEPS = [
    {{ off:-90, title:'Step 1 — Start winding down',
       body:'Ambient lighting, a soothing beverage, no intense work.' }},
    {{ off:-60, title:'Step 2 — Begin night-time routines',
       body:'Brush teeth, wash up, and settle your space for the night.' }},
    {{ off:-30, title:'Step 3 — Ready for bed!',
       body:'Lights out and settle in. Sweet dreams!' }},
  ];

  function render(){{
    const pull = PULL[+slider.value];
    const r = computeTAT(pull);

    // Timeline (TAT itself is intentionally NOT shown).
    tl.innerHTML = STEPS.map(s => {{
      const t = r.tat + s.off;                        // minutes-since-noon
      const dot = todHexFromNoon(t);
      return '<div class="ds-step">'
        + '<div class="ds-time">'+clockFromNoon(t)+'</div>'
        + '<div><span class="ds-dot" style="background:'+dot+'"></span></div>'
        + '<div><div class="ds-steptitle">'+s.title+'</div>'
        + '<div class="ds-stepbody">'+s.body+'</div></div>'
        + '</div>';
    }}).join('');

    // Explanatory notes (right-hand side).
    const trendWord = Math.abs(r.trend) < 3 ? 'has been fairly steady'
      : (r.trend > 0 ? 'has been drifting later' : 'has been drifting earlier');
    const wakeWord = Math.abs(r.wakeDev) < 15 ? 'about your usual time'
      : (r.wakeDev < 0 ? 'earlier than usual' : 'later than usual');
    const wakeEffect = Math.abs(r.wakeDev) < 15 ? 'so it plays no real part today'
      : (r.wakeDev < 0
          ? 'so you may be tired sooner — nudging the plan a little earlier'
          : 'so sleep may come harder — nudging the plan a little later');
    const pat = clockFromNoon(cfg.pat);

    notesEl.innerHTML =
      '<h3>How these times were chosen</h3><ul>'
      + '<li>The plan is anchored to your <b>typical recent bedtime</b> '
        + '(a recency-weighted average of the last '+begins.length+' nights, '
        + 'so last night counts most and older nights taper off).</li>'
      + '<li>Your bedtime <b>'+trendWord+'</b> lately, which is taken into account '
        + '— chasing a sudden change rarely sticks.</li>'
      + '<li>You woke <b>'+wakeWord+'</b> today, '+wakeEffect+'.</li>'
      + '<li>The plan gently tilts toward an ideal of <b>'+pat+'</b>, at a '
        + '<b>'+PULL_LABEL[+slider.value]+'</b> level of ambition '
        + '(adjust with the slider above).</li>'
      + '<li>Each step is spaced to ease you in: wind-down, then routines '
        + '30 min later, then bed 30 min after that.</li>'
      + '</ul>';
  }}

  slider.addEventListener('input', render);
  render();
}})();

// ---- Histogram ---------------------------------------------------------- //
(function(){{
  const b=A.buckets, keys=Object.keys(b), vals=keys.map(k=>b[k]);
  const W=460,H=260,mL=34,mR=12,mT=12,mB=40;
  const iw=W-mL-mR, ih=H-mT-mB, max=Math.max(1,...vals);
  const svg=el('svg',{{viewBox:`0 0 ${{W}} ${{H}}`}});
  const bw=iw/keys.length*0.68, gap=iw/keys.length;
  keys.forEach((k,i)=>{{
    const h=vals[i]/max*ih, cx=mL+i*gap+gap/2;
    const good=(k==='7–8h'||k==='8–9h');
    svg.appendChild(el('rect',{{x:cx-bw/2,y:mT+ih-h,width:bw,height:h,rx:3,
      fill:good?css('--good'):css('--dawn2'),opacity:good?0.9:0.55}}));
    const val=el('text',{{x:cx,y:mT+ih-h-6,'text-anchor':'middle'}});
    val.setAttribute('class','axis'); val.textContent=vals[i]||''; svg.appendChild(val);
    const lab=el('text',{{x:cx,y:H-14,'text-anchor':'middle'}});
    lab.setAttribute('class','axis'); lab.textContent=k; svg.appendChild(lab);
  }});
  svg.appendChild(el('line',{{x1:mL,y1:mT+ih,x2:W-mR,y2:mT+ih,
    stroke:css('--line')}}));
  document.getElementById('hist').appendChild(svg);
}})();

// ---- Weekday chart ------------------------------------------------------ //
(function(){{
  const names=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], w=A.weekday_avg;
  const W=460,H=260,mL=34,mR=12,mT=12,mB=40;
  const iw=W-mL-mR, ih=H-mT-mB;
  const max=Math.max(10,...w.filter(v=>v!=null));
  const svg=el('svg',{{viewBox:`0 0 ${{W}} ${{H}}`}});
  const bw=iw/7*0.6, gap=iw/7;
  // target line at 8h
  const y8=mT+ih-(8/max)*ih;
  svg.appendChild(el('line',{{x1:mL,y1:y8,x2:W-mR,y2:y8,
    stroke:css('--good'),'stroke-dasharray':'4 4','stroke-width':1.5,opacity:.6}}));
  names.forEach((nm,i)=>{{
    const cx=mL+i*gap+gap/2, v=w[i];
    if(v!=null){{
      const h=v/max*ih;
      svg.appendChild(el('rect',{{x:cx-bw/2,y:mT+ih-h,width:bw,height:h,rx:3,
        fill:i>=5?css('--dawn3'):css('--dawn1'),opacity:.8}}));
      const val=el('text',{{x:cx,y:mT+ih-h-6,'text-anchor':'middle'}});
      val.setAttribute('class','axis'); val.textContent=v.toFixed(1); svg.appendChild(val);
    }}
    const lab=el('text',{{x:cx,y:H-14,'text-anchor':'middle'}});
    lab.setAttribute('class','axis'); lab.textContent=nm; svg.appendChild(lab);
  }});
  svg.appendChild(el('line',{{x1:mL,y1:mT+ih,x2:W-mR,y2:mT+ih,stroke:css('--line')}}));
  document.getElementById('weekday').appendChild(svg);
}})();

// ---- Theme (light/dark) ------------------------------------------------- //
(function(){{
  const root = document.documentElement;
  // Default by time of day: dark from 9PM to 6AM, light otherwise.
  const hr = new Date().getHours();
  const auto = (hr >= 21 || hr < 6) ? 'dark' : 'light';
  root.setAttribute('data-theme', auto);
  const btn = document.getElementById('themeToggle');
  function setPressed(){{
    btn.setAttribute('aria-pressed', root.getAttribute('data-theme')==='dark');
  }}
  setPressed();
  btn.addEventListener('click', () => {{
    root.setAttribute('data-theme',
      root.getAttribute('data-theme')==='dark' ? 'light' : 'dark');
    setPressed();
  }});
}})();

// ---- Sidebar scroll-spy ------------------------------------------------- //
(function(){{
  const links = Array.from(document.querySelectorAll('.side-nav a'));
  const byId = Object.fromEntries(links.map(a => [a.dataset.target, a]));
  const sections = links.map(a => document.getElementById(a.dataset.target))
                        .filter(Boolean);
  if(!sections.length) return;

  function setActive(id){{
    links.forEach(a => a.classList.toggle('active', a.dataset.target === id));
  }}

  // Track how much of each section is visible; highlight the most-visible one.
  const ratios = new Map();
  const obs = new IntersectionObserver((entries) => {{
    entries.forEach(e => ratios.set(e.target.id, e.intersectionRatio));
    let best = null, bestR = -1;
    sections.forEach(s => {{
      const r = ratios.get(s.id) || 0;
      if(r > bestR) {{ bestR = r; best = s.id; }}
    }});
    // If nothing is meaningfully visible (between sections), keep the topmost
    // section that has scrolled past the top of the viewport.
    if(bestR <= 0) {{
      for(const s of sections) {{
        if(s.getBoundingClientRect().top <= window.innerHeight * 0.3) best = s.id;
      }}
    }}
    if(best) setActive(best);
  }}, {{ threshold:[0,0.1,0.25,0.5,0.75,1], rootMargin:'-10% 0px -40% 0px' }});
  sections.forEach(s => obs.observe(s));

  // Smooth-scroll + immediate highlight on click.
  links.forEach(a => a.addEventListener('click', () => setActive(a.dataset.target)));
}})();

// ---- Colour-palette modal ----------------------------------------------- //
(function(){{
  const overlay = document.getElementById('paletteModal');
  const openBtn = document.getElementById('paletteOpen');
  const closeBtn = document.getElementById('paletteClose');
  const rows = document.getElementById('paletteRows');

  // Build one row per hour of the day using the shared time-of-day palette.
  let html='';
  for(let h=0; h<24; h++){{
    const hex = todHex(h*60).toUpperCase();
    const label = String(h).padStart(2,'0')+':00';
    html += '<tr>'
      + '<td class="pal-time">'+label+'</td>'
      + '<td><button class="swatch" style="background:'+hex+'" '
        + 'data-hex="'+hex+'" title="Copy '+hex+'" aria-label="Copy '+hex+'"></button></td>'
      + '<td><button class="hexbtn" data-hex="'+hex+'">'+hex+'</button></td>'
      + '</tr>';
  }}
  rows.innerHTML = html;

  function copyHex(hex, btn){{
    const done = () => {{
      if(btn.classList.contains('hexbtn')){{
        const orig = btn.textContent; btn.textContent='Copied!'; btn.classList.add('copied');
        setTimeout(()=>{{ btn.textContent=orig; btn.classList.remove('copied'); }}, 1100);
      }} else {{
        const hb = btn.closest('tr').querySelector('.hexbtn');
        if(hb){{ const o=hb.textContent; hb.textContent='Copied!'; hb.classList.add('copied');
          setTimeout(()=>{{ hb.textContent=o; hb.classList.remove('copied'); }},1100); }}
      }}
    }};
    if(navigator.clipboard && navigator.clipboard.writeText){{
      navigator.clipboard.writeText(hex).then(done).catch(()=>fallback(hex,done));
    }} else {{ fallback(hex, done); }}
  }}
  function fallback(text, done){{
    const ta=document.createElement('textarea'); ta.value=text;
    ta.style.position='fixed'; ta.style.opacity='0'; document.body.appendChild(ta);
    ta.select(); try{{ document.execCommand('copy'); }}catch(e){{}}
    document.body.removeChild(ta); done();
  }}
  rows.addEventListener('click', (e) => {{
    const b = e.target.closest('[data-hex]');
    if(b) copyHex(b.dataset.hex, b);
  }});

  function open(){{ overlay.hidden=false; document.body.style.overflow='hidden'; }}
  function close(){{ overlay.hidden=true; document.body.style.overflow=''; }}
  openBtn.addEventListener('click', open);
  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', (e) => {{ if(e.target===overlay) close(); }});
  document.addEventListener('keydown', (e) => {{ if(e.key==='Escape' && !overlay.hidden) close(); }});
}})();

// ---- Persona cards modal ------------------------------------------------ //
(function(){{
  const overlay = document.getElementById('personaModal');
  const head = document.getElementById('personaHead');
  const titleEl = document.getElementById('personaTitle');
  const tagsEl = document.getElementById('personaTags');
  const hoursEl = document.getElementById('personaHours');
  const detailEl = document.getElementById('personaDetail');
  const healthEl = document.getElementById('personaHealth');
  const closeBtn = document.getElementById('personaClose');

  function tag(txt, bg, fg, sub){{
    return '<span class="persona-tag" style="background:'+bg+';color:'+fg+'">'
      + txt + (sub ? '<small>'+sub+'</small>' : '') + '</span>';
  }}

  function openCard(bi, ei){{
    const c = (PERSONA_CARDS[bi]||[])[ei];
    if(!c) return;
    titleEl.textContent = c.name;
    document.getElementById('personaIcon').innerHTML = c.icon || '';
    // Tint the header with the persona's blended colour.
    head.style.background = c.bg;
    head.style.color = c.fg;
    // ensure the eyebrow + close inherit readable colour on the tint
    head.querySelectorAll('.persona-eyebrow, h2, .modal-close')
        .forEach(el => el.style.color = c.fg);
    tagsEl.innerHTML =
      tag(c.begin_label, c.begin_bg, c.begin_fg, c.begin_sub)
      + '<span class="persona-plus">+</span>'
      + tag(c.end_label, c.end_bg, c.end_fg, c.end_sub);
    hoursEl.textContent = c.hours;
    detailEl.textContent = c.detail;
    healthEl.textContent = c.health;
    overlay.hidden = false;
    document.body.style.overflow = 'hidden';
  }}
  function close(){{ overlay.hidden=true; document.body.style.overflow=''; }}

  // Delegate clicks/keys from any persona trigger (reference cells + composite pills).
  function handle(e){{
    const t = e.target.closest('.persona-open');
    if(!t) return;
    if(e.type==='keydown' && e.key!=='Enter' && e.key!==' ') return;
    if(e.type==='keydown') e.preventDefault();
    openCard(+t.dataset.bi, +t.dataset.ei);
  }}
  document.addEventListener('click', handle);
  document.addEventListener('keydown', handle);

  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', (e) => {{ if(e.target===overlay) close(); }});
  document.addEventListener('keydown', (e) => {{ if(e.key==='Escape' && !overlay.hidden) close(); }});
}})();
</script>
</body>
</html>"""
