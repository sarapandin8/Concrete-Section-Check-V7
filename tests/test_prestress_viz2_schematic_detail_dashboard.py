from __future__ import annotations

import sys
import types
from pathlib import Path

import pandas as pd

SOURCE = Path("concrete_pmm_pro/ui/prestress_page.py").read_text(encoding="utf-8")


def _function_source(name: str) -> str:
    start = SOURCE.index(f"def {name}")
    end = SOURCE.index("\n\ndef ", start + 1)
    return SOURCE[start:end]


def test_cross_section_layout_is_overall_schematic_not_single_clutter_plot() -> None:
    body = _function_source("_plot_girder_strand_cross_section_layout")

    assert "Overall section schematic" in body
    assert "Strand row summary" not in body
    assert "fig.add_annotation" not in body or "strand block" in body
    assert "_add_strand_state_marker_traces" in body
    assert "marker_size=7" in body
    assert "type=\"rect\"" in body


def test_dashboard_renderer_splits_overall_summary_and_detail_panels() -> None:
    body = _function_source("_render_girder_strand_cross_section_dashboard")

    assert "Split dashboard" in body
    assert "Strand row summary" in body
    assert "Zoomed strand block detail" in body
    assert "_plot_girder_strand_block_detail" in body
    assert "displayModeBar" in body


def test_detail_panel_uses_large_markers_and_no_row_summary_annotation() -> None:
    body = _function_source("_plot_girder_strand_block_detail")

    assert "marker_size=14" in body
    assert "ticktext" in body
    assert "Strand row summary" not in body


def test_row_summary_combines_symmetric_railway_rows(monkeypatch) -> None:
    st = types.ModuleType("streamlit")
    st.session_state = {}
    st.column_config = types.SimpleNamespace(
        CheckboxColumn=lambda *args, **kwargs: None,
        TextColumn=lambda *args, **kwargs: None,
        NumberColumn=lambda *args, **kwargs: None,
        SelectboxColumn=lambda *args, **kwargs: None,
    )
    monkeypatch.setitem(sys.modules, "streamlit", st)

    from concrete_pmm_pro.ui.prestress_page import (  # noqa: PLC0415
        _girder_strand_row_summary_dataframe,
        _normalize_girder_strand_layout_table,
    )

    raw = pd.DataFrame(
        [
            {
                "Active": True,
                "Group ID": "L Row 1",
                "Strand Size": "12.7 mm low-relaxation strand",
                "No. Strands": 9,
                "y_mm_from_bottom": 95.0,
                "Left debond m": 2.0,
                "Right debond m": 2.0,
                "Debonded strand nos": "1,9",
            },
            {
                "Active": True,
                "Group ID": "R Row 1",
                "Strand Size": "12.7 mm low-relaxation strand",
                "No. Strands": 9,
                "y_mm_from_bottom": 95.0,
                "Left debond m": 2.0,
                "Right debond m": 2.0,
                "Debonded strand nos": "1,9",
            },
        ]
    )
    table = _normalize_girder_strand_layout_table(raw, span_length_m=10.0)
    summary = _girder_strand_row_summary_dataframe(table, None)

    assert summary.shape[0] == 1
    assert summary.loc[0, "Row"] == "Row 1"
    assert summary.loc[0, "Total strands"] == 18
    assert summary.loc[0, "Bonded"] == 14
    assert summary.loc[0, "Debonded"] == 4
    assert summary.loc[0, "Left debond (m)"] == 2.0
    assert summary.loc[0, "Right debond (m)"] == 2.0
