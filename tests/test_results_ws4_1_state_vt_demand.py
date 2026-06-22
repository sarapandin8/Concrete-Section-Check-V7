from __future__ import annotations

from pathlib import Path


SOURCE = Path("app.py").read_text(encoding="utf-8")


def test_results_overall_state_does_not_claim_full_results_when_sls_missing() -> None:
    assert '"title": "ULS complete / SLS pending"' in SOURCE
    assert "All Beam/Girder ULS checks have stored results. SLS serviceability is not calculated yet." in SOURCE
    assert '"title": "Full stored results available"' not in SOURCE


def test_results_ready_state_uses_stored_uls_sls_summaries_wording() -> None:
    assert '"title": "Stored ULS/SLS summaries available"' in SOURCE


def test_results_shear_torsion_demand_display_includes_vu_tu_units() -> None:
    assert 'if check_name == "Shear + Torsion":' in SOURCE
    assert 'return f"Vu = {_results_scalar(vu)} kN; Tu = {_results_scalar(tu)} kN-m"' in SOURCE


def test_results_torsion_demand_display_includes_tu_unit() -> None:
    assert 'return "-" if tu == "-" else f"Tu = {_results_scalar(tu)} kN-m"' in SOURCE
