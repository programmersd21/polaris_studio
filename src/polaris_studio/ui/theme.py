"""Central design system for Polaris Studio.

Provides:
- Font loading from bundled .ttf files
- Color tokens, spacing tokens, radii, typography scales
- A QApplication font setup helper
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Optional

from PySide6.QtGui import QFont, QFontDatabase


FONT_FILES = {
    "inter": "Inter-Regular.ttf",
    "outfit": "Outfit-Regular.ttf",
    "instrumentserif": "InstrumentSerif-Regular.ttf",
    "jetbrainsmono": "JetBrainsMono-Regular.ttf",
}

FONT_DIR_CANDIDATES = [
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "fonts"
    ),
    os.path.join(os.getcwd(), "fonts"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "fonts"),
]


def _locate_font_dir() -> str:
    for candidate in FONT_DIR_CANDIDATES:
        if os.path.isdir(candidate):
            return candidate
    return ""


def _safe_point_size(point_size: int) -> int:
    return max(1, int(point_size))


def _patch_inter_family_name(path: str) -> None:
    """Rewrite Inter's family name to 'Inter' if it ships as 'Inter 18pt'.

    The Inter distribution at fonts/Inter-Regular.ttf is a multi-weight
    variable font with optical sizes baked in. Its internal family name is
    'Inter 18pt', which makes ``QFont('Inter')`` and QSS
    ``font-family: 'Inter'`` fall back to the system font. We rewrite the
    name table once so the family resolves as 'Inter'.
    """
    if not os.path.exists(path):
        return
    try:
        from fontTools.ttLib import TTFont  # type: ignore[import-untyped]
    except Exception:
        return
    try:
        font = TTFont(path)
    except Exception:
        return
    changed = False
    for record in font["name"].names:
        if record.nameID not in (1, 4, 16, 21):
            continue
        try:
            current = record.toUnicode()
        except Exception:
            current = ""
        if "Inter" in current and current != "Inter":
            try:
                if record.platformID == 3:
                    record.string = "Inter"
                elif record.platformID == 1:
                    record.string = b"Inter"
                else:
                    record.string = "Inter"
                changed = True
            except Exception:
                pass
    if changed:
        try:
            font.save(path)
        except Exception:
            return


def _resolve_inter_family() -> str:
    """Return the family name under which Inter is actually registered.

    The TTF we ship has been patched to 'Inter', but if a user re-downloads
    the upstream file it registers as 'Inter 18pt'. We search for any
    family starting with 'Inter' so both cases resolve.
    """
    for family in QFontDatabase.families():
        if family == "Inter" or family.startswith("Inter "):
            return family
    return "Inter"


@dataclass(frozen=True)
class Palette:
    bg_app: str = "#f6f7fb"
    bg_panel: str = "#ffffff"
    bg_canvas: str = "#f3f6fb"
    bg_node: str = "#ffffff"
    bg_node_alt: str = "#f8fafc"
    bg_node_header: str = "#edf2f8"
    border: str = "#dfe4ee"
    border_strong: str = "#aebbd0"
    text_primary: str = "#172033"
    text_secondary: str = "#526071"
    text_muted: str = "#8b96a8"
    accent: str = "#245bdb"
    accent_hover: str = "#1d4ec3"
    accent_dim: str = "#e7efff"
    success: str = "#16835f"
    warning: str = "#c27b12"
    error: str = "#c9363f"
    running: str = "#0a7bb8"
    edge: str = "#7b879d"
    edge_hover: str = "#245bdb"
    edge_selected: str = "#123d9a"
    port: str = "#607089"
    port_hover: str = "#245bdb"
    selection_box: str = "#245bdb"
    selection_box_fill: str = "#1f245bdb"
    grid_dot: str = "#d8e0ed"
    grid_dot_strong: str = "#b7c4d6"

    cat_source: str = "#bddfce"
    cat_transform: str = "#c8d6ee"
    cat_filter: str = "#d9cced"
    cat_aggregate: str = "#ead9b8"
    cat_join: str = "#b8dce0"
    cat_sort: str = "#cbd7e8"
    cat_chart: str = "#cfc5e6"
    cat_output: str = "#e5cbb7"


PALETTE = Palette()


@dataclass(frozen=True)
class Spacing:
    xxs: int = 2
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 32


SPACING = Spacing()


@dataclass(frozen=True)
class Radii:
    sm: int = 4
    md: int = 8
    lg: int = 12
    xl: int = 16


RADII = Radii()


@dataclass(frozen=True)
class Typography:
    display: int = 32
    title: int = 12
    body: int = 11
    caption: int = 10
    micro: int = 9
    code: int = 10


TYPO = Typography()


@lru_cache(maxsize=1)
def load_fonts() -> Dict[str, str]:
    """Load the four bundled UI fonts and return logical name -> registered family."""
    font_dir = _locate_font_dir()
    if not font_dir:
        return {}

    mapping: Dict[str, str] = {}
    for key, filename in FONT_FILES.items():
        path = os.path.join(font_dir, filename)
        if not os.path.exists(path):
            continue
        if key == "inter":
            _patch_inter_family_name(path)
        font_id = QFontDatabase.addApplicationFont(path)
        if font_id == -1:
            continue
        families = QFontDatabase.applicationFontFamilies(font_id)
        if not families:
            continue
        if key == "inter":
            mapping[key] = _resolve_inter_family()
        else:
            mapping[key] = families[0]
    return mapping


def font_outfit(
    point_size: int = TYPO.title, weight: QFont.Weight = QFont.Weight.DemiBold
) -> QFont:
    families = load_fonts()
    f = QFont(families.get("outfit", "Outfit"))
    f.setPointSize(_safe_point_size(point_size))
    f.setWeight(weight)
    f.setStyleStrategy(QFont.StyleStrategy.PreferQuality)
    return f


def font_inter(point_size: int = TYPO.body, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    families = load_fonts()
    f = QFont(families.get("inter", "Inter"))
    f.setPointSize(_safe_point_size(point_size))
    f.setWeight(weight)
    f.setStyleStrategy(QFont.StyleStrategy.PreferQuality)
    return f


def font_instrument_serif(point_size: int = 14) -> QFont:
    families = load_fonts()
    f = QFont(families.get("instrumentserif", families.get("instrument", "Instrument Serif")))
    f.setPointSize(_safe_point_size(point_size))
    f.setStyleName("Regular")
    f.setStyleStrategy(QFont.StyleStrategy.PreferQuality)
    return f


def font_mono(point_size: int = TYPO.code, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    families = load_fonts()
    f = QFont(families.get("jetbrainsmono", "JetBrains Mono"))
    f.setPointSize(_safe_point_size(point_size))
    f.setWeight(weight)
    f.setStyleStrategy(QFont.StyleStrategy.PreferQuality)
    return f


def category_color(category: str) -> str:
    pal = PALETTE
    return {
        "Source": pal.cat_source,
        "Transform": pal.cat_transform,
        "Filter": pal.cat_filter,
        "Aggregate": pal.cat_aggregate,
        "Join": pal.cat_join,
        "Sort": pal.cat_sort,
        "Chart": pal.cat_chart,
        "Output": pal.cat_output,
    }.get(category, pal.cat_transform)


def apply_application_font(app) -> None:
    """Apply the default UI font to the application."""
    families = load_fonts()
    base_family = families.get("inter", "Inter")
    font = QFont(base_family)
    font.setPointSize(_safe_point_size(TYPO.body))
    font.setStyleStrategy(QFont.StyleStrategy.PreferQuality)
    app.setFont(font)


def asset_path(*parts: str) -> Optional[str]:
    base = _locate_font_dir()
    if not base:
        return None
    return os.path.join(base, *parts)
