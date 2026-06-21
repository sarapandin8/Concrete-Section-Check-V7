"""Concrete Section Pro Streamlit application."""

from __future__ import annotations

from html import escape

import streamlit as st

from concrete_pmm_pro.core.analysis import AnalysisModeSettings
from concrete_pmm_pro.core.analysis_modes import analysis_mode_label
from concrete_pmm_pro.state.dirty_state import current_project_dirty_status, update_dirty_state_from_session
from concrete_pmm_pro.io.project_io import (
    ProjectIOError,
    apply_project_to_session_state,
    project_from_json,
    project_from_session_state,
    project_to_json,
)
from concrete_pmm_pro.ui.analysis_page import render_analysis_page
from concrete_pmm_pro.ui.loads_page import render_loads_page
from concrete_pmm_pro.ui.materials_page import render_materials_page
from concrete_pmm_pro.ui.prestress_page import render_prestress_page
from concrete_pmm_pro.ui.project_page import render_project_page
from concrete_pmm_pro.ui.navigation import render_active_choice
from concrete_pmm_pro.ui.rebar_page import render_rebar_page
from concrete_pmm_pro.ui.section_builder import render_section_builder
from concrete_pmm_pro.visualization.plot_readability import install_streamlit_plotly_readability_patch


WORKSPACE_NAVIGATION = {
    "Setup": ["Project", "Materials"],
    "Sections": ["Section Builder", "Rebar", "Prestress"],
    "Loads": ["Loads"],
    "Analysis": ["ULS Strength", "SLS / Stress & Cracking", "SLS Deflection / Camber", "Report / QA"],
    "Results": ["Results"],
}

RESULTS_WORKSPACE_PLACEHOLDER = (
    "Future Results Workspace. Current result outputs remain available under Analysis. "
    "Future milestones will add Summary Table, Case Details, Interaction Diagram, Charts, and Report Preview."
)


