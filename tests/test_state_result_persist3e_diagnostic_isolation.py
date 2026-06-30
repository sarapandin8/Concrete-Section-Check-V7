from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "concrete_pmm_pro" / "ui" / "analysis_page.py"
TEXT = SOURCE.read_text(encoding="utf-8")


def test_flexure_diagnostic_uses_separate_result_key():
    assert "_BEAM_ULS_FLEXURE_DIAGNOSTIC_RESULT_KEY" in TEXT
    assert "beam_girder_uls_flexure_diagnostic_result" in TEXT


def test_flexure_diagnostic_skips_production_cache_write():
    assert "diagnostic_flexure_run" in TEXT
    assert "production_cache_write\"] = \"disabled\"" in TEXT
    assert "production_cache_write=\"skipped\"" in TEXT
    assert "_beam_uls_store_manual_result(" in TEXT


def test_flexure_diagnostic_hides_production_workspace():
    assert "flexure_diagnostic_mode_active" in TEXT
    assert "selected_entry is None or flexure_diagnostic_mode_active" in TEXT
    assert "_render_beam_uls_flexure_diagnostic_output" in TEXT
    assert "not written to the production ULS cache" in TEXT


def test_flexure_diagnostic_skips_endpoint_boundary_rows():
    assert "diagnostic_endpoint_rows_skipped" in TEXT
