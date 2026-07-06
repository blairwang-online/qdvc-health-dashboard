"""Asset loading.

The dashboard's static front-end material (CSS, JS, and the persona SVG icons)
lives as plain files under ``qdvchealthdash_lib/assets/`` rather than embedded in
the Python source, so it can be edited with normal tooling (syntax highlighting,
linters, formatters). These helpers read those files **at generate time** and the
callers inline the text into the single output HTML — so the "one self-contained
offline file, no build step" guarantee is unchanged; nothing is fetched at
runtime by the generated page.

Files are read through ``importlib.resources`` so it works whether the package is
run in place or installed. Results are cached: assets don't change during a run.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources


@lru_cache(maxsize=None)
def load_text(*parts: str) -> str:
    """Return the text of an asset file under ``qdvchealthdash_lib/assets``.

    ``parts`` is the path below ``assets`` (e.g. ``"dashboard.css"`` or
    ``"icons", "rested-archer.svg"``). Reads as UTF-8.
    """
    res = resources.files(__package__).joinpath("assets", *parts)
    return res.read_text(encoding="utf-8")


def load_css() -> str:
    """The dashboard stylesheet (contains the ``__FONT_STACK__`` placeholder)."""
    return load_text("dashboard.css")


def load_js() -> str:
    """The dashboard script (contains ``__DATA_JSON__`` and
    ``__PERSONA_CARDS_JSON__`` placeholders)."""
    return load_text("dashboard.js")


def load_icon_inner(slug: str) -> str:
    """The inner markup of a persona icon SVG (everything between the outer
    ``<svg>`` tags), so callers can re-wrap it with a chosen ``class``.
    Returns an empty string if the asset is missing."""
    try:
        raw = load_text("icons", f"{slug}.svg")
    except (FileNotFoundError, ModuleNotFoundError):
        return ""
    # Strip the outer <svg …> … </svg> wrapper, keeping the inner content
    # (the medallion circle + silhouette). The wrapper is re-added by the
    # caller with the appropriate CSS class.
    open_end = raw.find(">")
    close_start = raw.rfind("</svg>")
    if open_end == -1 or close_start == -1:
        return ""
    # Drop the whitespace between the outer <svg …> and the first inner element
    # (a formatting artefact of the standalone file) so the re-wrapped markup is
    # byte-identical to the historically inlined form.
    return raw[open_end + 1:close_start].lstrip()
