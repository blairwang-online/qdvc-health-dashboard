"""Persona illustration icons.

Each icon is a filled-silhouette SVG drawn entirely in ``currentColor`` at
varying opacity, inside a faint medallion circle. Because they use
``currentColor`` (set to the card's auto-contrast text colour) and partial
opacity, they read on any tint — light or dark — and the underlying tint shows
through the translucent fills.

The SVG markup itself lives as individual files under ``assets/icons/`` (one per
persona, named by a slug of the persona name); this module only maps persona
names to those files and wraps the loaded markup for use on a card. Keep the
``0 0 100 100`` viewBox and the ``currentColor``-only rule for any new icon.
"""

from __future__ import annotations

from .assets import load_icon_inner


def _slug(name: str) -> str:
    """Map a persona name to its icon filename stem (see assets/icons/)."""
    return name.lower().replace(" ", "-")


def persona_icon_svg(name: str, cls: str = "persona-icon") -> str:
    """Return a complete <svg> for a persona, drawn in currentColor with a faint
    medallion backdrop. Returns empty string if the name is unknown."""
    inner = load_icon_inner(_slug(name))
    if not inner:
        return ""
    return (
        f'<svg class="{cls}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" '
        f'aria-hidden="true">{inner}</svg>'
    )
