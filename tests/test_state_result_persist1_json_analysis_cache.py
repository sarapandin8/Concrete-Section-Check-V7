from __future__ import annotations

import pandas as pd

from concrete_pmm_pro.core.analysis import AnalysisModeSettings
from concrete_pmm_pro.core.concrete_materials import c45_precast_material
from concrete_pmm_pro.core.models import LoadCase
from concrete_pmm_pro.geometry.generators import rectangle
from concrete_pmm_pro.io.project_io import (
    ANALYSIS_RESULTS_METADATA_KEY,
    apply_project_to_session_state,
    project_from_json,
    project_from_session_state,
    project_to_json,
)
from concrete_pmm_pro.state.dirty_state import ANALYSIS_STATUS_KEY


def _railway_session() -> dict[str, object]:
    return {
        "project_name": "Railway saved cache",
        "design_code": "AASHTO LRFD",
        "code_edition": "AASHTO LRFD 9th Edition",
        "section_preset_key": "railway_u_girder",
        "section_preset_name": "Railway U-Girder",
        "section_category": "Precast Composite Girder",
        "girder_section_family": "precast_composite_girder",
        "section_parameters": {"B_mm": 5500.0, "H_mm": 1600.0},
        "section_geometry": rectangle(width_mm=5500.0, height_mm=1600.0),
        "concrete_material": c45_precast_material(),
        "load_cases": [LoadCase(name="Strength I", Pu_N=0.0, Mux_Nmm=100_000_000.0, Muy_Nmm=0.0)],
        "analysis_mode_settings": AnalysisModeSettings(member_type="beam_girder"),
    }


def test_project_json_restores_beam_girder_uls_and_sls_result_handoff_tables() -> None:
    session = _railway_session()
    session["_beam_girder_uls_manual_calculation_cache"] = {
        "Shear": {
            "input_hash": "shear-current-hash",
            "check": "Shear",
            "calculated_at": "2026-06-30 10:00:00",
            "shear_preview_df": pd.DataFrame(
                [
                    {
                        "Status": "FAIL",
                        "Case": "Strength I",
                        "Governing x": "7.000 m",
                        "Demand": "805.09 kN",
                        "Capacity": "φVn = 1,908.64 kN",
                        "Utilization": "Strength D/C 0.422; Av/s min D/C 1.893",
                        "Strength D/C value": 0.422,
                    }
                ]
            ),
        }
    }
    session["result_summary_beam_girder_sls_stage_summary_df"] = pd.DataFrame(
        [
            {
                "Module": "SLS Stress",
                "Check": "Beam/Girder stage stress",
                "Status": "Preview FAIL",
                "Governing Case": "AUTO-LIFT",
                "Station / Point": "2.000 m / Top",
                "D/C / Util.": 3.077,
            }
        ]
    )
    session["result_summary_beam_girder_sls_demand_detail_df"] = pd.DataFrame(
        [{"Stage": "Lifting stage", "Demand": "Tension 4.246 MPa", "Limit": "3.480 MPa"}]
    )
    session["result_summary_beam_girder_lifting_audit_df"] = pd.DataFrame(
        [{"Station x (m)": 2.0, "Effective strands": 50, "Audit note": "Row 1 debond termination"}]
    )
    session["result_summary_beam_girder_sls_code_label"] = "AASHTO LRFD 9th Edition"
    session["result_summary_beam_girder_sls_cache_hash"] = "sls-stage-hash"

    project = project_from_session_state(session)
    metadata = project.metadata[ANALYSIS_RESULTS_METADATA_KEY]
    assert "beam_girder_uls_manual_calculation_cache" in metadata
    assert "beam_girder_sls_result_handoff" in metadata

    restored: dict[str, object] = {}
    apply_project_to_session_state(project_from_json(project_to_json(project)), restored)

    cache = restored.get("_beam_girder_uls_manual_calculation_cache")
    assert isinstance(cache, dict)
    assert cache["Shear"]["shear_preview_df"].iloc[0]["Status"] == "FAIL"
    assert restored["result_summary_beam_girder_sls_stage_summary_df"].iloc[0]["Status"] == "Preview FAIL"
    assert restored["result_summary_beam_girder_lifting_audit_df"].iloc[0]["Effective strands"] == 50
    assert restored["result_summary_beam_girder_sls_code_label"] == "AASHTO LRFD 9th Edition"
    assert restored[ANALYSIS_STATUS_KEY] == "Current"


def test_project_json_restores_column_pier_vt_result_handoff() -> None:
    session = _railway_session()
    session["analysis_mode_settings"] = AnalysisModeSettings(member_type="column_pier_pmm")
    session["column_pier_combined_vt_result_df"] = pd.DataFrame(
        [
            {
                "Status": "FAIL",
                "Case": "ULS-02",
                "Direction": "Vux",
                "Vu kN": 80.0,
                "Tu kN-m": 75.0,
                "Overall D/C value": 1.111,
            }
        ]
    )
    session["column_pier_combined_vt_screen_df"] = pd.DataFrame(
        [{"Status": "FAIL", "Case": "ULS-02", "Dir": "Vux", "D/C": 1.111}]
    )
    session["column_pier_combined_vt_controlling_cause"] = "source torsion strength + source/stress gate"
    session["column_pier_combined_vt_governing_label"] = "ULS-02 / Vux"
    session["column_pier_combined_vt_route_label"] = "AASHTO 5.7.3.6"

    restored: dict[str, object] = {}
    apply_project_to_session_state(project_from_json(project_to_json(project_from_session_state(session))), restored)

    vt_df = restored.get("column_pier_combined_vt_result_df")
    assert isinstance(vt_df, pd.DataFrame)
    assert vt_df.iloc[0]["Status"] == "FAIL"
    assert restored["column_pier_combined_vt_governing_label"] == "ULS-02 / Vux"
    assert restored["column_pier_vt_runtime_cache_status"] == "Loaded cached Column/Pier V+T result"


def test_project_file_save_renders_after_workspace_cache_updates() -> None:
    source = open("app.py", encoding="utf-8").read()
    assert "STATE.RESULT.PERSIST1/PERSIST3B: render Project JSON download after the" in source
    sidebar_fn_start = source.index("def _render_commercial_sidebar")
    sidebar_fn_end = source.index("def _render_commercial_brand_header")
    main_workspace_block = source[source.index("def main") :]

    assert "_render_sidebar_project_file_actions()" not in source[sidebar_fn_start:sidebar_fn_end]
    assert "_render_sidebar_project_load_actions()" in main_workspace_block
    assert "_render_sidebar_project_save_actions()" in main_workspace_block
    assert main_workspace_block.index("_render_sidebar_project_load_actions()") < main_workspace_block.index("render_analysis_workspace()")
    assert main_workspace_block.index("render_analysis_workspace()") < main_workspace_block.index("_render_sidebar_project_save_actions()")


def test_project_file_load_renders_before_workspace_widgets_to_avoid_streamlit_state_error() -> None:
    source = open("app.py", encoding="utf-8").read()
    main_workspace_block = source[source.index("def main") :]

    assert "Project load must be handled before workspace widgets" in main_workspace_block
    assert main_workspace_block.index("_render_sidebar_project_load_actions()") < main_workspace_block.index("active_workspace = _safe_choice")
    assert main_workspace_block.index("_render_sidebar_project_load_actions()") < main_workspace_block.index("render_setup_workspace()")
