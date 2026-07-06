"""Asset loading.

The dashboard's static front-end material lives as plain files under
``qdvchealthdash_lib/assets/`` rather than embedded in the Python source, so it
can be edited with normal tooling (syntax highlighting, linters, formatters):

    assets/css/*.css   the stylesheet, split into logical components
    assets/js/*.js     the page script, split into logical components
    assets/icons/*.svg one persona silhouette per file

``load_css()`` / ``load_js()`` concatenate their component files **in the fixed
order defined below** and return one text blob each; ``render`` inlines those
blobs into the single output HTML. So the "one self-contained offline file, no
build step" guarantee is unchanged — nothing is fetched at runtime by the
generated page, and the CSS cascade / JS execution order is deterministic.

Order matters:
  * CSS is ordered by the cascade (tokens first, then broad layout, then
    components); later files may override earlier ones.
  * JS shares a single script scope, so files must load in dependency order:
    data first, then shared helpers, then the features that use them.
To add a component, create the file and add it to the relevant manifest.

Files are read through ``importlib.resources`` so it works whether the package is
run in place or installed. Results are cached: assets don't change during a run.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources

from jinja2 import Environment, FunctionLoader, select_autoescape

# CSS components, in cascade order (earlier = lower specificity baseline).
_CSS_FILES = (
    "tokens.css",            # :root custom properties + dark-theme overrides
    "base.css",              # body, page shell, main column
    "sidebar.css",           # right sidebar: nav + theme toggle
    "palette-modal.css",     # colour-palette modal + swatches
    "persona.css",           # persona cards, icons, persona modal
    "hero.css",              # header, score arc, stat grid
    "panel-tabs.css",        # .panel + tab bar (incl. dark overrides)
    "charts.css",            # chart layout + punctuality legend
    "decision-support.css",  # Targeted-Asleep-Time timeline + notes
    "reference-table.css",   # archetype/reference tables, axes, pills
    "misc.css",              # warnings, footer, responsive, motion
)

# JS components, in execution order. Shared scope, so dependencies come first:
# data -> helpers -> chart builders -> tab wiring -> self-contained features.
_JS_FILES = (
    "data.js",               # parse the JSON script tags; animate the score arc
    "helpers.js",            # SVG/DOM + clock/colour helpers; buildView
    "chart-duration.js",     # renderDuration
    "chart-clock.js",        # renderClock
    "timing-tabs.js",        # showView + timing tab wiring
    "punctuality.js",        # bedtime-punctuality chart + its tabs
    "archetype-table.js",    # per-night archetype table
    "decision-support.js",   # TAT slider + wind-down timeline
    "histogram.js",          # bedtime histogram
    "weekday.js",            # weekday averages chart
    "theme.js",              # light/dark toggle + default-by-hour
    "scroll-spy.js",         # sidebar active-section highlighting
    "palette-modal.js",      # colour-palette modal behaviour
    "persona-modal.js",      # persona-card modal behaviour
)


@lru_cache(maxsize=None)
def load_text(*parts: str) -> str:
    """Return the text of an asset file under ``qdvchealthdash_lib/assets``.

    ``parts`` is the path below ``assets`` (e.g. ``"css", "base.css"`` or
    ``"icons", "rested-archer.svg"``). Reads as UTF-8.
    """
    res = resources.files(__package__).joinpath("assets", *parts)
    return res.read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def _concat(subdir: str, names: tuple[str, ...]) -> str:
    """Concatenate the named files in ``assets/<subdir>`` in the given order.

    Each component file stores its section verbatim (including any blank lines
    that separated it from the next) plus one trailing newline; joining the
    files with a newline after removing that single trailing newline reproduces
    the original single-file layout exactly.
    """
    chunks = []
    for name in names:
        text = load_text(subdir, name)
        chunks.append(text[:-1] if text.endswith("\n") else text)
    return "\n".join(chunks)


def load_css() -> str:
    """The full stylesheet: the CSS components joined in cascade order.
    Contains the ``__FONT_STACK__`` placeholder for the caller to fill."""
    return _concat("css", _CSS_FILES)


def load_js() -> str:
    """The full page script: the JS components joined in execution order.
    Fully static — it reads its data from the page's
    ``<script type="application/json">`` blocks."""
    return _concat("js", _JS_FILES)


# --------------------------------------------------------------------------- #
# HTML templating (Jinja2)
# --------------------------------------------------------------------------- #
# Templates live under assets/templates/*.html.jinja and are loaded through the
# same importlib.resources path as every other asset (so it works in place or
# installed). Autoescaping is ON: data values are escaped by default, and the
# few trusted-HTML fragments (inlined CSS/JS, the pre-built reference table, the
# persona SVGs, the pill style= attributes, the JSON script-tag bodies) are
# marked ``| safe`` in the templates. The environment is built once and cached.

@lru_cache(maxsize=None)
def _jinja_env() -> Environment:
    env = Environment(
        loader=FunctionLoader(lambda name: load_text("templates", name)),
        autoescape=select_autoescape(
            enabled_extensions=("jinja", "html"), default=True
        ),
        # Trim the newline after a block tag and strip leading block whitespace,
        # so ``{% ... %}`` control lines don't inject blank lines into the output.
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=False,
    )
    return env


def get_template(name: str):
    """Return the compiled Jinja template ``assets/templates/<name>``."""
    return _jinja_env().get_template(name)


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
