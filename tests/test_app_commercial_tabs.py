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


def test_ui_active_tabs1_adds_deterministic_active_tab_css() -> None:
    source = Path("app.py").read_text(encoding="utf-8")

    assert "UI.ACTIVE.TABS1" in source
    assert ".cpmm-nav-tab-active" in source
    assert "background: var(--cpmm-active-tab-fill)" in source
    assert "render_active_choice" in source


def test_ui_active_tabs2_uses_compact_commercial_nav_and_styles_streamlit_tabs() -> None:
    source = Path("app.py").read_text(encoding="utf-8")

    assert "UI.ACTIVE.TABS2" in source
    assert ".cpmm-deterministic-nav-row--compact" in source
    assert "min-height: 1.64rem" in source
    assert "0 1px 1px var(--cpmm-active-tab-shadow)" in source
    assert 'div[data-testid="stTabs"] button[role="tab"][aria-selected="true"]' in source
    assert "--cpmm-active-tab-accent" in source


def test_ui_active_tabs3_applies_working_screen_density_polish() -> None:
    source = Path("app.py").read_text(encoding="utf-8")

    assert "UI.ACTIVE.TABS3" in source
    assert ".block-container" in source
    assert "padding-top: 1.55rem" in source
    assert "font-size: 1.95rem" in source
    assert "min-height: 1.64rem" in source
    assert "0.01rem 0 0.34rem" in source
    assert "inset 0 -2px 0 var(--cpmm-active-tab-accent)" in source


def test_app_brand1_renames_visible_app_and_prevents_header_crop() -> None:
    source = Path("app.py").read_text(encoding="utf-8")

    assert 'page_title="Concrete Section Pro"' in source
    assert 'st.title("Concrete Section Pro")' in source
    assert "Concrete section analysis and design-review workspace." in source
    assert "line-height: 1.24rem" not in source
    assert "line-height: 1.24" in source
    assert "padding-top: 1.55rem" in source
    assert "overflow: visible" in source
