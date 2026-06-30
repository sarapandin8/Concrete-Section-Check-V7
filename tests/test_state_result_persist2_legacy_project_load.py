from __future__ import annotations

import json

from concrete_pmm_pro.core.analysis import AnalysisModeSettings
from concrete_pmm_pro.io.project_io import project_from_json, apply_project_to_session_state


def test_project_from_json_accepts_legacy_bridge_workflow_member_label() -> None:
    old_project = {
        "project_name": "Old Railway U-Girder",
        "version": None,
        "design_code": "AASHTO LRFD 9th Edition",
        "analysis_mode_settings": {
            "member_type": "Bridge Beam / Girder — RC / Prestressed Member",
            "analysis_workflow": "Bridge Beam / Girder",
        },
        "section_preset_key": "railway_u_girder",
        "section_preset_name": "Railway U-Girder",
        "section_parameters": {"B_mm": 5500.0, "H_mm": 1600.0},
        "loads": [
            {"name": "Strength I", "Pu_N": 0.0, "Mux_Nmm": 1.0, "Muy_Nmm": 0.0, "active": "true"}
        ],
        "metadata": {"legacy_note": "file saved before result-cache persistence"},
    }

    project = project_from_json(json.dumps(old_project))

    assert isinstance(project.analysis_mode_settings, AnalysisModeSettings)
    assert project.analysis_mode_settings.member_type == "beam_girder"
    assert project.code == "AASHTO LRFD"
    assert project.code_edition == "AASHTO LRFD 9th Edition"
    assert project.loads[0].active is True


def test_apply_legacy_project_without_analysis_results_loads_as_not_run_not_crash() -> None:
    old_project = {
        "project_name": "Old input-only file",
        "design_code": "AASHTO LRFD",
        "analysis_mode_settings": {"member_type": "bridge_beam_girder"},
        "section_preset_key": "railway_u_girder",
        "section_preset_name": "Railway U-Girder",
        "metadata": {},
    }
    restored: dict[str, object] = {}

    apply_project_to_session_state(project_from_json(json.dumps(old_project)), restored)

    assert restored["analysis_mode_settings"].member_type == "beam_girder"
    assert restored["_perf_analysis_status"] == "Not run"
    assert restored["project_metadata"] == {}
