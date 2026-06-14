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
/* UI.COMMERCIAL.TABS2/TABS3: dark-blue bold typography plus actual Streamlit stButtonGroup selector coverage. */
:root {
  --cpmm-ink-blue: #0b3a66;
  --cpmm-ink-blue-soft: #164f83;
  --cpmm-blue-border: #9fb9d4;
  --cpmm-blue-fill: #e8f1ff;
  --cpmm-blue-fill-strong: #d9eafe;
}

/* Existing app/workspace tabs: bolder, slightly larger, dark-blue text. */
div[data-testid="stSegmentedControl"],
div[data-testid="stButtonGroup"] {
  margin: 0.1rem 0 0.65rem 0;
}

/* Streamlit version compatibility:
   - older segmented controls can expose stSegmentedControl
   - current segmented_control/pills often render as stButtonGroup
   - radio fallback remains styled below */
div[data-testid="stSegmentedControl"] button,
div[data-testid="stButtonGroup"] button,
div[data-testid="stButtonGroup"] [role="button"],
div[data-testid="stButtonGroup"] [role="radio"] {
  border-radius: 0 !important;
  border: 1px solid var(--cpmm-blue-border) !important;
  border-right: 0 !important;
  background: #ffffff !important;
  color: var(--cpmm-ink-blue) !important;
  min-height: 2.24rem !important;
  padding: 0.38rem 1.0rem !important;
  font-size: 0.94rem !important;
  font-weight: 800 !important;
  letter-spacing: 0.004em !important;
  box-shadow: none !important;
}
div[data-testid="stSegmentedControl"] button:first-child,
div[data-testid="stButtonGroup"] button:first-child,
div[data-testid="stButtonGroup"] [role="button"]:first-child,
div[data-testid="stButtonGroup"] [role="radio"]:first-child {
  border-radius: 7px 0 0 7px !important;
}
div[data-testid="stSegmentedControl"] button:last-child,
div[data-testid="stButtonGroup"] button:last-child,
div[data-testid="stButtonGroup"] [role="button"]:last-child,
div[data-testid="stButtonGroup"] [role="radio"]:last-child {
  border-right: 1px solid var(--cpmm-blue-border) !important;
  border-radius: 0 7px 7px 0 !important;
}
div[data-testid="stSegmentedControl"] button[aria-pressed="true"],
div[data-testid="stSegmentedControl"] button[data-selected="true"],
div[data-testid="stButtonGroup"] button[aria-pressed="true"],
div[data-testid="stButtonGroup"] button[data-selected="true"],
div[data-testid="stButtonGroup"] [role="radio"][aria-checked="true"],
div[data-testid="stButtonGroup"] [role="button"][aria-pressed="true"] {
  background: var(--cpmm-blue-fill) !important;
  color: var(--cpmm-ink-blue) !important;
  border-color: var(--cpmm-ink-blue-soft) !important;
  box-shadow: inset 0 -2px 0 var(--cpmm-ink-blue) !important;
}
div[data-testid="stSegmentedControl"] button p,
div[data-testid="stSegmentedControl"] button span,
div[data-testid="stButtonGroup"] button p,
div[data-testid="stButtonGroup"] button span,
div[data-testid="stButtonGroup"] [role="button"] p,
div[data-testid="stButtonGroup"] [role="button"] span,
div[data-testid="stButtonGroup"] [role="radio"] p,
div[data-testid="stButtonGroup"] [role="radio"] span {
  color: var(--cpmm-ink-blue) !important;
  font-size: 0.94rem !important;
  font-weight: 800 !important;
}

/* Radio fallback navigation styled as app tabs, not as ordinary radio text. */
div[data-testid="stRadio"] > label {
  color: var(--cpmm-ink-blue) !important;
  font-size: 0.84rem !important;
  font-weight: 780 !important;
  margin-bottom: 0.24rem !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] {
  gap: 0 !important;
  margin: 0.1rem 0 0.65rem 0;
}
div[data-testid="stRadio"] div[role="radiogroup"] label {
  border: 1px solid var(--cpmm-blue-border);
  border-right: 0;
  border-radius: 0;
  background: #ffffff;
  min-height: 2.18rem;
  padding: 0.24rem 0.84rem;
  color: var(--cpmm-ink-blue);
  font-size: 0.9rem;
  font-weight: 760;
  display: inline-flex;
  align-items: center;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:first-child {
  border-radius: 7px 0 0 7px;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:last-child {
  border-right: 1px solid var(--cpmm-blue-border);
  border-radius: 0 7px 7px 0;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
  background: var(--cpmm-blue-fill);
  color: var(--cpmm-ink-blue);
  border-color: var(--cpmm-ink-blue-soft);
  box-shadow: inset 0 -2px 0 var(--cpmm-ink-blue);
}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) + label {
  border-left-color: var(--cpmm-ink-blue-soft);
}
div[data-testid="stRadio"] div[role="radiogroup"] label [data-testid="stMarkdownContainer"] p,
div[data-testid="stRadio"] div[role="radiogroup"] label p,
div[data-testid="stRadio"] div[role="radiogroup"] label span {
  color: var(--cpmm-ink-blue) !important;
  font-size: 0.94rem !important;
  font-weight: 800 !important;
}

/* Action buttons: commercial-style bold dark-blue text. */
.stButton button,
.stDownloadButton button,
div[data-testid="stFormSubmitButton"] button {
  color: var(--cpmm-ink-blue) !important;
  font-weight: 780 !important;
  font-size: 0.9rem !important;
  border-color: var(--cpmm-blue-border) !important;
}
.stButton button[kind="primary"],
.stDownloadButton button[kind="primary"],
div[data-testid="stFormSubmitButton"] button[kind="primary"] {
  background: var(--cpmm-blue-fill) !important;
  color: var(--cpmm-ink-blue) !important;
  border-color: var(--cpmm-ink-blue-soft) !important;
}
.stButton button:hover,
.stDownloadButton button:hover,
div[data-testid="stFormSubmitButton"] button:hover {
  color: var(--cpmm-ink-blue) !important;
  border-color: var(--cpmm-ink-blue) !important;
  background: var(--cpmm-blue-fill-strong) !important;
}

/* Labels for user input points and selectable/editable controls. */
div[data-testid="stWidgetLabel"] label,
div[data-testid="stWidgetLabel"] p,
div[data-testid="stSelectbox"] label,
div[data-testid="stMultiSelect"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stDateInput"] label,
div[data-testid="stFileUploader"] label,
div[data-testid="stCheckbox"] label,
div[data-testid="stToggle"] label,
div[data-testid="stDataFrame"] label,
div[data-testid="stDataEditor"] label {
  color: var(--cpmm-ink-blue) !important;
  font-weight: 760 !important;
}

/* Field text and select display values should read as engineering inputs. */
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="select"] div,
div[data-baseweb="base-input"] input {
  color: var(--cpmm-ink-blue) !important;
  font-weight: 650 !important;
}

/* Section/card headings that tell the user where to act. */
h2, h3, h4,
div[data-testid="stMarkdownContainer"] h2,
div[data-testid="stMarkdownContainer"] h3,
div[data-testid="stMarkdownContainer"] h4 {
  color: var(--cpmm-ink-blue);
  font-weight: 760;
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
