from __future__ import annotations

from pathlib import Path


def test_app_uses_visual_only_commercial_tab_styles_without_new_navigation() -> None:
    source = Path("app.py").read_text(encoding="utf-8")

    assert "_COMMERCIAL_TAB_CSS" in source
    assert "_render_global_commercial_tab_styles()" in source
    assert "div[data-testid=\"stSegmentedControl\"]" in source
    assert "div[data-testid=\"stRadio\"] div[role=\"radiogroup\"]" in source
    assert "This does not add, move, or remove navigation controls" in source
    assert source.count('"Analysis": ["ULS / PMM", "SLS / Stress & Cracking", "SLS Deflection / Camber", "Report / QA"]') == 1


def test_app_commercial_tabs2_applies_dark_blue_bold_typography_to_existing_controls() -> None:
    source = Path("app.py").read_text(encoding="utf-8")

    assert "UI.COMMERCIAL.TABS2" in source
    assert "--cpmm-ink-blue: #0b3a66" in source
    assert "font-weight: 760" in source
    assert "font-weight: 780" in source
    assert "font-size: 0.9rem" in source
    assert ".stButton button" in source
    assert ".stDownloadButton button" in source
    assert "div[data-testid=\"stWidgetLabel\"]" in source
    assert "div[data-testid=\"stNumberInput\"] label" in source
    assert "div[data-baseweb=\"input\"] input" in source


def test_ui_commercial_tabs3_styles_actual_streamlit_button_group_tabs() -> None:
    source = Path("app.py").read_text(encoding="utf-8")

    assert 'div[data-testid="stButtonGroup"]' in source
    assert 'div[data-testid="stButtonGroup"] button p' in source
    assert 'div[data-testid="stButtonGroup"] [role="radio"][aria-checked="true"]' in source
    assert 'font-weight: 800' in source
    assert '--cpmm-ink-blue' in source


def test_ui_commercial_tabs4_highlights_active_segmented_tabs() -> None:
    source = Path("app.py").read_text(encoding="utf-8")

    assert "UI.COMMERCIAL.TABS4" in source
    assert "--cpmm-active-tab-fill" in source
    assert "--cpmm-active-tab-border" in source
    assert 'button[data-testid="stBaseButton-segmentedControlActive"]' in source
    assert 'box-shadow: inset 0 -3px 0 var(--cpmm-ink-blue)' in source
    assert 'label:has(input:checked)' in source
