"""Concrete PMM Pro Streamlit application."""

from __future__ import annotations

import streamlit as st

from concrete_pmm_pro.state.dirty_state import update_dirty_state_from_session
from concrete_pmm_pro.ui.analysis_page import render_analysis_page
from concrete_pmm_pro.ui.loads_page import render_loads_page
from concrete_pmm_pro.ui.materials_page import render_materials_page
from concrete_pmm_pro.ui.prestress_page import render_prestress_page
from concrete_pmm_pro.ui.project_page import render_project_page
from concrete_pmm_pro.ui.navigation import render_active_choice
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
/* UI.COMMERCIAL.TABS2 / UI.COMMERCIAL.TABS3 / UI.COMMERCIAL.TABS4 / UI.ACTIVE.TABS1 / UI.ACTIVE.TABS2:
   dark-blue bold typography plus compact deterministic active-tab highlight for app-owned navigation. */
:root {
  --cpmm-ink-blue: #0b3a66;
  --cpmm-ink-blue-soft: #164f83;
  --cpmm-blue-border: #9fb9d4;
  --cpmm-blue-fill: #e8f1ff;
  --cpmm-blue-fill-strong: #d9eafe;
  --cpmm-active-tab-fill: #e7f2ff;
  --cpmm-active-tab-border: #0b3a66;
  --cpmm-active-tab-accent: #0b3a66;
  --cpmm-active-tab-shadow: rgba(11, 58, 102, 0.12);
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
button[data-testid="stBaseButton-segmentedControl"],
button[data-testid="stBaseButton-segmentedControlActive"],
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
button[data-testid="stBaseButton-segmentedControl"]:first-child,
button[data-testid="stBaseButton-segmentedControlActive"]:first-child,
div[data-testid="stButtonGroup"] [role="button"]:first-child,
div[data-testid="stButtonGroup"] [role="radio"]:first-child {
  border-radius: 7px 0 0 7px !important;
}
div[data-testid="stSegmentedControl"] button:last-child,
div[data-testid="stButtonGroup"] button:last-child,
button[data-testid="stBaseButton-segmentedControl"]:last-child,
button[data-testid="stBaseButton-segmentedControlActive"]:last-child,
div[data-testid="stButtonGroup"] [role="button"]:last-child,
div[data-testid="stButtonGroup"] [role="radio"]:last-child {
  border-right: 1px solid var(--cpmm-blue-border) !important;
  border-radius: 0 7px 7px 0 !important;
}
div[data-testid="stSegmentedControl"] button[aria-pressed="true"],
div[data-testid="stSegmentedControl"] button[data-selected="true"],
div[data-testid="stSegmentedControl"] button[data-testid="stBaseButton-segmentedControlActive"],
div[data-testid="stButtonGroup"] button[aria-pressed="true"],
div[data-testid="stButtonGroup"] button[data-selected="true"],
div[data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmentedControlActive"],
button[data-testid="stBaseButton-segmentedControlActive"],
div[data-testid="stButtonGroup"] [role="radio"][aria-checked="true"],
div[data-testid="stButtonGroup"] [role="button"][aria-pressed="true"] {
  background: var(--cpmm-active-tab-fill) !important;
  color: var(--cpmm-ink-blue) !important;
  border-color: var(--cpmm-active-tab-border) !important;
  box-shadow: inset 0 -3px 0 var(--cpmm-ink-blue), 0 0 0 1px var(--cpmm-active-tab-shadow) !important;
}
div[data-testid="stSegmentedControl"] button p,
div[data-testid="stSegmentedControl"] button span,
div[data-testid="stButtonGroup"] button p,
div[data-testid="stButtonGroup"] button span,
button[data-testid="stBaseButton-segmentedControl"] p,
button[data-testid="stBaseButton-segmentedControl"] span,
button[data-testid="stBaseButton-segmentedControlActive"] p,
button[data-testid="stBaseButton-segmentedControlActive"] span,
div[data-testid="stButtonGroup"] [role="button"] p,
div[data-testid="stButtonGroup"] [role="button"] span,
div[data-testid="stButtonGroup"] [role="radio"] p,
div[data-testid="stButtonGroup"] [role="radio"] span {
  color: var(--cpmm-ink-blue) !important;
  font-size: 0.94rem !important;
  font-weight: 800 !important;
}

/* Active tab text should stay dark-blue and bold even when Streamlit theme tries to color it red. */
div[data-testid="stSegmentedControl"] button[data-testid="stBaseButton-segmentedControlActive"] p,
div[data-testid="stSegmentedControl"] button[data-testid="stBaseButton-segmentedControlActive"] span,
div[data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmentedControlActive"] p,
div[data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmentedControlActive"] span,
button[data-testid="stBaseButton-segmentedControlActive"] p,
button[data-testid="stBaseButton-segmentedControlActive"] span {
  color: var(--cpmm-ink-blue) !important;
  font-weight: 850 !important;
}


/* Streamlit st.tabs used inside detail workspaces, e.g. Longitudinal/Transverse Rebar.
   Keep them in the same dark-blue active-tab language instead of the theme red underline. */
div[data-testid="stTabs"] div[role="tablist"] {
  gap: 0.12rem !important;
  border-bottom: 1px solid #d8e2ee !important;
}
div[data-testid="stTabs"] button[role="tab"] {
  color: var(--cpmm-ink-blue) !important;
  font-size: 0.91rem !important;
  font-weight: 800 !important;
  padding: 0.42rem 0.86rem !important;
  border-radius: 7px 7px 0 0 !important;
  border: 1px solid transparent !important;
  background: transparent !important;
}
div[data-testid="stTabs"] button[role="tab"] p,
div[data-testid="stTabs"] button[role="tab"] span {
  color: var(--cpmm-ink-blue) !important;
  font-size: 0.91rem !important;
  font-weight: 800 !important;
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  background: var(--cpmm-active-tab-fill) !important;
  border-color: var(--cpmm-blue-border) !important;
  border-bottom-color: var(--cpmm-active-tab-accent) !important;
  box-shadow: inset 0 -3px 0 var(--cpmm-active-tab-accent) !important;
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p,
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] span {
  color: var(--cpmm-ink-blue) !important;
  font-weight: 850 !important;
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
  background: var(--cpmm-active-tab-fill);
  color: var(--cpmm-ink-blue);
  border-color: var(--cpmm-active-tab-border);
  box-shadow: inset 0 -3px 0 var(--cpmm-ink-blue), 0 0 0 1px var(--cpmm-active-tab-shadow);
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

/* Deterministic app-owned navigation: active option is rendered from session_state,
   so the highlight does not depend on Streamlit selected-state DOM internals. */
.cpmm-nav-label {
  color: var(--cpmm-ink-blue);
  font-size: 0.88rem;
  font-weight: 800;
  margin: 0.22rem 0 0.16rem 0;
}
.cpmm-deterministic-nav-row,
.cpmm-deterministic-nav-row--compact {
  margin: 0.02rem 0 0.58rem 0;
}
.cpmm-nav-tab-pill {
  width: 100%;
  min-height: 2.02rem;
  border: 1px solid var(--cpmm-blue-border);
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.28rem 0.72rem;
  color: var(--cpmm-ink-blue);
  font-size: 0.91rem;
  font-weight: 850;
  line-height: 1.12;
  white-space: nowrap;
}
.cpmm-nav-tab-active {
  background: var(--cpmm-active-tab-fill);
  border-color: var(--cpmm-active-tab-border);
  box-shadow: inset 0 -3px 0 var(--cpmm-active-tab-accent), 0 1px 2px var(--cpmm-active-tab-shadow);
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

    Streamlit tabs execute every tab body on each rerun.  PERF.RERUN1 keeps
    navigation as a single-choice control so only the selected workspace/subpage
    runs.  UI.ACTIVE.TABS1 renders the active item from app state so the
    highlight is deterministic and does not depend on Streamlit's internal DOM.
    """

    return render_active_choice(label, options, key=key, horizontal=horizontal)


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
