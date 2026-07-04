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
  <path d="M56 22 L78 29 V50 C78 63 68 74 56 79 C44 74 34 63 34 50 V29 Z" fill="currentColor" opacity="0.28"/>
  <path d="M56 22 L78 29 V50 C78 63 68 74 56 79 C44 74 34 63 34 50 V29 Z" fill="none" stroke="currentColor" stroke-width="3" opacity="0.8"/>
  <g opacity="0.9">
    <path d="M24 78 L30 72 L60 30 L64 26 L66 34 L34 76 Z" fill="currentColor"/>
    <line x1="26" y1="66" x2="40" y2="80" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
    <line x1="24" y1="78" x2="18" y2="84" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
    <circle cx="16" cy="86" r="3.5" fill="currentColor"/>
  </g>
""",
    "Besieged Defender": """
  <g opacity="0.85">
    <rect x="24" y="52" width="52" height="30" fill="currentColor" opacity="0.30"/>
    <rect x="24" y="52" width="52" height="30" fill="none" stroke="currentColor" stroke-width="3"/>
    <rect x="20" y="42" width="16" height="40" fill="currentColor" opacity="0.30"/>
    <rect x="20" y="42" width="16" height="40" fill="none" stroke="currentColor" stroke-width="3"/>
    <rect x="64" y="42" width="16" height="40" fill="currentColor" opacity="0.30"/>
    <rect x="64" y="42" width="16" height="40" fill="none" stroke="currentColor" stroke-width="3"/>
    <path d="M20 42 h4 v-5 h4 v5 h4 v-5 h4 v5" fill="currentColor"/>
    <path d="M64 42 h4 v-5 h4 v5 h4 v-5 h4 v5" fill="currentColor"/>
    <path d="M30 52 v-5 h5 v5 M43 52 v-6 h6 v6 M57 52 v-5 h5 v5" fill="currentColor"/>
  </g>
  <path d="M44 82 v-14 a6 6 0 0 1 12 0 v14 Z" fill="currentColor" opacity="0.65"/>
""",
    "Stockholm Winter": """
  <g stroke="currentColor" stroke-linecap="round" fill="none">
    <g opacity="0.9" stroke-width="3" transform="translate(46,46)">
      <g id="fl"><line x1="0" y1="0" x2="0" y2="-22"/><line x1="0" y1="-14" x2="-6" y2="-20"/><line x1="0" y1="-14" x2="6" y2="-20"/></g>
      <use href="#fl" transform="rotate(60)"/><use href="#fl" transform="rotate(120)"/>
      <use href="#fl" transform="rotate(180)"/><use href="#fl" transform="rotate(240)"/><use href="#fl" transform="rotate(300)"/>
    </g>
    <g opacity="0.6" stroke-width="2.2" transform="translate(76,26)">
      <g id="fs"><line x1="0" y1="0" x2="0" y2="-11"/><line x1="0" y1="-7" x2="-4" y2="-11"/><line x1="0" y1="-7" x2="4" y2="-11"/></g>
      <use href="#fs" transform="rotate(60)"/><use href="#fs" transform="rotate(120)"/>
      <use href="#fs" transform="rotate(180)"/><use href="#fs" transform="rotate(240)"/><use href="#fs" transform="rotate(300)"/>
    </g>
    <g opacity="0.5" stroke-width="2" transform="translate(24,74)">
      <g id="ft"><line x1="0" y1="0" x2="0" y2="-9"/><line x1="0" y1="-6" x2="-3" y2="-9"/><line x1="0" y1="-6" x2="3" y2="-9"/></g>
      <use href="#ft" transform="rotate(60)"/><use href="#ft" transform="rotate(120)"/>
      <use href="#ft" transform="rotate(180)"/><use href="#ft" transform="rotate(240)"/><use href="#ft" transform="rotate(300)"/>
    </g>
  </g>
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
  <path d="M18 82 L44 56 L52 64 Z" fill="currentColor" opacity="0.5"/>
  <path d="M18 82 L44 56 L52 64 Z" fill="none" stroke="currentColor" stroke-width="2.5" opacity="0.85"/>
  <line x1="41" y1="53" x2="55" y2="67" stroke="currentColor" stroke-width="3" stroke-linecap="round" opacity="0.85"/>
  <g stroke="currentColor" fill="none" stroke-linecap="round" opacity="0.85">
    <path d="M52 60 q10 -14 24 -14" stroke-width="2.6"/>
    <path d="M50 56 q6 -18 14 -26" stroke-width="2.6"/>
    <path d="M54 62 q16 -6 26 2" stroke-width="2.6"/>
  </g>
  <g fill="currentColor" opacity="0.8">
    <rect x="72" y="42" width="5" height="5" rx="1" transform="rotate(20 74 44)"/>
    <rect x="62" y="26" width="5" height="5" rx="1" transform="rotate(-15 64 28)"/>
    <rect x="80" y="50" width="4.5" height="4.5" rx="1" transform="rotate(35 82 52)"/>
    <circle cx="58" cy="34" r="2.4"/><circle cx="78" cy="34" r="2.4"/><circle cx="68" cy="48" r="2.2"/>
  </g>
