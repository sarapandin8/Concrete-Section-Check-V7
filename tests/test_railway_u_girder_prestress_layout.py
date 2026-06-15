from __future__ import annotations

import pandas as pd


def _install_streamlit_stub(monkeypatch):
    import sys
    import types

    st = types.ModuleType("streamlit")
    st.session_state = {}
    st.column_config = types.SimpleNamespace(
        CheckboxColumn=lambda *args, **kwargs: None,
        TextColumn=lambda *args, **kwargs: None,
        NumberColumn=lambda *args, **kwargs: None,
        SelectboxColumn=lambda *args, **kwargs: None,
    )
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


def _railway_geometry():
    from concrete_pmm_pro.geometry.generators import railway_u_girder

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


def test_railway_u_girder_is_enabled_for_dedicated_strand_layout(monkeypatch) -> None:
    _install_streamlit_stub(monkeypatch)

    import concrete_pmm_pro.ui.prestress_page as prestress_page

    assert prestress_page.RAILWAY_U_GIRDER_PRESET_KEY == "railway_u_girder"
    assert "railway_u_girder" in prestress_page.GIRDER_PRESTRESS_UI_PRESET_KEYS
    assert "Debond pattern mm" in prestress_page.GIRDER_STRAND_LAYOUT_COLUMNS
    assert "Debond pattern mm" in prestress_page.GIRDER_STRAND_LAYOUT_EDITOR_COLUMNS
    assert "1000, 2000" in prestress_page.__dict__["_parse_debond_pattern_mm"].__doc__


def test_railway_u_girder_default_strand_layout_matches_drawing(monkeypatch) -> None:
    _install_streamlit_stub(monkeypatch)

    from concrete_pmm_pro.ui.prestress_page import (
        _girder_strand_point_layout_dataframe,
        _normalize_girder_strand_layout_table,
        _validate_girder_strand_layout,
    )

    geometry = _railway_geometry()
    table = _normalize_girder_strand_layout_table(None, span_length_m=30.0, geometry=geometry)

    assert table["Group ID"].tolist() == [
        "L Row 1", "L Row 2", "L Row 3", "L Row 4", "L Row 5",
        "R Row 1", "R Row 2", "R Row 3", "R Row 4", "R Row 5",
    ]
    assert table["No. Strands"].tolist() == [9, 9, 7, 7, 4, 9, 9, 7, 7, 4]
    assert int(table["No. Strands"].sum()) == 72
    assert table["y_mm_from_bottom"].tolist() == [95.0, 150.0, 205.0, 260.0, 315.0] * 2
    assert set(table["Strand Size"]) == {"12.7 mm low-relaxation strand"}
    assert all(table["Debond pattern mm"].fillna("") == "")
    assert "-2620,-2565,-2510,-2455,-2400,-2345,-2290,-2235,-2180" == table.loc[0, "Strand x positions mm"]
    assert "2620,2565,2510,2455,2400,2345,2290,2235,2180" == table.loc[5, "Strand x positions mm"]
    assert table.loc[4, "Strand x positions mm"] == "-2510,-2455,-2400,-2345"
    assert table.loc[9, "Strand x positions mm"] == "2510,2455,2400,2345"

    errors, warnings = _validate_girder_strand_layout(table, span_length_m=30.0, geometry=geometry)
    assert errors == []
    assert warnings == []

    points = _girder_strand_point_layout_dataframe(table, geometry)
    assert len(points.index) == 72
    assert points["x_mm"].min() == -2620.0
    assert points["x_mm"].max() == 2620.0
    assert points.loc[points["Group ID"] == "L Row 1", "y_mm_from_bottom"].unique().tolist() == [95.0]
    assert points.loc[points["Group ID"] == "R Row 5", "y_mm_from_bottom"].unique().tolist() == [315.0]


def test_railway_u_girder_debond_symbol_pattern_is_preview_metadata(monkeypatch) -> None:
    _install_streamlit_stub(monkeypatch)

    from concrete_pmm_pro.ui.prestress_page import (
        _girder_effective_prestress_preview_dataframe,
        _girder_strand_point_layout_dataframe,
        _normalize_girder_strand_layout_table,
        _plot_girder_strand_cross_section_layout,
        _validate_girder_strand_layout,
    )

    raw = pd.DataFrame(
        [
            {
                "Active": True,
                "Group ID": "Symbol row",
                "Strand Size": "12.7 mm low-relaxation strand",
                "No. Strands": 6,
                "Strand x positions mm": "0,55,110,165,220,275",
                "y_mm_from_bottom": 95.0,
                "Left debond m": 0.0,
                "Right debond m": 0.0,
                "Debonded strand nos": "",
                "Debond pattern mm": "0,1000,2000,3000,4000,5000",
            }
        ]
    )
    table = _normalize_girder_strand_layout_table(raw, span_length_m=20.0, geometry=None)
    assert table.loc[0, "Debond pattern mm"] == "0,1000,2000,3000,4000,5000"
    errors, warnings = _validate_girder_strand_layout(table, span_length_m=20.0, geometry=None)
    assert errors == []
    assert warnings == ["REVIEW: Symbol row: section width at this y-level could not be resolved; centered layout uses minimum spacing only."]

    points = _girder_strand_point_layout_dataframe(table, None)
    assert points["Drawing debond length mm"].tolist() == [0, 1000, 2000, 3000, 4000, 5000]
    assert points["Debonded selected"].tolist() == [False] * 6

    preview = _girder_effective_prestress_preview_dataframe(table, span_length_m=20.0)
    assert int(preview.loc[preview["x_m"] == 10.0, "Effective strands"].iloc[0]) == 6

    fig = _plot_girder_strand_cross_section_layout(table, None)
    trace_names = [trace.name for trace in fig.data]
    for label in [
        "Debonded at 1000 mm",
        "Debonded at 2000 mm",
        "Debonded at 3000 mm",
        "Debonded at 4000 mm",
        "Debonded at 5000 mm",
    ]:
        assert label in trace_names


def test_project_io_preserves_strand_x_positions_and_debond_pattern_source() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    source = (root / "concrete_pmm_pro" / "io" / "project_io.py").read_text(encoding="utf-8")
    assert "Strand x positions mm" in source
    assert "Debonded strand nos" in source
    assert "Debond pattern mm" in source