_COMMERCIAL_TAB_CSS = """
<style>
/* UI.COMMERCIAL.TABS2 / UI.COMMERCIAL.TABS3 / UI.COMMERCIAL.TABS4 / UI.ACTIVE.TABS1 / UI.ACTIVE.TABS2 / UI.ACTIVE.TABS3 / UI.ACTION.BUTTONS1 / UI.ACTION.BUTTONS2:
   dark-blue bold typography plus compact deterministic active-tab highlight and state-aware highlighted primary action buttons. */
:root {
  --cpmm-ink-blue: #0b3a66;
  --cpmm-ink-blue-soft: #164f83;
  --cpmm-blue-border: #9fb9d4;
  --cpmm-blue-fill: #e8f1ff;
  --cpmm-blue-fill-strong: #d9eafe;
  --cpmm-action-fill: #1d6fe7;
  --cpmm-action-fill-hover: #175cd3;
  --cpmm-action-border: #1d6fe7;
  --cpmm-action-border-hover: #0f5ec2;
  --cpmm-action-disabled-fill: #f3f6f9;
  --cpmm-action-disabled-border: #c8d2dd;
  --cpmm-action-disabled-text: #6d7d8f;
  --cpmm-active-tab-fill: #e7f2ff;
  --cpmm-active-tab-border: #1d6fe7;
  --cpmm-active-tab-accent: #1d6fe7;
  --cpmm-active-tab-shadow: rgba(29, 111, 231, 0.14);
}

/* UI.ACTIVE.TABS3: make the app feel like a working engineering screen, not a landing page. */
.block-container {
  padding-top: 1.55rem !important;
}
div[data-testid="stVerticalBlock"] {
  gap: 0.48rem !important;
}
h1, div[data-testid="stMarkdownContainer"] h1 {
  color: var(--cpmm-ink-blue) !important;
  font-size: 1.95rem !important;
  line-height: 1.24 !important;
  margin: 0.12rem 0 0.18rem 0 !important;
  font-weight: 850 !important;
  overflow: visible !important;
}
div[data-testid="stCaptionContainer"] {
  margin-bottom: 0.15rem !important;
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
  box-shadow: inset 0 -3px 0 var(--cpmm-active-tab-accent), 0 0 0 1px var(--cpmm-active-tab-shadow) !important;
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
  overflow: visible !important;
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
  overflow: visible !important;
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
  box-shadow: inset 0 -3px 0 var(--cpmm-active-tab-accent), 0 0 0 1px var(--cpmm-active-tab-shadow);
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
  margin: 0.10rem 0 0.08rem 0;
}
.cpmm-deterministic-nav-row,
.cpmm-deterministic-nav-row--compact {
  margin: 0.02rem 0 0.48rem 0; /* previous compact baseline: 0.01rem 0 0.34rem */
}
.cpmm-deterministic-nav-row--compact .stButton button,
.cpmm-deterministic-nav-row--compact .stButton button p,
.cpmm-deterministic-nav-row--compact .stButton button span {
  white-space: nowrap !important;
  word-break: keep-all !important;
  overflow-wrap: normal !important;
  min-width: 108px !important;
}
.cpmm-nav-tab-pill {
  width: 100%;
  min-height: 1.92rem; /* previous compact baseline: min-height: 1.64rem */
  border: 1px solid var(--cpmm-blue-border);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.24rem 0.72rem;
  color: var(--cpmm-ink-blue);
  font-size: 0.84rem;
  font-weight: 900;
  line-height: 1.08;
  white-space: nowrap;
  min-width: 108px;
}
.cpmm-nav-tab-active {
  background: var(--cpmm-active-tab-fill);
  border-color: var(--cpmm-active-tab-border);
  box-shadow: inset 0 -2px 0 var(--cpmm-active-tab-accent), 0 1px 1px var(--cpmm-active-tab-shadow);
}

/* Action buttons: commercial-style bold dark-blue text.
   UI.COMMERCIAL4.3.2 migrates primary/action buttons to the app blue accent
   so Run, Save, Upload/Load, Apply, Replace, Append, and confirm actions read
   as active controls in the same language as selected navigation. */
.stButton button,
.stDownloadButton button,
div[data-testid="stFormSubmitButton"] button {
  color: var(--cpmm-ink-blue) !important;
  font-weight: 800 !important;
  font-size: 0.86rem !important;
  min-height: 1.68rem !important;
  padding: 0.22rem 0.64rem !important;
  border-radius: 5px !important;
  border-color: var(--cpmm-blue-border) !important;
}
.stButton button[kind="primary"],
.stDownloadButton button[kind="primary"],
div[data-testid="stFormSubmitButton"] button[kind="primary"],
button[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, var(--cpmm-action-fill), var(--cpmm-action-fill-hover)) !important;
  color: #ffffff !important;
  border-color: var(--cpmm-action-border) !important;
  font-weight: 850 !important;
  box-shadow: inset 0 -2px 0 rgba(7, 55, 99, 0.20) !important;
}
.stButton button[kind="primary"] p,
.stDownloadButton button[kind="primary"] p,
div[data-testid="stFormSubmitButton"] button[kind="primary"] p,
button[data-testid="stBaseButton-primary"] p,
.stButton button[kind="primary"] span,
.stDownloadButton button[kind="primary"] span,
div[data-testid="stFormSubmitButton"] button[kind="primary"] span,
button[data-testid="stBaseButton-primary"] span {
  color: #ffffff !important;
  font-weight: 850 !important;
}
.stButton button:hover,
.stDownloadButton button:hover,
div[data-testid="stFormSubmitButton"] button:hover {
  color: var(--cpmm-ink-blue) !important;
  border-color: var(--cpmm-ink-blue) !important;
  background: var(--cpmm-blue-fill-strong) !important;
}
.stButton button[kind="primary"]:hover,
.stDownloadButton button[kind="primary"]:hover,
div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover {
  color: #ffffff !important;
  border-color: var(--cpmm-action-border-hover) !important;
  background: linear-gradient(135deg, var(--cpmm-action-fill-hover), #0f5ec2) !important;
}
/* UI.ACTION.BUTTONS2: disabled action buttons must not look ready to run. */
.stButton button:disabled,
.stDownloadButton button:disabled,
div[data-testid="stFormSubmitButton"] button:disabled,
button[data-testid="stBaseButton-primary"]:disabled,
button[data-testid="stBaseButton-secondary"]:disabled {
  background: var(--cpmm-action-disabled-fill) !important;
  color: var(--cpmm-action-disabled-text) !important;
  border-color: var(--cpmm-action-disabled-border) !important;
  box-shadow: none !important;
  opacity: 1 !important;
  cursor: not-allowed !important;
}
.stButton button:disabled p,
.stDownloadButton button:disabled p,
div[data-testid="stFormSubmitButton"] button:disabled p,
button[data-testid="stBaseButton-primary"]:disabled p,
button[data-testid="stBaseButton-secondary"]:disabled p,
.stButton button:disabled span,
.stDownloadButton button:disabled span,
div[data-testid="stFormSubmitButton"] button:disabled span,
button[data-testid="stBaseButton-primary"]:disabled span,
button[data-testid="stBaseButton-secondary"]:disabled span {
  color: var(--cpmm-action-disabled-text) !important;
  font-weight: 800 !important;
}
/* Compact runtime status cards keep the PMM run area readable without large metrics. */
.cpmm-runtime-compact-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.45rem;
  margin-top: 0.42rem;
}
.cpmm-runtime-compact-card {
  border: 1px solid #d9e2ec;
  background: #fbfdff;
  border-radius: 6px;
  padding: 0.42rem 0.58rem;
  min-height: 2.9rem;
}
.cpmm-runtime-compact-card .cpmm-kicker {
  color: #55708b;
  font-size: 0.70rem;
  font-weight: 760;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
.cpmm-runtime-compact-card .cpmm-value {
  color: var(--cpmm-ink-blue);
  font-size: 1.02rem;
  font-weight: 850;
  line-height: 1.25;
  margin-top: 0.14rem;
}
@media (max-width: 900px) {
  .cpmm-runtime-compact-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
/* Upload controls have a built-in Browse button; keep only the dropzone
   Browse button in the soft action language. Do not style every button under
   stFileUploader: uploaded-file pills also contain remove (x) buttons, and
   broad button selectors can make those native controls hard to click. */
div[data-testid="stFileUploaderDropzone"] button {
  background: #e8f1ff !important;
  color: var(--cpmm-ink-blue) !important;
  border-color: #9fb9d4 !important;
  font-weight: 850 !important;
}
div[data-testid="stFileUploaderDropzone"] button:hover {
  background: #d9eafe !important;
  border-color: #1d6fe7 !important;
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

/* UI.THEME1: visual-only commercial engineering theme foundation.
   This layer intentionally changes color, spacing, cards, and table chrome only.
   It does not add, remove, move, or rename widgets and it does not affect session-state keys. */
:root {
  --cpmm-theme-navy: #071a33;
  --cpmm-theme-navy-2: #0b2545;
  --cpmm-theme-navy-3: #102f55;
  --cpmm-theme-bg: #f4f7fb;
  --cpmm-theme-panel: #ffffff;
  --cpmm-theme-panel-soft: #f8fbff;
  --cpmm-theme-line: #d7e2ee;
  --cpmm-theme-shadow: rgba(7, 26, 51, 0.08);
  --cpmm-theme-shadow-strong: rgba(7, 26, 51, 0.14);
  --cpmm-theme-cyan: #3aa0c4;
  --cpmm-theme-amber: #f6b84b;
}
html, body, [data-testid="stAppViewContainer"] {
  background: var(--cpmm-theme-bg) !important;
}
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #071a33 0%, #0b2545 100%) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.10) !important;
}
section[data-testid="stSidebar"] *:not(input):not(textarea):not(option):not(svg):not(path) {
  color: #eef6ff !important;
}
section[data-testid="stSidebar"] div[data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] div[data-testid="stWidgetLabel"] label,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p {
  color: #d9e8f7 !important;
  font-weight: 750 !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] *,
section[data-testid="stSidebar"] div[data-baseweb="input"] input,
section[data-testid="stSidebar"] div[data-baseweb="base-input"] input,
section[data-testid="stSidebar"] textarea {
  color: #071a33 !important;
}
section[data-testid="stSidebar"] .stButton button,
section[data-testid="stSidebar"] .stDownloadButton button {
  background: #0f335d !important;
  color: #f7fbff !important;
  border-color: #3a5f88 !important;
}
section[data-testid="stSidebar"] .stButton button[kind="primary"],
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
  background: #1f8fb3 !important;
  border-color: #58c3e3 !important;
  color: #ffffff !important;
  box-shadow: inset 0 -2px 0 rgba(255, 255, 255, 0.18) !important;
}
.block-container {
  background: transparent !important;
}
div[data-testid="stAppViewBlockContainer"] > div[data-testid="stVerticalBlock"] {
  background: transparent !important;
}
/* Top-level cards and Streamlit containers. */
div[data-testid="stMetric"],
div[data-testid="stDataFrame"],
div[data-testid="stDataEditor"],
div[data-testid="stPlotlyChart"],
div[data-testid="stPyplot"],
div[data-testid="stImage"] {
  border-radius: 9px !important;
}
/* UI.COMMERCIAL4.5: soften Streamlit metric cards.  Metrics are dashboard
   summaries, not primary actions; keep the blue accent in border/value only. */
div[data-testid="stMetric"] {
  background: linear-gradient(180deg, #ffffff 0%, #f4f8ff 100%) !important;
  border: 1px solid #cfe0ff !important;
  border-left: 5px solid #1d6fe7 !important;
  box-shadow: 0 3px 10px rgba(29, 111, 231, 0.08) !important;
  padding: 0.50rem 0.66rem !important;
}
div[data-testid="stMetric"] label,
div[data-testid="stMetric"] [data-testid="stMetricLabel"],
div[data-testid="stMetric"] [data-testid="stMetricLabel"] p {
  color: #526f8d !important;
  font-weight: 900 !important;
  letter-spacing: 0.035em !important;
  text-transform: uppercase !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"],
div[data-testid="stMetric"] [data-testid="stMetricValue"] div {
  color: #175cd3 !important;
  font-weight: 950 !important;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
  color: #166534 !important;
  font-weight: 800 !important;
}
/* UI.COMMERCIAL4.4: light-blue accordion system. Dark navy remains reserved for
   structural/brand emphasis; expanders now behave as lightweight group controls. */
div[data-testid="stExpander"] details {
  border: 1px solid #cfe0ff !important;
  border-radius: 9px !important;
  overflow: hidden !important;
  background: #ffffff !important;
  box-shadow: 0 2px 8px rgba(29, 111, 231, 0.08) !important;
}
div[data-testid="stExpander"] details > summary {
  background: linear-gradient(90deg, #f4f8ff 0%, #eef5ff 82%, #e7f1ff 100%) !important;
  border-bottom: 1px solid #cfe0ff !important;
  min-height: 2.0rem !important;
  padding: 0.44rem 0.75rem !important;
}
div[data-testid="stExpander"] details[open] > summary {
  background: linear-gradient(90deg, #eaf2ff 0%, #e0ecff 100%) !important;
  border-bottom-color: #b7d0ff !important;
}
div[data-testid="stExpander"] details > summary p,
div[data-testid="stExpander"] details > summary span,
div[data-testid="stExpander"] details > summary div {
  color: #123a6b !important;
  font-weight: 850 !important;
  letter-spacing: 0.006em !important;
}
div[data-testid="stExpander"] details > summary svg {
  color: #1d6fe7 !important;
  fill: #1d6fe7 !important;
}
div[data-testid="stExpander"] details > div[role="group"] {
  background: #ffffff !important;
  padding-top: 0.56rem !important;
}
/* Data tables/editors: stronger engineering grid chrome without touching editor behavior. */
div[data-testid="stDataFrame"],
div[data-testid="stDataEditor"] {
  border: 1px solid var(--cpmm-theme-line) !important;
  background: var(--cpmm-theme-panel) !important;
  box-shadow: 0 2px 8px var(--cpmm-theme-shadow) !important;
  overflow: hidden !important;
}
div[data-testid="stDataFrame"] [role="columnheader"],
div[data-testid="stDataEditor"] [role="columnheader"],
div[data-testid="stDataFrame"] [data-testid="stTableStyledCell"],
div[data-testid="stDataEditor"] [data-testid="stTableStyledCell"] {
  font-weight: 800 !important;
}
div[data-testid="stDataFrame"] [role="columnheader"],
div[data-testid="stDataEditor"] [role="columnheader"] {
  color: var(--cpmm-theme-navy) !important;
}
/* Plots sit inside report-like panels. */
div[data-testid="stPlotlyChart"],
div[data-testid="stPyplot"] {
  border: 1px solid var(--cpmm-theme-line) !important;
  background: #ffffff !important;
  box-shadow: 0 2px 8px var(--cpmm-theme-shadow) !important;
  padding: 0.35rem !important;
}
/* Existing custom cards should pick up the darker professional result style. */
.cpmm-analysis-strip,
.cpmm-analysis-card,
.cpmm-governing-card,
.cpmm-prestress-chip,
.cpmm-prestress-kv-panel,
.cpmm-prestress-note-panel,
.cpmm-dashboard-card,
.cpmm-summary-strip,
.cpmm-compact-panel,
.cpmm-runtime-compact-card {
  border-color: var(--cpmm-theme-line) !important;
  box-shadow: 0 2px 8px var(--cpmm-theme-shadow) !important;
}
.cpmm-analysis-title,
.cpmm-card-title,
.cpmm-summary-title,
.cpmm-prestress-chip-label,
.cpmm-prestress-kv-label,
.cpmm-governing-label,
.cpmm-runtime-compact-card .cpmm-kicker {
  color: #526f8d !important;
  font-weight: 850 !important;
  letter-spacing: 0.025em !important;
  text-transform: uppercase !important;
}
.cpmm-analysis-value,
.cpmm-card-value,
.cpmm-summary-value,
.cpmm-prestress-chip-value,
.cpmm-prestress-kv-value,
.cpmm-governing-value,
.cpmm-runtime-compact-card .cpmm-value {
  color: var(--cpmm-theme-navy) !important;
  font-weight: 900 !important;
}
.cpmm-executive-header {
  background: linear-gradient(90deg, var(--cpmm-theme-navy) 0%, var(--cpmm-theme-navy-2) 74%, #123e6d 100%) !important;
  border-color: #183f6b !important;
  box-shadow: 0 4px 14px var(--cpmm-theme-shadow-strong) !important;
}
.cpmm-executive-eyebrow,
.cpmm-executive-title,
.cpmm-executive-subtitle {
  color: #f7fbff !important;
}
.cpmm-sls-action-panel,
.cpmm-prestress-mode-card {
  border-left: 5px solid var(--cpmm-theme-cyan) !important;
  border-color: var(--cpmm-theme-line) !important;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%) !important;
  box-shadow: 0 2px 8px var(--cpmm-theme-shadow) !important;
}
.cpmm-decision-banner,
.cpmm-prestress-table-note,
.cpmm-prestress-quiet-note {
  box-shadow: 0 2px 8px var(--cpmm-theme-shadow) !important;
}
/* Streamlit alerts and callouts: cleaner border and density. */
div[data-testid="stAlert"] {
  border-radius: 8px !important;
  border: 1px solid var(--cpmm-theme-line) !important;
  box-shadow: 0 2px 8px rgba(7, 26, 51, 0.05) !important;
}
/* Forms and inputs get a more deliberate engineering-software feel. */
div[data-baseweb="input"],
div[data-baseweb="base-input"],
div[data-baseweb="select"],
div[data-baseweb="textarea"],
textarea,
input {
  border-radius: 6px !important;
}
/* Header text polish under the global brand. */
div[data-testid="stMarkdownContainer"] h2 {
  border-bottom: 2px solid #d7e2ee !important;
  padding-bottom: 0.18rem !important;
}
div[data-testid="stMarkdownContainer"] h3 {
  color: var(--cpmm-theme-navy) !important;
}


/* UI.COMMERCIAL4: premium app shell, sidebar rail, and centered commercial canvas. */
.stApp {
  background: linear-gradient(135deg, #f4f8fd 0%, #f7fbff 48%, #eef5ff 100%) !important;
}
.block-container {
  max-width: 1720px !important;
  padding-left: 1.45rem !important;
  padding-right: 1.45rem !important;
}
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #f3f8ff 0%, #ffffff 44%, #e7f1ff 100%) !important;
  border-right: 1px solid rgba(11, 58, 102, 0.22) !important;
  box-shadow: 12px 0 30px rgba(7, 26, 51, 0.085) !important;
}
section[data-testid="stSidebar"] * {
  text-shadow: none !important;
}
section[data-testid="stSidebar"] .stButton button {
  min-height: 2.10rem !important;
  border-radius: 10px !important;
  border-color: #a9c4df !important;
  background: #ffffff !important;
  color: #0b3a66 !important;
  font-weight: 900 !important;
  opacity: 1 !important;
}
section[data-testid="stSidebar"] .stButton button p,
section[data-testid="stSidebar"] .stButton button span {
  color: #0b3a66 !important;
  font-weight: 900 !important;
}
section[data-testid="stSidebar"] > div {
  padding-top: 1.05rem !important;
}
.cpmm-sidebar-brand {
  border-bottom: 1px solid rgba(11, 58, 102, 0.12);
  padding: 0.20rem 0.20rem 0.92rem 0.20rem;
  margin-bottom: 0.72rem;
}
.cpmm-sidebar-brand-title {
  color: #061b35 !important;
  font-size: 1.22rem;
  line-height: 1.08;
  font-weight: 950;
  letter-spacing: -0.015em;
}
.cpmm-sidebar-brand-subtitle {
  margin-top: 0.42rem;
  color: #344054 !important;
  font-size: 0.80rem;
  line-height: 1.34;
  font-weight: 650;
}
.cpmm-sidebar-section-label {
  color: #0b3a66 !important;
  font-size: 0.70rem;
  font-weight: 950;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin: 0.82rem 0 0.38rem 0.10rem;
}
.cpmm-sidebar-active-pill,
.cpmm-sidebar-sub-active-pill {
  display: flex;
  align-items: center;
  gap: 0.50rem;
  width: 100%;
  border-radius: 11px;
  padding: 0.55rem 0.66rem;
  background: linear-gradient(135deg, #175cd3, #2f80ed);
  color: #ffffff;
  font-size: 0.86rem;
  font-weight: 900;
  box-shadow: 0 9px 20px rgba(23, 92, 211, 0.22);
  margin: 0.22rem 0;
}
.cpmm-sidebar-sub-active-pill {
  background: linear-gradient(135deg, #175cd3, #2f80ed);
  font-size: 0.78rem;
  padding: 0.44rem 0.58rem;
  box-shadow: 0 7px 16px rgba(23, 92, 211, 0.20);
}
.cpmm-sidebar-status {
  border: 1px solid rgba(11, 58, 102, 0.20);
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
  padding: 0.78rem 0.78rem;
  box-shadow: 0 10px 24px rgba(7, 26, 51, 0.09);
  margin-top: 0.86rem;
}
.cpmm-sidebar-status-row {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.50rem;
  align-items: center;
  margin: 0.42rem 0;
}
.cpmm-sidebar-status-dot {
  width: 25px;
  height: 25px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 950;
  font-size: 0.74rem;
  background: #e8f1ff;
  color: #175cd3;
}
.cpmm-sidebar-status-dot.ready { background: #dcfce7; color: #16833a; }
.cpmm-sidebar-status-dot.warning { background: #fef3c7; color: #b45309; }
.cpmm-sidebar-status-title {
  color: #526f8d !important;
  font-size: 0.64rem;
  font-weight: 950;
  letter-spacing: 0.055em;
  text-transform: uppercase;
}
.cpmm-sidebar-status-value {
  color: #061b35 !important;
  font-size: 0.85rem;
  font-weight: 950;
  margin-top: 0.04rem;
  line-height: 1.22;
}

/* UI.COMMERCIAL4.1: sidebar contrast cleanup.  Older dark-sidebar
   selectors intentionally remain for backward compatibility, but the new
   premium light rail must keep readable ink colors. */
.cpmm-sidebar-brand-title,
.cpmm-sidebar-status-value { color: #061b35 !important; }
.cpmm-sidebar-brand-subtitle { color: #344054 !important; }
.cpmm-sidebar-section-label { color: #0b3a66 !important; }
.cpmm-sidebar-status-title { color: #526f8d !important; }
.cpmm-sidebar-active-pill, .cpmm-sidebar-active-pill *,
.cpmm-sidebar-sub-active-pill, .cpmm-sidebar-sub-active-pill * { color: #ffffff !important; }

/* UI.COMMERCIAL4.2: harden sidebar contrast and mini-status readability. */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #eef6ff 0%, #ffffff 44%, #eaf3ff 100%) !important;
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"],
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] * {
  opacity: 1 !important;
  filter: none !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-brand {
  background: rgba(255, 255, 255, 0.72) !important;
  border: 1px solid rgba(11, 58, 102, 0.16) !important;
  border-radius: 14px !important;
  padding: 0.70rem 0.72rem 0.76rem 0.72rem !important;
  margin-bottom: 0.84rem !important;
  box-shadow: 0 8px 20px rgba(7, 26, 51, 0.07) !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-brand-title {
  color: #062348 !important;
  font-size: 1.18rem !important;
  font-weight: 950 !important;
  opacity: 1 !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-brand-subtitle {
  color: #243b53 !important;
  font-size: 0.78rem !important;
  font-weight: 750 !important;
  opacity: 1 !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-section-label,
section[data-testid="stSidebar"] .cpmm-sidebar-status .cpmm-sidebar-section-label {
  color: #073763 !important;
  font-weight: 950 !important;
  opacity: 1 !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-status {
  background: linear-gradient(180deg, #ffffff 0%, #f2f8ff 100%) !important;
  border: 1px solid rgba(7, 55, 99, 0.30) !important;
  box-shadow: 0 12px 26px rgba(7, 26, 51, 0.12) !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-status-title {
  color: #34536f !important;
  font-weight: 950 !important;
  opacity: 1 !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-status-value {
  color: #061b35 !important;
  font-weight: 950 !important;
  opacity: 1 !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-status-dot {
  opacity: 1 !important;
  border: 1px solid rgba(23, 92, 211, 0.16) !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-active-pill,
section[data-testid="stSidebar"] .cpmm-sidebar-sub-active-pill {
  opacity: 1 !important;
  filter: none !important;
}

/* UI.COMMERCIAL4.3: sidebar project file actions and compact context. */
.cpmm-sidebar-context,
.cpmm-sidebar-file {
  border: 1px solid rgba(7, 55, 99, 0.22);
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
  padding: 0.74rem 0.76rem;
  box-shadow: 0 9px 22px rgba(7, 26, 51, 0.085);
  margin-top: 0.82rem;
}
.cpmm-sidebar-mini-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.12rem;
  padding: 0.28rem 0;
  border-bottom: 1px solid rgba(11, 58, 102, 0.09);
}
.cpmm-sidebar-mini-row:last-child { border-bottom: 0; }
.cpmm-sidebar-mini-label {
  color: #34536f !important;
  font-size: 0.62rem;
  font-weight: 950;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.cpmm-sidebar-mini-value {
  color: #061b35 !important;
  font-size: 0.78rem;
  font-weight: 900;
  line-height: 1.18;
  overflow-wrap: anywhere;
}
.cpmm-sidebar-file-note {
  color: #526f8d !important;
  font-size: 0.70rem;
  line-height: 1.25;
  margin: 0.18rem 0 0.42rem 0;
  font-weight: 650;
}
section[data-testid="stSidebar"] div[data-testid="stDownloadButton"] button {
  background: linear-gradient(135deg, #1d6fe7, #175cd3) !important;
  border-color: #1d6fe7 !important;
  color: #ffffff !important;
}
section[data-testid="stSidebar"] div[data-testid="stDownloadButton"] button p,
section[data-testid="stSidebar"] div[data-testid="stDownloadButton"] button span {
  color: #ffffff !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] {
  border: 1px dashed rgba(11, 58, 102, 0.28) !important;
  border-radius: 12px !important;
  background: rgba(255,255,255,0.82) !important;
  padding: 0.28rem !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] label,
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] small {
  color: #0b3a66 !important;
  font-weight: 750 !important;
}


/* UI.COMMERCIAL4.3.1: sidebar text contrast hotfix.
   Override the older global sidebar ink rule with higher-specificity selectors
   for the new light commercial rail panels. */
section[data-testid="stSidebar"] .cpmm-sidebar-brand,
section[data-testid="stSidebar"] .cpmm-sidebar-status,
section[data-testid="stSidebar"] .cpmm-sidebar-context,
section[data-testid="stSidebar"] .cpmm-sidebar-file {
  opacity: 1 !important;
  filter: none !important;
  color: #061b35 !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-brand *,
section[data-testid="stSidebar"] .cpmm-sidebar-status *,
section[data-testid="stSidebar"] .cpmm-sidebar-context *,
section[data-testid="stSidebar"] .cpmm-sidebar-file * {
  opacity: 1 !important;
  filter: none !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-brand-title,
section[data-testid="stSidebar"] .cpmm-sidebar-status-value,
section[data-testid="stSidebar"] .cpmm-sidebar-mini-value {
  color: #061b35 !important;
  font-weight: 950 !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-brand-subtitle,
section[data-testid="stSidebar"] .cpmm-sidebar-file-note {
  color: #243b53 !important;
  font-weight: 750 !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-section-label,
section[data-testid="stSidebar"] .cpmm-sidebar-status-title,
section[data-testid="stSidebar"] .cpmm-sidebar-mini-label {
  color: #0b3a66 !important;
  font-weight: 950 !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-context,
section[data-testid="stSidebar"] .cpmm-sidebar-file {
  background: linear-gradient(180deg, #ffffff 0%, #f2f8ff 100%) !important;
  border: 1px solid rgba(7, 55, 99, 0.34) !important;
  box-shadow: 0 12px 26px rgba(7, 26, 51, 0.12) !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-mini-row {
  border-bottom: 1px solid rgba(11, 58, 102, 0.18) !important;
}
section[data-testid="stSidebar"] .cpmm-sidebar-mini-row:last-child {
  border-bottom: 0 !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] {
  background: #ffffff !important;
  border: 1px dashed rgba(7, 55, 99, 0.46) !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] *,
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] p,
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] small,
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] label {
  color: #0b3a66 !important;
  opacity: 1 !important;
  font-weight: 800 !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] button {
  color: #0b3a66 !important;
  background: #f8fbff !important;
  border-color: #a9c4df !important;
  font-weight: 900 !important;
}

.cpmm-top-brand-shell {
  border: 1px solid rgba(11, 58, 102, 0.11);
  border-radius: 18px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fbff 56%, #eef6ff 100%);
  padding: 0.82rem 1.02rem;
  margin: 0.20rem 0 0.82rem 0;
  box-shadow: 0 10px 30px rgba(7, 26, 51, 0.065);
}
.cpmm-top-brand-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.86rem;
}
.cpmm-top-brand-logo {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: linear-gradient(135deg, #0b3a66, #1d6fe7);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  font-weight: 950;
  box-shadow: 0 8px 18px rgba(29, 111, 231, 0.20);
}
.cpmm-top-brand-title {
  color: #071a33;
  font-size: 1.36rem;
  font-weight: 950;
  line-height: 1.12;
}
.cpmm-top-brand-subtitle {
  color: #526f8d;
  font-size: 0.82rem;
  line-height: 1.30;
  margin-top: 0.18rem;
}
.cpmm-top-brand-badge {
  border: 1px solid rgba(29, 111, 231, 0.20);
  border-radius: 999px;
  background: #e8f1ff;
  color: #0b3a66;
  padding: 0.28rem 0.72rem;
  font-size: 0.70rem;
  font-weight: 950;
  letter-spacing: 0.055em;
  text-transform: uppercase;
}
.cpmm-context-summary-shell {
  border: 1px solid rgba(11, 58, 102, 0.10);
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 8px 22px rgba(7, 26, 51, 0.055);
  padding: 0.72rem 0.82rem;
  margin: 0.35rem 0 0.80rem 0;
}
.cpmm-context-summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.50rem;
}
.cpmm-context-summary-item {
  border-right: 1px solid #e3eaf3;
  padding: 0.12rem 0.66rem;
  min-width: 0;
}
.cpmm-context-summary-item:last-child { border-right: 0; }
.cpmm-context-summary-label {
  color: #526f8d;
  font-size: 0.66rem;
  font-weight: 950;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 0.16rem;
}
.cpmm-context-summary-value {
  color: #071a33;
  font-size: 0.86rem;
  font-weight: 900;
  line-height: 1.22;
  overflow-wrap: anywhere;
}
@media (max-width: 1100px) {
  .cpmm-context-summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .cpmm-context-summary-item { border-right: 0; border-bottom: 1px solid #e3eaf3; padding-bottom: 0.42rem; }
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



def _commercial_workspace_icon(workspace: str) -> str:
    return {
        "Setup": "⚙",
        "Sections": "▦",
        "Loads": "⇩",
        "Analysis": "⌁",
        "Results": "▤",
    }.get(str(workspace), "•")


def _commercial_subpage_icon(subpage: str) -> str:
    return {
        "Project": "▣",
        "Materials": "⚗",
        "Section Builder": "◇",
        "Rebar": "#",
        "Prestress": "PT",
        "ULS Strength": "ULS",
        "SLS / Stress & Cracking": "SLS",
        "SLS Deflection / Camber": "δ",
        "Report / QA": "QA",
    }.get(str(subpage), "•")


def _analysis_mode_from_session_for_chrome() -> AnalysisModeSettings:
    value = st.session_state.get("analysis_mode_settings")
    if isinstance(value, AnalysisModeSettings):
        return value
    if isinstance(value, dict):
        try:
            return AnalysisModeSettings.model_validate(value)
        except Exception:
            return AnalysisModeSettings()
    return AnalysisModeSettings()


def _current_section_label_for_chrome() -> str:
    return str(st.session_state.get("section_preset_name") or st.session_state.get("section_preset_selector_key") or "Not selected")


def _project_code_label_for_chrome() -> str:
    code = str(st.session_state.get("design_code") or st.session_state.get("project_design_code") or "ACI 318")
    edition = str(st.session_state.get("code_edition") or st.session_state.get("project_code_edition") or "")
    return f"{code} {edition}".strip()


def _render_sidebar_active_context() -> None:
    """Render compact always-visible project context in the left rail."""
    mode = _analysis_mode_from_session_for_chrome()
    st.sidebar.markdown(
        f"""
