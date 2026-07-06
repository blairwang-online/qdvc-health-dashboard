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
from .assets import load_css, load_js, load_mobile_css, load_mobile_js, get_template


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


def _reference_grid() -> dict:
    """Structured data for the composite-archetype reference grid, consumed by
    ``templates/reference_table.html.jinja``. Rows are begin buckets, columns
    are end buckets; each cell blends the two spectrum colours. Trusted-HTML
    fields (``style``, ``icon``) are rendered ``| safe`` in the template; text
    fields are autoescaped there.

    Returns ``{"end_heads": [...], "rows": [{..., "cells": [...]}, ...]}``.
    """
    end_labels = [e[1] for e in END_ARCHETYPES]
    begin_labels = [b[1] for b in BEGIN_ARCHETYPES]
    end_heads = [
        {"label": lbl, "sub": sub, "style": _pill_style(_END_BG[ei])}
        for ei, (lbl, sub) in enumerate(zip(end_labels, END_SUBTITLES))
    ]
    rows = []
    for bi, begin_lbl in enumerate(begin_labels):
        cells = []
        for ei in range(len(END_ARCHETYPES)):
            bg = _mix_hex(_BEGIN_BG[bi], _END_BG[ei])
            cells.append({
                "bi": bi, "ei": ei,
                "style": _pill_style(bg),
                "icon": persona_icon_svg(
                    COMPOSITE_ARCHETYPES[bi][ei], cls="persona-icon ref-icon"),
                "name": COMPOSITE_ARCHETYPES[bi][ei],
                "hours": _sleep_hours_range(bi, ei),
                "blurb": COMPOSITE_BLURBS[bi][ei],
            })
        rows.append({
            "label": begin_lbl, "sub": BEGIN_SUBTITLES[bi],
            "style": _pill_style(_BEGIN_BG[bi]), "cells": cells,
        })
    return {"end_heads": end_heads, "rows": rows}


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


def _warn_html(warnings: list[str]) -> str:
    """The optional data-notes ``<details>`` block (empty string if no warnings).
    Built here rather than in the template because the item list is capped and
    the markup is trivial; the result is injected via ``| safe``. Warning text is
    HTML-escaped, since it can contain values echoed from the input file."""
    if not warnings:
        return ""
    items = "".join(f"<li>{html.escape(w)}</li>" for w in warnings[:12])
    more = "" if len(warnings) <= 12 else f"<li>\u2026 and {len(warnings) - 12} more</li>"
    return (f'<details class="warn"><summary>{len(warnings)} data note(s)</summary>'
            f'<ul>{items}{more}</ul></details>')


def _verdict(score: int) -> str:
    return (
        "Well rested" if score >= 80 else
        "On track" if score >= 65 else
        "Room to improve" if score >= 50 else
        "Needs attention"
    )


def render_html(a: dict, warnings: list[str], source: str) -> str:
    """Render the full single-file dashboard page via the Jinja template.

    Autoescaping is on (see assets._jinja_env): plain data values in the context
    are HTML-escaped automatically, so only trusted-HTML fragments are marked
    ``| safe`` in the templates. The three inlined blobs (CSS, JS, reference
    table) and the two JSON script-tag bodies are such fragments.
    """
    # Static front-end assets, inlined at generate time. The CSS carries one
    # Python value (the font stack) via a __PLACEHOLDER__ token; the JS is fully
    # static (it reads its data from the JSON script tags below).
    styles = load_css().replace("__FONT_STACK__", FONT_STACK).rstrip("\n")
    scripts = load_js().rstrip("\n")

    # The reference grid is templated from structured data (see _reference_grid).
    reference_table = get_template("reference_table.html.jinja").render(
        grid=_reference_grid()
    )

    context = {
        "a": a,
        "score": a["score"],
        "verdict": _verdict(a["score"]),
        # Pre-formatted overview values (kept out of the template for clarity).
        "avg_hm": _fmt_hm(a["avg"]),
        "median_hm": _fmt_hm(a["median"]),
        "bed_swing": f"{a['bed_sd_min'] / 60:.1f}",
        "wake_swing": f"{a['wake_sd_min'] / 60:.1f}",
        "pct_7_9": round(100 * a["nights_7_9"] / a["recorded"]),
        "styles": styles,
        "scripts": scripts,
        "reference_table": reference_table,
        "warn_html": _warn_html(warnings),
        "source": source,
        # Payloads for the two <script type="application/json"> blocks the page's
        # JS reads on load. Escaped for safe embedding (see _json_for_script) and
        # marked | safe in the template so autoescaping leaves the JSON intact.
        "data_json": _json_for_script(a),
        "persona_cards_json": _json_for_script(_persona_cards()),
    }
    return get_template("page.html.jinja").render(context)


def render_mobile_html(a: dict, warnings: list[str], source: str) -> str:
    """Render the mobile companion page via ``page_mobile.html.jinja``.

    The mobile page is a deliberately reduced summary (not feature parity with
    the desktop dashboard): a compact score chip, a slider-free "moderate"
    Decision-support plan, the when-you-slept clock chart (Last 7 / weekly /
    monthly means), weekly/monthly bedtime-punctuality benchmarks, and the
    past-7-nights persona list with the reference grid parked in a modal. It
    reuses the same analysis dict, the same time-of-day palette, and the shared
    persona-card modal, so branding stays identical to the desktop build; only
    the CSS/JS bundles and the template differ (see assets._MOBILE_* manifests).
    Autoescaping and the ``| safe`` rules are exactly as in ``render_html``.
    """
    styles = load_mobile_css().replace("__FONT_STACK__", FONT_STACK).rstrip("\n")
    scripts = load_mobile_js().rstrip("\n")

    reference_table = get_template("reference_table.html.jinja").render(
        grid=_reference_grid()
    )

    context = {
        "a": a,
        "score": a["score"],
        "verdict": _verdict(a["score"]),
        "styles": styles,
        "scripts": scripts,
        "reference_table": reference_table,
        "warn_html": _warn_html(warnings),
        "source": source,
        "data_json": _json_for_script(a),
        "persona_cards_json": _json_for_script(_persona_cards()),
    }
    return get_template("page_mobile.html.jinja").render(context)
