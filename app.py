"""Concrete PMM Pro Streamlit application."""

from __future__ import annotations

import streamlit as st

from concrete_pmm_pro.state.dirty_state import update_dirty_state_from_session
from concrete_pmm_pro.ui.analysis_page import render_analysis_page
from concrete_pmm_pro.ui.loads_page import render_loads_page
from concrete_pmm_pro.ui.materials_page import render_materials_page
from concrete_pmm_pro.ui.prestress_page import render_prestress_page
from concrete_pmm_pro.ui.project_page import render_project_page
from concrete_pmm_pro.ui.rebar_page import render_rebar_page
from concrete_pmm_pro.ui.section_builder import render_section_builder


WORKSPACE_NAVIGATION = {
    "Setup": ["Project", "Materials"],
    "Sections": ["Section Builder", "Rebar", "Prestress"],
    "Loads": ["Loads"],
    "Analysis": ["ULS / PMM", "SLS / Stress & Cracking", "SLS Deflection / Camber", "Report / QA"],
    "Results": ["Results"],
}

RESULTS_WORKSPACE_PLACEHOLDER = (
    "Future Results Workspace. Current result outputs remain available under Analysis. "
    "Future milestones will add Summary Table, Case Details, Interaction Diagram, Charts, and Report Preview."
)


_COMMERCIAL_TAB_CSS = """
<style>
/* UI.COMMERCIAL.TABS1: visual-only polish for existing Streamlit navigation controls. */
div[data-testid="stSegmentedControl"] {
  margin: 0.1rem 0 0.65rem 0;
}
div[data-testid="stSegmentedControl"] button {
  border-radius: 0 !important;
  border: 1px solid #cfd8e3 !important;
  border-right: 0 !important;
  background: #ffffff !important;
  color: #344054 !important;
  min-height: 2.05rem !important;
  padding: 0.32rem 0.86rem !important;
  font-size: 0.82rem !important;
  font-weight: 650 !important;
  box-shadow: none !important;
}
div[data-testid="stSegmentedControl"] button:first-child {
  border-radius: 7px 0 0 7px !important;
}
div[data-testid="stSegmentedControl"] button:last-child {
  border-right: 1px solid #cfd8e3 !important;
  border-radius: 0 7px 7px 0 !important;
}
div[data-testid="stSegmentedControl"] button[aria-pressed="true"],
div[data-testid="stSegmentedControl"] button[data-selected="true"] {
  background: #1f5f99 !important;
  color: #ffffff !important;
  border-color: #1f5f99 !important;
}
div[data-testid="stRadio"] > label {
  color: #344054 !important;
  font-size: 0.78rem !important;
  font-weight: 700 !important;
  margin-bottom: 0.22rem !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] {
  gap: 0 !important;
  margin: 0.1rem 0 0.65rem 0;
}
div[data-testid="stRadio"] div[role="radiogroup"] label {
  border: 1px solid #cfd8e3;
  border-right: 0;
  border-radius: 0;
  background: #ffffff;
  min-height: 2.05rem;
  padding: 0.22rem 0.78rem;
  color: #344054;
  font-size: 0.82rem;
  font-weight: 650;
  display: inline-flex;
  align-items: center;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:first-child {
  border-radius: 7px 0 0 7px;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:last-child {
  border-right: 1px solid #cfd8e3;
  border-radius: 0 7px 7px 0;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
  background: #1f5f99;
  color: #ffffff;
  border-color: #1f5f99;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) + label {
  border-left-color: #1f5f99;
}
div[data-testid="stRadio"] div[role="radiogroup"] label [data-testid="stMarkdownContainer"] p {
  font-size: inherit;
  font-weight: inherit;
}
</style>
"""


def _render_global_commercial_tab_styles() -> None:
    """Apply visual-only tab polish to existing navigation widgets.

    This does not add, move, or remove navigation controls; it only styles the
    existing segmented/radio controls so app tabs read closer to commercial
    engineering software.
    """

    st.markdown(_COMMERCIAL_TAB_CSS, unsafe_allow_html=True)


def _safe_choice(label: str, options: list[str], *, key: str, horizontal: bool = True) -> str:
    """Return one selected option without rendering inactive pages.

    Streamlit tabs execute every tab body on each rerun.  PERF.RERUN1 uses a
    segmented/radio choice instead so only the selected workspace/subpage runs.
    This is the key performance gate for heavy Analysis and preview code.
    """

    if not options:
        raise ValueError("Navigation options must not be empty.")
    if st.session_state.get(key) not in options:
        st.session_state[key] = options[0]
    # Prefer segmented_control when available; fall back to radio for older
    # Streamlit versions and for lightweight test stubs.
    segmented = getattr(st, "segmented_control", None)
    if callable(segmented):
        try:
            value = segmented(label, options, key=key, selection_mode="single")
            if value in options:
                return str(value)
        except TypeError:
            pass
    value = st.radio(label, options, key=key, horizontal=horizontal, label_visibility="collapsed")
    return str(value) if value in options else str(st.session_state.get(key, options[0]))


def render_setup_workspace() -> None:
    active = _safe_choice("Setup workspace", WORKSPACE_NAVIGATION["Setup"], key="_nav_setup_subpage")
    if active == "Project":
        render_project_page()
    elif active == "Materials":
        render_materials_page()


def render_sections_workspace() -> None:
    active = _safe_choice("Sections workspace", WORKSPACE_NAVIGATION["Sections"], key="_nav_sections_subpage")
    if active == "Section Builder":
        render_section_builder()
    elif active == "Rebar":
        render_rebar_page()
    elif active == "Prestress":
        render_prestress_page()


def render_loads_workspace() -> None:
    render_loads_page()


def render_analysis_workspace() -> None:
    render_analysis_page()


def render_results_workspace() -> None:
    st.info(RESULTS_WORKSPACE_PLACEHOLDER)


def main() -> None:
    st.set_page_config(page_title="Concrete PMM Pro", layout="wide")
    _render_global_commercial_tab_styles()
    st.title("Concrete PMM Pro")
    st.caption(
        "Milestone STATE.RESULT1: PMM analysis cache persists across navigation and project save/load. "
        "Internal units: mm, MPa, N, N-mm."
    )

    update_dirty_state_from_session(st.session_state)

    active_workspace = _safe_choice(
        "Workspace",
        list(WORKSPACE_NAVIGATION.keys()),
        key="_nav_active_workspace",
    )
    if active_workspace == "Setup":
        render_setup_workspace()
    elif active_workspace == "Sections":
        render_sections_workspace()
    elif active_workspace == "Loads":
        render_loads_workspace()
    elif active_workspace == "Analysis":
        render_analysis_workspace()
    elif active_workspace == "Results":
        render_results_workspace()


if __name__ == "__main__":
    main()