<div class="cpmm-sidebar-context">
  <div class="cpmm-sidebar-section-label" style="margin-top:0;">Active Context</div>
  <div class="cpmm-sidebar-mini-row"><div class="cpmm-sidebar-mini-label">Workflow</div><div class="cpmm-sidebar-mini-value">{escape(analysis_mode_label(mode))}</div></div>
  <div class="cpmm-sidebar-mini-row"><div class="cpmm-sidebar-mini-label">Section</div><div class="cpmm-sidebar-mini-value">{escape(_current_section_label_for_chrome())}</div></div>
  <div class="cpmm-sidebar-mini-row"><div class="cpmm-sidebar-mini-label">Code</div><div class="cpmm-sidebar-mini-value">{escape(_project_code_label_for_chrome())}</div></div>
  <div class="cpmm-sidebar-mini-row"><div class="cpmm-sidebar-mini-label">Units</div><div class="cpmm-sidebar-mini-value">mm, MPa, N, N-mm</div></div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_sidebar_project_file_actions() -> None:
    """Move project-level save/load actions into the commercial sidebar.

    UI.COMMERCIAL4.3 keeps the existing JSON serialization/loading logic, but
    places file actions in the left rail where project-level actions belong.
    This is UI-only and does not change the project data model.
    """
    with st.sidebar.container(border=True):
        st.markdown('<div class="cpmm-sidebar-section-label" style="margin-top:0;">Project File</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="cpmm-sidebar-file-note">Save or load the complete project JSON before handoff or major edits.</div>',
            unsafe_allow_html=True,
        )
        project = project_from_session_state(st.session_state)
        st.download_button(
            "Save Project JSON",
            data=project_to_json(project),
            file_name="concrete_section_pro_project.json",
            mime="application/json",
            use_container_width=True,
            type="primary",
            key="ui_commercial4_3_sidebar_save_project_json",
        )
        uploaded_file = st.file_uploader(
            "Load Project JSON",
            type=["json"],
            key="ui_commercial4_3_sidebar_project_json_uploader",
        )
        if uploaded_file is not None and st.button(
            "Apply Loaded Project",
            use_container_width=True,
            type="primary",
            key="ui_commercial4_3_sidebar_apply_project_json",
        ):
            try:
                pending_json = uploaded_file.getvalue().decode("utf-8")
                project = project_from_json(pending_json)
                apply_project_to_session_state(project, st.session_state)
            except (UnicodeDecodeError, ProjectIOError) as exc:
                st.session_state["_project_load_error"] = str(exc)
            else:
                st.session_state["_project_load_success"] = (
                    "Project JSON loaded. Review Section Builder, Rebar, Prestress, and Loads tabs before future analysis."
                )
            rerun = getattr(st, "rerun", None)
            if callable(rerun):
                rerun()


