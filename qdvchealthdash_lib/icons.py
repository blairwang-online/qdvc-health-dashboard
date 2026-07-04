"""Persona illustration icons.

Each icon is a filled-silhouette SVG drawn entirely in ``currentColor`` at
varying opacity, inside a faint medallion circle. Because they use
``currentColor`` (set to the card's auto-contrast text colour) and partial
opacity, they read on any tint — light or dark — and the underlying tint shows
through the translucent fills.

``PERSONA_ICONS`` is indexed [begin_bucket][end_bucket] to match the reference
grid and the table's bi/ei, so the icon lines up with each sleep persona.
"""

from __future__ import annotations

# Inner SVG content for a 0 0 100 100 viewBox (no outer <svg>, no colour except
# currentColor). Keyed by composite name for readability; mapped to the grid below.
_ICON_INNER = {
    "Rested Archer": """
  <path d="M32 20 A44 44 0 0 1 32 80" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" opacity="0.85"/>
  <line x1="32" y1="20" x2="32" y2="80" stroke="currentColor" stroke-width="2.5" opacity="0.6"/>
  <line x1="26" y1="50" x2="78" y2="50" stroke="currentColor" stroke-width="4" stroke-linecap="round" opacity="0.85"/>
  <polygon points="78,50 68,44 68,56" fill="currentColor" opacity="0.85"/>
  <path d="M26 50 l-6 -5 M26 50 l-6 5" stroke="currentColor" stroke-width="3" stroke-linecap="round" fill="none" opacity="0.7"/>
""",
    "Classic Warrior": """
  <path d="M50 18 L74 26 V50 C74 64 63 76 50 82 C37 76 26 64 26 50 V26 Z" fill="currentColor" opacity="0.30"/>
  <path d="M50 18 L74 26 V50 C74 64 63 76 50 82 C37 76 26 64 26 50 V26 Z" fill="none" stroke="currentColor" stroke-width="3" opacity="0.85"/>
  <line x1="50" y1="28" x2="50" y2="70" stroke="currentColor" stroke-width="5" stroke-linecap="round" opacity="0.9"/>
  <line x1="40" y1="40" x2="60" y2="40" stroke="currentColor" stroke-width="4" stroke-linecap="round" opacity="0.9"/>
""",
    "Besieged Defender": """
  <rect x="34" y="40" width="32" height="42" fill="currentColor" opacity="0.30"/>
  <rect x="34" y="40" width="32" height="42" fill="none" stroke="currentColor" stroke-width="3" opacity="0.85"/>
  <path d="M30 40 v-8 h6 v8 M47 40 v-8 h6 v8 M64 40 v-8 h6 v8" fill="currentColor" opacity="0.85"/>
  <rect x="30" y="34" width="40" height="6" fill="currentColor" opacity="0.85"/>
  <path d="M44 82 v-16 a6 6 0 0 1 12 0 v16 Z" fill="currentColor" opacity="0.6"/>
  <rect x="48" y="48" width="4" height="10" fill="currentColor" opacity="0.7"/>
""",
    "Stockholm Winter": """
  <path d="M72 26 l2.2 5.4 5.8 .5 -4.4 3.8 1.3 5.7 -4.9 -3.1 -4.9 3.1 1.3 -5.7 -4.4 -3.8 5.8 -.5 Z" fill="currentColor" opacity="0.55"/>
  <path d="M28 74 V58 c0 -6 3 -11 8 -14 l-3 -9 c-1 -3 1 -5 3 -3 l6 7 c3 -1 6 -1 9 0 l10 -2
           c3 -1 5 2 3 4 l-6 6 c2 4 3 8 3 13 v14 h-7 V62 h-2 v12 h-7 V62 c-3 1 -6 1 -9 0 v12 Z" fill="currentColor" opacity="0.85"/>
""",
    "Classic Commuter": """
  <rect x="30" y="24" width="40" height="46" rx="10" fill="currentColor" opacity="0.30"/>
  <rect x="30" y="24" width="40" height="46" rx="10" fill="none" stroke="currentColor" stroke-width="3" opacity="0.85"/>
  <rect x="37" y="32" width="26" height="14" rx="3" fill="currentColor" opacity="0.6"/>
  <circle cx="40" cy="58" r="3.5" fill="currentColor" opacity="0.85"/>
  <circle cx="60" cy="58" r="3.5" fill="currentColor" opacity="0.85"/>
  <line x1="38" y1="70" x2="33" y2="80" stroke="currentColor" stroke-width="4" stroke-linecap="round" opacity="0.85"/>
  <line x1="62" y1="70" x2="67" y2="80" stroke="currentColor" stroke-width="4" stroke-linecap="round" opacity="0.85"/>
""",
    "Madrid Summer": """
  <g stroke="currentColor" stroke-linecap="round" fill="none" opacity="0.9" stroke-width="3.2">
    <line x1="50" y1="50" x2="50" y2="30"/><line x1="50" y1="50" x2="64" y2="36"/>
    <line x1="50" y1="50" x2="70" y2="50"/><line x1="50" y1="50" x2="64" y2="64"/>
    <line x1="50" y1="50" x2="50" y2="70"/><line x1="50" y1="50" x2="36" y2="64"/>
    <line x1="50" y1="50" x2="30" y2="50"/><line x1="50" y1="50" x2="36" y2="36"/>
  </g>
  <circle cx="50" cy="50" r="3" fill="currentColor" opacity="0.9"/>
  <g stroke="currentColor" stroke-linecap="round" fill="none" opacity="0.55" stroke-width="2.4">
    <line x1="26" y1="28" x2="26" y2="18"/><line x1="26" y1="28" x2="33" y2="21"/>
    <line x1="26" y1="28" x2="19" y2="21"/><line x1="26" y1="28" x2="33" y2="35"/>
    <line x1="26" y1="28" x2="19" y2="35"/>
  </g>
  <g stroke="currentColor" stroke-linecap="round" fill="none" opacity="0.5" stroke-width="2.2">
    <line x1="76" y1="72" x2="76" y2="64"/><line x1="76" y1="72" x2="82" y2="66"/>
    <line x1="76" y1="72" x2="70" y2="66"/><line x1="76" y1="72" x2="82" y2="78"/>
    <line x1="76" y1="72" x2="70" y2="78"/>
  </g>
""",
    "Dreaming Kierkegaard": """
  <path d="M20 64 C30 58 44 58 50 62 C56 58 70 58 80 64 L80 40 C70 34 56 34 50 38
           C44 34 30 34 20 40 Z" fill="currentColor" opacity="0.30"/>
  <path d="M20 64 C30 58 44 58 50 62 C56 58 70 58 80 64 L80 40 C70 34 56 34 50 38
           C44 34 30 34 20 40 Z" fill="none" stroke="currentColor" stroke-width="3" opacity="0.85"/>
  <line x1="50" y1="38" x2="50" y2="62" stroke="currentColor" stroke-width="2.5" opacity="0.7"/>
  <text x="60" y="34" font-family="monospace" font-size="14" font-weight="700" fill="currentColor" opacity="0.85">z</text>
  <text x="70" y="26" font-family="monospace" font-size="11" font-weight="700" fill="currentColor" opacity="0.7">z</text>
  <text x="78" y="20" font-family="monospace" font-size="8"  font-weight="700" fill="currentColor" opacity="0.55">z</text>
""",
    "Classic Philosopher": """
  <path d="M50 20 C36 20 27 30 27 42 C27 51 33 56 37 62 C39 65 40 68 40 71 L60 71
           C60 68 61 65 63 62 C67 56 73 51 73 42 C73 30 64 20 50 20 Z" fill="currentColor" opacity="0.30"/>
  <path d="M50 20 C36 20 27 30 27 42 C27 51 33 56 37 62 C39 65 40 68 40 71 L60 71
           C60 68 61 65 63 62 C67 56 73 51 73 42 C73 30 64 20 50 20 Z" fill="none" stroke="currentColor" stroke-width="3" opacity="0.85"/>
  <path d="M44 40 l6 8 6 -8" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.7"/>
  <rect x="42" y="74" width="16" height="4" rx="2" fill="currentColor" opacity="0.85"/>
  <rect x="44" y="80" width="12" height="4" rx="2" fill="currentColor" opacity="0.7"/>
""",
    "Nocturnal Voltaire": """
  <ellipse cx="50" cy="56" rx="24" ry="26" fill="currentColor" opacity="0.30"/>
  <ellipse cx="50" cy="56" rx="24" ry="26" fill="none" stroke="currentColor" stroke-width="3" opacity="0.85"/>
  <path d="M32 34 l6 12 -12 -4 Z" fill="currentColor" opacity="0.85"/>
  <path d="M68 34 l-6 12 12 -4 Z" fill="currentColor" opacity="0.85"/>
  <circle cx="41" cy="50" r="8" fill="currentColor" opacity="0.6"/>
  <circle cx="59" cy="50" r="8" fill="currentColor" opacity="0.6"/>
  <circle cx="41" cy="50" r="3.5" fill="currentColor" opacity="0.95"/>
  <circle cx="59" cy="50" r="3.5" fill="currentColor" opacity="0.95"/>
  <path d="M50 56 l-4 6 8 0 Z" fill="currentColor" opacity="0.9"/>
  <path d="M44 82 v4 M50 82 v5 M56 82 v4" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" opacity="0.7"/>
""",
}


def persona_icon_svg(name: str, cls: str = "persona-icon") -> str:
    """Return a complete <svg> for a persona, drawn in currentColor with a faint
    medallion backdrop. Returns empty string if the name is unknown."""
    inner = _ICON_INNER.get(name)
    if inner is None:
        return ""
    return (
        f'<svg class="{cls}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" '
        f'aria-hidden="true">'
        f'<circle cx="50" cy="50" r="48" fill="currentColor" opacity="0.12"/>'
        f'{inner}</svg>'
    )
