"""qdvchealthdash_lib — sleep-health dashboard generator.

Public API:
    load_nights(path) -> (nights, warnings)   read & parse the CSV
    analyse(nights)   -> dict                  compute all metrics
    render_html(analysis, warnings, source) -> str   build the HTML page

Modules:
    config      tunable labels, thresholds, composite names/blurbs, font
    colors      time-of-day colour palette shared across the whole dashboard
    data        Night model, CSV parsing, low-level time helpers
    archetypes  bedtime/wake classification and composite lookup
    analysis    weekly aggregation and the main analyse()
    render      composite reference grid and full HTML page
"""

from __future__ import annotations

from .data import Night, load_nights
from .analysis import analyse
from .render import render_html

__all__ = ["Night", "load_nights", "analyse", "render_html"]