def _render_commercial_sidebar(active_workspace: str | None = None) -> None:
    """Render a visual navigation rail without changing the existing page contracts.

    UI.COMMERCIAL4 keeps the top navigation available for backward
    compatibility, but adds a premium sidebar rail that writes to the same
    Streamlit session-state navigation keys when used.
    """
    if st.session_state.get("_nav_active_workspace") not in WORKSPACE_NAVIGATION:
        st.session_state["_nav_active_workspace"] = "Setup"
    active = str(active_workspace or st.session_state.get("_nav_active_workspace", "Setup"))

    st.sidebar.markdown(
        """
<div class="cpmm-sidebar-brand">
  <div class="cpmm-sidebar-brand-title">Concrete Section Pro</div>
  <div class="cpmm-sidebar-brand-subtitle">Concrete section analysis and design-review workspace.</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown('<div class="cpmm-sidebar-section-label">Workspace</div>', unsafe_allow_html=True)
    for workspace in WORKSPACE_NAVIGATION:
        if workspace == active:
            st.sidebar.markdown(
                f'<div class="cpmm-sidebar-active-pill"><span>{_commercial_workspace_icon(workspace)}</span><span>{workspace}</span></div>',
                unsafe_allow_html=True,
            )
        else:
            if st.sidebar.button(f"{_commercial_workspace_icon(workspace)}  {workspace}", key=f"_sidebar_workspace_{workspace}", use_container_width=True):
                st.session_state["_nav_active_workspace"] = workspace
                rerun = getattr(st, "rerun", None)
                if callable(rerun):
                    rerun()

    subpages = WORKSPACE_NAVIGATION.get(active, [])
    if len(subpages) > 1:
        subpage_key = {
            "Setup": "_nav_setup_subpage",
            "Sections": "_nav_sections_subpage",
            "Analysis": "_nav_analysis_subpage",
        }.get(active)
        if subpage_key:
            if st.session_state.get(subpage_key) not in subpages:
                st.session_state[subpage_key] = subpages[0]
            active_subpage = str(st.session_state.get(subpage_key, subpages[0]))
            st.sidebar.markdown('<div class="cpmm-sidebar-section-label">Subpage</div>', unsafe_allow_html=True)
            for subpage in subpages:
                if subpage == active_subpage:
                    st.sidebar.markdown(
                        f'<div class="cpmm-sidebar-sub-active-pill"><span>{_commercial_subpage_icon(subpage)}</span><span>{subpage}</span></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    if st.sidebar.button(f"{_commercial_subpage_icon(subpage)}  {subpage}", key=f"_sidebar_subpage_{active}_{subpage}", use_container_width=True):
                        st.session_state[subpage_key] = subpage
                        rerun = getattr(st, "rerun", None)
                        if callable(rerun):
                            rerun()

    dirty_status = current_project_dirty_status(st.session_state)
    model_dot = "warning" if dirty_status.model_status == "Modified" else "ready"
    analysis_dot = "warning" if dirty_status.analysis_status == "Out of date" else ("ready" if dirty_status.analysis_status == "Current" else "")
    affected_count = len(dirty_status.affected_checks)
    st.sidebar.markdown(
        f"""
<div class="cpmm-sidebar-status">
  <div class="cpmm-sidebar-section-label" style="margin-top:0;">Project Status</div>
  <div class="cpmm-sidebar-status-row">
    <span class="cpmm-sidebar-status-dot {model_dot}">●</span>
    <div><div class="cpmm-sidebar-status-title">Model</div><div class="cpmm-sidebar-status-value">{escape(dirty_status.model_status)}</div></div>
  </div>
  <div class="cpmm-sidebar-status-row">
    <span class="cpmm-sidebar-status-dot {analysis_dot}">●</span>
    <div><div class="cpmm-sidebar-status-title">Analysis</div><div class="cpmm-sidebar-status-value">{escape(dirty_status.analysis_status)}</div></div>
  </div>
  <div class="cpmm-sidebar-status-row">
    <span class="cpmm-sidebar-status-dot">{affected_count}</span>
    <div><div class="cpmm-sidebar-status-title">Affected Checks</div><div class="cpmm-sidebar-status-value">{escape(', '.join(dirty_status.affected_checks[:2]) if dirty_status.affected_checks else 'None')}</div></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    _render_sidebar_active_context()
    _render_sidebar_project_file_actions()


def _render_commercial_brand_header(active_workspace: str) -> None:
    st.markdown(
        f"""
<div class="cpmm-top-brand-shell">
  <div class="cpmm-top-brand-row">
    <div class="cpmm-top-brand-logo">CS</div>
    <div>
      <div class="cpmm-top-brand-title">Concrete Section Pro</div>
      <div class="cpmm-top-brand-subtitle">Professional concrete section analysis and design-review workspace · Internal units: mm, MPa, N, N-mm.</div>
    </div>
    <div class="cpmm-top-brand-badge">{escape(active_workspace)} Workspace</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_engineering_context_summary(active_workspace: str) -> None:
    mode = _analysis_mode_from_session_for_chrome()
    section_label = _current_section_label_for_chrome()
    code_label = _project_code_label_for_chrome()
    st.markdown(
        f"""
<div class="cpmm-context-summary-shell">
  <div class="cpmm-context-summary-grid">
    <div class="cpmm-context-summary-item"><div class="cpmm-context-summary-label">Workspace</div><div class="cpmm-context-summary-value">{escape(active_workspace)}</div></div>
    <div class="cpmm-context-summary-item"><div class="cpmm-context-summary-label">Active Workflow</div><div class="cpmm-context-summary-value">{escape(analysis_mode_label(mode))}</div></div>
    <div class="cpmm-context-summary-item"><div class="cpmm-context-summary-label">Section Type / Preset</div><div class="cpmm-context-summary-value">{escape(section_label)}</div></div>
    <div class="cpmm-context-summary-item"><div class="cpmm-context-summary-label">Design Code</div><div class="cpmm-context-summary-value">{escape(code_label)}</div></div>
    <div class="cpmm-context-summary-item"><div class="cpmm-context-summary-label">Units</div><div class="cpmm-context-summary-value">mm, MPa, N, N-mm</div></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

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
    st.set_page_config(page_title="Concrete Section Pro", layout="wide", initial_sidebar_state="expanded")
    _render_global_commercial_tab_styles()
    install_streamlit_plotly_readability_patch(st)
    # Keep the canonical Streamlit title call for brand continuity and tests;
    # the premium app shell below carries the visible commercial header.
    st.title("Concrete Section Pro")
    st.caption(
        "Concrete section analysis and design-review workspace. "
        "Internal units: mm, MPa, N, N-mm."
    )

    update_dirty_state_from_session(st.session_state)

    if st.session_state.get("_nav_active_workspace") not in WORKSPACE_NAVIGATION:
        st.session_state["_nav_active_workspace"] = "Setup"
    _render_commercial_sidebar(str(st.session_state.get("_nav_active_workspace", "Setup")))
    _render_commercial_brand_header(str(st.session_state.get("_nav_active_workspace", "Setup")))

    active_workspace = _safe_choice(
        "Workspace",
        list(WORKSPACE_NAVIGATION.keys()),
        key="_nav_active_workspace",
    )
    _render_engineering_context_summary(active_workspace)
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
