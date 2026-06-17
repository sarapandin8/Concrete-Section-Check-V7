from __future__ import annotations

import pytest

from concrete_pmm_pro.core.models import ConcreteMaterial
from concrete_pmm_pro.ui import analysis_page


def _with_session_state(values: dict[str, object]):
    state = analysis_page.st.session_state
    backup = dict(state)
    state.clear()
    state.update(values)
    return state, backup


def _restore_session_state(backup: dict[str, object]) -> None:
    state = analysis_page.st.session_state
    state.clear()
    state.update(backup)


def test_railway_u_girder_sls_limit_strength_routes_transfer_to_web_fci() -> None:
    state, backup = _with_session_state(
        {
            "section_preset_key": "railway_u_girder",
            "concrete_material": ConcreteMaterial(name="C45_PRECAST", fc_MPa=45.0, density_kg_m3=2400.0),
            "railway_u_girder_stage_settings": {
                "web_fc_MPa": 45.0,
                "web_fci_MPa": 36.0,
                "slab_fc_MPa": 35.0,
            },
        }
    )
    try:
        transfer = analysis_page._stage_material_strength_values_for_sls_limit_preview("Transfer stage")
        construction = analysis_page._stage_material_strength_values_for_sls_limit_preview("Construction stage")
        service = analysis_page._stage_material_strength_values_for_sls_limit_preview("Service stage")

        assert transfer["strength_MPa"] == pytest.approx(36.0)
        assert "web f'ci" in str(transfer["strength_label"])
        assert "not web final f'c" in str(transfer["audit_note"])
        assert construction["strength_MPa"] == pytest.approx(45.0)
        assert "pre-composite" in str(construction["strength_label"])
        assert service["strength_MPa"] == pytest.approx(45.0)
        assert "CIP slab f'c = 35.000 MPa" in str(service["audit_note"])
    finally:
        _restore_session_state(backup)


def test_generic_prestressed_girder_transfer_uses_fci_not_final_fc() -> None:
    _state, backup = _with_session_state(
        {
            "section_preset_key": "parametric_i_girder",
            "concrete_material": ConcreteMaterial(name="C45_PRECAST", fc_MPa=45.0, density_kg_m3=2400.0),
            "girder_prestress_system_settings": {"fci_MPa": 36.0},
        }
    )
    try:
        transfer = analysis_page._stage_material_strength_values_for_sls_limit_preview("Transfer stage")
        service = analysis_page._stage_material_strength_values_for_sls_limit_preview("Service stage")

        assert transfer["strength_MPa"] == pytest.approx(36.0)
        assert "f'ci" in str(transfer["strength_label"])
        assert "primary f'c = 45.000 MPa" in str(transfer["audit_note"])
        assert service["strength_MPa"] == pytest.approx(45.0)
    finally:
        _restore_session_state(backup)


def test_stage_strength_routing_is_threaded_into_analysis_page_source() -> None:
    from pathlib import Path

    source = Path("concrete_pmm_pro/ui/analysis_page.py").read_text(encoding="utf-8")
    assert "SLS.MATERIAL.ROUTING1" in source
    assert "web f'ci at transfer / release" in source
    assert "_stage_material_strength_values_for_sls_limit_preview(locked_stage_label or stage)" in source
    assert "must not reuse a stale service f'c" in source
