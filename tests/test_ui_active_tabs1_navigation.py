from __future__ import annotations

from pathlib import Path


def test_ui_active_tabs1_uses_app_state_navigation_renderer_not_streamlit_selected_dom() -> None:
    app_source = Path("app.py").read_text(encoding="utf-8")
    nav_source = Path("concrete_pmm_pro/ui/navigation.py").read_text(encoding="utf-8")
    analysis_source = Path("concrete_pmm_pro/ui/analysis_page.py").read_text(encoding="utf-8")

    assert "UI.ACTIVE.TABS1" in app_source
    assert "render_active_choice" in app_source
    assert "render_active_choice" in analysis_source
    assert "cpmm-nav-tab-active" in app_source
    assert "aria-current=\"page\"" in nav_source
    assert "st.session_state[key]" in nav_source
    assert "st.button(" in nav_source
    assert "segmented_control(" not in nav_source


def test_ui_active_tabs1_preserves_existing_navigation_option_lists() -> None:
    app_source = Path("app.py").read_text(encoding="utf-8")

    assert '"Setup": ["Project", "Materials"]' in app_source
    assert '"Sections": ["Section Builder", "Rebar", "Prestress"]' in app_source
    assert '"Analysis": ["ULS / PMM", "SLS / Stress & Cracking", "SLS Deflection / Camber", "Report / QA"]' in app_source
