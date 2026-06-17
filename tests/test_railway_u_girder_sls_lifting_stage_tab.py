from __future__ import annotations

import pytest

from concrete_pmm_pro.core.models import ConcreteMaterial
from concrete_pmm_pro.geometry.generators import railway_u_girder
from concrete_pmm_pro.ui import analysis_page
from concrete_pmm_pro.ui.prestress_page import _default_girder_strand_layout_table


def _railway_geometry():
    return railway_u_girder(
        width_mm=5500,
        depth_mm=1600,
        top_wall_width_mm=600,
        bottom_side_width_mm=650,
        haunch_x_mm=300,
        haunch_y_mm=300,
        h1_step_height_mm=670,
        h2_bottom_opening_mm=305,
        h3_floor_side_thickness_mm=395,
        h4_floor_center_thickness_mm=450,
    )


def _with_session_state(values: dict[str, object]):
    state = analysis_page.st.session_state
    backup = dict(state)
    state.clear()
    state.update(values)
    return backup


def _restore_session_state(backup: dict[str, object]) -> None:
    state = analysis_page.st.session_state
    state.clear()
    state.update(backup)


def test_railway_u_girder_analysis_tabs_include_lifting_stage_only_for_railway() -> None:
    geom = _railway_geometry()
    backup = _with_session_state(
        {
            "section_preset_key": "railway_u_girder",
            "section_geometry": geom,
            "railway_u_girder_stage_settings": {
                "web_fc_MPa": 45.0,
                "web_fci_MPa": 36.0,
                "slab_fc_MPa": 35.0,
                "construction_method": "Case B - wet slab carried by precast webs",
            },
        }
    )
    try:
        labels = [label for _key, label, _note in analysis_page._beam_sls_stage_tab_specs()]
        assert labels == ["Transfer stage", "Lifting stage", "Construction stage", "Service stage"]
    finally:
        _restore_session_state(backup)

    backup = _with_session_state({"section_preset_key": "parametric_i_girder"})
    try:
        labels = [label for _key, label, _note in analysis_page._beam_sls_stage_tab_specs()]
        assert labels == ["Transfer stage", "Construction stage", "Service stage"]
    finally:
        _restore_session_state(backup)


def test_lifting_stage_uses_transfer_strength_profile_for_railway_u_girder() -> None:
    geom = _railway_geometry()
    backup = _with_session_state(
        {
            "section_preset_key": "railway_u_girder",
            "section_geometry": geom,
            "concrete_material": ConcreteMaterial(name="C45_PRECAST", fc_MPa=45.0, density_kg_m3=2400.0),
            "railway_u_girder_stage_settings": {
                "web_fc_MPa": 45.0,
                "web_fci_MPa": 36.0,
                "slab_fc_MPa": 35.0,
                "construction_method": "Case B - wet slab carried by precast webs",
            },
        }
    )
    try:
        assert analysis_page._beam_sls_stage_label_for_analysis("Temporary lifting") == "Lifting stage"
        lifting = analysis_page._stage_material_strength_values_for_sls_limit_preview("Lifting stage")
        assert lifting["strength_MPa"] == pytest.approx(36.0)
        assert "web f'ci" in str(lifting["strength_label"])
    finally:
        _restore_session_state(backup)


def test_railway_u_girder_lifting_stage_full_length_rows_use_one_web_lifting_basis() -> None:
    geom = _railway_geometry()
    strand_table = _default_girder_strand_layout_table(geom)
    backup = _with_session_state(
        {
            "section_preset_key": "railway_u_girder",
            "section_geometry": geom,
            "girder_strand_layout_table": strand_table,
            "railway_u_girder_stage_settings": {
                "span_length_m": 10.0,
                "web_fc_MPa": 45.0,
                "web_fci_MPa": 36.0,
                "slab_fc_MPa": 35.0,
                "concrete_unit_weight_kN_m3": 24.0,
                "wet_slab_distribution_each_web": 0.5,
                "formwork_construction_load_kN_m2": 2.5,
                "lifting_point_ratio": 0.20,
                "lifting_impact_factor": 1.10,
                "construction_method": "Case B - wet slab carried by precast webs",
            },
        }
    )
    try:
        df = analysis_page._girder_full_length_sls_stage_rows(
            stage_label="Lifting stage",
            load_rows=[],
            basis_options=object(),
            basis_names=[],
            span_length_m=10.0,
        )
        assert not df.empty
        assert set(df["Stage"]) == {"Lifting stage"}
        assert set(df["Basis"]) == {"Railway U-Girder one-web lifting section"}
        assert df["Auto load components"].astype(str).str.contains("two-point lifting").any()
        # Two-point lifting produces a negative overhang moment at the lifting point
        # and a positive midspan moment; a simple-span Transfer tab would not.
        row_at_lift = df.iloc[(df["Station x (m)"] - 2.0).abs().argsort()[:1]]
        row_at_mid = df.iloc[(df["Station x (m)"] - 5.0).abs().argsort()[:1]]
        assert float(row_at_lift["Auto Mx (kN-m)"].iloc[0]) < 0.0
        assert float(row_at_mid["Auto Mx (kN-m)"].iloc[0]) > 0.0
        assert float(df["Pe stage (kN)"].max()) > 0.0
    finally:
        _restore_session_state(backup)
