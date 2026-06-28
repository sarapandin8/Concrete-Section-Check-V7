from __future__ import annotations

import math

import pytest

from concrete_pmm_pro.code_checks import aashto_combined_shear_torsion_result
from concrete_pmm_pro.core.analysis import AnalysisInput, AnalysisSettings
from concrete_pmm_pro.core.design_code import PROJECT_CODE_AASHTO_LRFD
from concrete_pmm_pro.core.models import ConcreteMaterial, LoadCase, Rebar, RebarMaterial
from concrete_pmm_pro.geometry.generators import rectangle
from concrete_pmm_pro.ui.analysis_page import (
    _column_pier_check_decision_rows,
    _column_pier_combined_vt_check_dataframe,
)


def _analysis_input() -> AnalysisInput:
    return AnalysisInput(
        section_geometry=rectangle(width_mm=600.0, height_mm=900.0),
        concrete_material=ConcreteMaterial(name="C45", fc_MPa=45.0, ecu=0.003),
        rebar_materials=[RebarMaterial(name="SD40", fy_MPa=420.0, Es_MPa=200000.0)],
        rebars=[
            Rebar(x_mm=-250.0, y_mm=-380.0, diameter_mm=25.0, material_name="SD40", label="B1"),
            Rebar(x_mm=250.0, y_mm=-380.0, diameter_mm=25.0, material_name="SD40", label="B2"),
            Rebar(x_mm=250.0, y_mm=380.0, diameter_mm=25.0, material_name="SD40", label="B3"),
            Rebar(x_mm=-250.0, y_mm=380.0, diameter_mm=25.0, material_name="SD40", label="B4"),
        ],
        prestress_elements=[],
        load_cases=[LoadCase(name="ULS-VT", Pu_N=1_200_000.0, Mux_Nmm=0.0, Muy_Nmm=0.0, load_type="ULS")],
        settings=AnalysisSettings(code=PROJECT_CODE_AASHTO_LRFD, transverse_reinforcement="tied"),
    )


def _state(*, tu_kNm: float = 50.0, spacing_mm: float = 100.0) -> dict[str, object]:
    return {
        "project_design_code": PROJECT_CODE_AASHTO_LRFD,
        "project_code_edition": "AASHTO LRFD 9th Edition",
        "design_code": "ACI 318",  # stale widget key must not control routing
        "code_edition": "ACI 318-19",
        "column_uls_loads_table": [
            {
                "Active": True,
                "Case Name": "ULS-VT",
                "Pu": 1_200.0,
                "Mux": 120.0,
                "Muy": 60.0,
                "Vux": 80.0,
                "Vuy": 50.0,
                "Tu": tu_kNm,
                "Note": "AASHTO.COL.VT1 regression",
            }
        ],
        "column_pier_transverse_reinforcement_settings": {
            "closed_tie_layout": "Closed ties / hoops",
            "torsion_core_basis": "Auto from section and tie offset",
            "tie_center_offset_mm": 50.0,
        },
        "column_pier_transverse_reinforcement_table": [
            {
                "Active": True,
                "Zone": "Control section",
                "x_start_m": 0.0,
                "x_end_m": 1.0,
                "Bar Size": "DB16",
                "Diameter_mm": 16.0,
                "Legs": 4.0,
                "Spacing_mm": spacing_mm,
                "fy_MPa": 420.0,
                "Note": "closed control section hoop",
            }
        ],
        "rebars": _analysis_input().rebars,
    }


def test_aashto_vt1_helper_combines_source_demands_in_si() -> None:
    vt = aashto_combined_shear_torsion_result(
        vu_N=80_000.0,
        tu_Nmm=50.0e6,
        phi=0.90,
        vc_N=250_000.0,
        phi_vn_N=500_000.0,
        phi_tn_Nmm=70.0e6,
        bv_mm=600.0,
        dv_mm=320.0,
        Ao_mm2=127_500.0,
        ph_mm=1_600.0,
        fy_MPa=420.0,
        avs_provided_mm2_per_mm=8.0,
        at_provided_mm2_per_mm=2.0,
        avs_minimum_mm2_per_mm=0.5,
    )

    assert vt.phi == pytest.approx(0.90)
    assert vt.theta_deg == pytest.approx(45.0)
    assert vt.torsion_required_mm2_per_mm > 0.0
    assert vt.combined_transverse_required_mm2_per_mm == pytest.approx(
        vt.shear_required_mm2_per_mm + 2.0 * vt.torsion_required_mm2_per_mm
    )
    assert vt.provided_av_plus_2at_mm2_per_mm == pytest.approx(12.0)
    assert "5.7.3.6.1" in vt.basis


def test_aashto_vt1_dataframe_routes_to_aashto_not_aci() -> None:
    vt_df = _column_pier_combined_vt_check_dataframe(_state(), _analysis_input())

    active = vt_df[vt_df["Status"].astype(str) != "NOT APPLICABLE"]
    assert not active.empty
    assert active["Code basis"].eq("AASHTO LRFD 9th Column/Pier V+T").all()
    assert not active["Notes"].str.contains("ACI 318", case=False, na=False).any()
    assert active["Interaction form"].str.contains("AASHTO 5.7.3.6.1", regex=False).all()
    assert set(active["Status"]).issubset({"PASS", "FAIL", "REVIEW", "DATA REQUIRED"})
    assert active["Provided Av+2At per s mm2/mm"].astype(float).gt(0.0).all()


def test_aashto_vt1_decision_view_no_longer_says_not_implemented() -> None:
    rows = _column_pier_check_decision_rows(_state(), _analysis_input())
    vt_row = next(row for row in rows if row["Check"] == "Shear + Torsion")

    assert "not implemented" not in vt_row["Route / Scope"].lower()
    assert "AASHTO LRFD 9th Section 5.7.3.6" in vt_row["Route / Scope"]


def test_aashto_vt1_threshold_row_uses_source_shear_gate() -> None:
    vt_df = _column_pier_combined_vt_check_dataframe(_state(tu_kNm=0.01), _analysis_input())
    active = vt_df[vt_df["Status"].astype(str) != "NOT APPLICABLE"]

    assert not active.empty
    assert active["Source torsion status"].eq("BELOW THRESHOLD").all()
    assert active["Interaction form"].eq("torsion below threshold").all()