""",
    "Dreaming Kierkegaard": """
  <g opacity="0.85">
    <path d="M18 68 C28 62 42 62 48 66 L48 72 C42 68 28 68 18 74 Z" fill="currentColor" opacity="0.5"/>
    <path d="M52 66 C58 62 72 62 82 68 L82 74 C72 68 58 68 52 72 Z" fill="currentColor" opacity="0.5"/>
    <path d="M18 68 C28 60 42 60 48 65 L48 40 C42 35 28 35 18 43 Z" fill="currentColor" opacity="0.30"/>
    <path d="M52 65 C58 60 72 60 82 68 L82 43 C72 35 58 35 52 40 Z" fill="currentColor" opacity="0.30"/>
    <path d="M18 68 C28 60 42 60 48 65 C52 60 66 60 82 68 L82 43 C66 35 52 35 48 40 C42 35 28 35 18 43 Z"
          fill="none" stroke="currentColor" stroke-width="3"/>
    <line x1="48" y1="40" x2="48" y2="65" stroke="currentColor" stroke-width="2.5" opacity="0.7"/>
  </g>
  <text x="58" y="34" font-family="monospace" font-size="20" font-weight="700" fill="currentColor" opacity="0.9">z</text>
  <text x="71" y="24" font-family="monospace" font-size="15" font-weight="700" fill="currentColor" opacity="0.72">z</text>
  <text x="81" y="16" font-family="monospace" font-size="11" font-weight="700" fill="currentColor" opacity="0.55">z</text>
""",
    "Classic Philosopher": """
  <g stroke="currentColor" stroke-width="3" stroke-linecap="round" opacity="0.7">
    <line x1="50" y1="10" x2="50" y2="18"/>
    <line x1="22" y1="20" x2="27" y2="26"/>
    <line x1="78" y1="20" x2="73" y2="26"/>
    <line x1="14" y1="44" x2="22" y2="44"/>
    <line x1="86" y1="44" x2="78" y2="44"/>
  </g>
  <path d="M50 18 C37 18 28 27 28 39 C28 48 34 53 38 59 C40 62 41 65 41 68 L59 68
           C59 65 60 62 62 59 C66 53 72 48 72 39 C72 27 63 18 50 18 Z" fill="currentColor" opacity="0.30"/>
  <path d="M50 18 C37 18 28 27 28 39 C28 48 34 53 38 59 C40 62 41 65 41 68 L59 68
           C59 65 60 62 62 59 C66 53 72 48 72 39 C72 27 63 18 50 18 Z" fill="none" stroke="currentColor" stroke-width="3" opacity="0.85"/>
  <path d="M44 38 l6 8 6 -8" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.7"/>
  <rect x="42" y="71" width="16" height="4" rx="2" fill="currentColor" opacity="0.85"/>
  <rect x="44" y="77" width="12" height="4" rx="2" fill="currentColor" opacity="0.7"/>
""",
    "Nocturnal Voltaire": """
  <path d="M74 12 A16 16 0 1 0 90 34 A12 12 0 1 1 74 12 Z" fill="currentColor" opacity="0.55" fill-rule="evenodd"/>
  <path d="M34 34 L38 24 L43 33 C46 31 54 31 57 33 L62 24 L66 34
           C71 39 73 47 73 55 C73 70 63 82 50 82 C37 82 27 70 27 55
           C27 47 29 39 34 34 Z"
        fill="none" stroke="currentColor" stroke-width="3.4" stroke-linejoin="round" opacity="0.92"/>
  <path d="M33 49 C40 43 60 43 67 49" fill="none" stroke="currentColor" stroke-width="2.4" opacity="0.55"/>
  <path d="M36 52 C26 56 20 66 20 74 C26 70 31 68 37 68"
        fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity="0.7"/>
  <path d="M64 52 C74 56 80 66 80 74 C74 70 69 68 63 68"
        fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity="0.7"/>
  <path d="M50 55 v21" stroke="currentColor" stroke-width="1.6" opacity="0.3"/>
  <line x1="24" y1="84" x2="76" y2="84" stroke="currentColor" stroke-width="3" stroke-linecap="round" opacity="0.6"/>
  <path d="M44 82 v3 M44 85 l-3 2 M44 85 l3 2 M56 82 v3 M56 85 l-3 2 M56 85 l3 2"
        fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" opacity="0.7"/>
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
