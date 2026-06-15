from __future__ import annotations

import pytest

from concrete_pmm_pro.core.analysis import AnalysisModeSettings
from concrete_pmm_pro.geometry import default_registry
from concrete_pmm_pro.geometry.presets import preset_by_key
from concrete_pmm_pro.geometry.summary import summarize_geometry
from concrete_pmm_pro.geometry.validation import validate_section_geometry
from concrete_pmm_pro.ui.section_builder import _preset_matches_member_type


DEFAULT_PARAMS = {
    "width_mm": 5500,
    "depth_mm": 1600,
    "top_wall_width_mm": 600,
    "bottom_side_width_mm": 650,
    "inner_vertical_depth_mm": 600,
    "haunch_size_mm": 300,
    "floor_side_thickness_mm": 395,
    "floor_center_thickness_mm": 450,
}


def _vertices_down_from_top():
    geometry = default_registry.geometry("railway_u_girder")(**DEFAULT_PARAMS)
    depth = DEFAULT_PARAMS["depth_mm"]
    return [(round(point.x, 6), round(depth / 2.0 - point.y, 6)) for point in geometry.outer_polygon]


def test_railway_u_girder_preset_is_available_for_bridge_beam_girder() -> None:
    preset = preset_by_key("railway_u_girder")

    assert preset["display_name"] == "Railway U-Girder"
    assert preset["category"] == "General / Non-composite Girder"
    assert preset["generator"] == "railway_u_girder"
    assert _preset_matches_member_type(preset, AnalysisModeSettings(member_type="beam_girder")) is True


def test_railway_u_girder_default_geometry_matches_user_drawing_dimensions() -> None:
    geometry = default_registry.geometry("railway_u_girder")(**DEFAULT_PARAMS)
    validation = validate_section_geometry(geometry)
    summary = summarize_geometry(geometry)

    assert validation.is_valid, validation.errors
    assert len(geometry.holes) == 0
    assert geometry.metadata["preset"] == "railway_u_girder"
    assert geometry.metadata["derived_details"] == {
        "outside_notch_mm": pytest.approx(50.0),
        "outside_step_y_from_top_mm": pytest.approx(930.0),
        "chamfer_mm": pytest.approx(25.0),
        "inner_half_width_mm": pytest.approx(2100.0),
        "floor_side_top_y_from_top_mm": pytest.approx(900.0),
        "floor_center_top_y_from_top_mm": pytest.approx(845.0),
        "floor_underside_y_from_top_mm": pytest.approx(1295.0),
    }
    assert summary.x_min_mm == pytest.approx(-2750.0)
    assert summary.x_max_mm == pytest.approx(2750.0)
    assert summary.y_min_mm == pytest.approx(-800.0)
    assert summary.y_max_mm == pytest.approx(800.0)
    assert summary.area_mm2 == pytest.approx(3_833_125.0)
    assert summary.centroid_x_mm == pytest.approx(0.0, abs=1e-9)
    assert summary.centroid_y_from_top_mm == pytest.approx(939.1259851078863)


def test_railway_u_girder_vertices_include_notches_chamfers_and_haunches() -> None:
    assert _vertices_down_from_top() == [
        (-2675.0, 0.0),
        (-2125.0, 0.0),
        (-2100.0, 25.0),
        (-2100.0, 600.0),
        (-1800.0, 900.0),
        (0.0, 845.0),
        (1800.0, 900.0),
        (2100.0, 600.0),
        (2100.0, 25.0),
        (2125.0, 0.0),
        (2675.0, 0.0),
        (2700.0, 25.0),
        (2700.0, 930.0),
        (2750.0, 930.0),
        (2750.0, 1575.0),
        (2725.0, 1600.0),
        (2100.0, 1600.0),
        (2100.0, 1295.0),
        (-2100.0, 1295.0),
        (-2100.0, 1600.0),
        (-2725.0, 1600.0),
        (-2750.0, 1575.0),
        (-2750.0, 930.0),
        (-2700.0, 930.0),
        (-2700.0, 25.0),
    ]


def test_railway_u_girder_dimension_guides_show_drawing_and_derived_values() -> None:
    dimensions = default_registry.dimensions("railway_u_girder")(**DEFAULT_PARAMS)
    values_by_symbol = {dimension.symbol: dimension.value_mm for dimension in dimensions}

    assert values_by_symbol["B"] == pytest.approx(5500.0)
    assert values_by_symbol["B/2 L"] == pytest.approx(2750.0)
    assert values_by_symbol["B/2 R"] == pytest.approx(2750.0)
    assert values_by_symbol["t_wall_top"] == pytest.approx(600.0)
    assert values_by_symbol["clear_half"] == pytest.approx(2100.0)
    assert values_by_symbol["H"] == pytest.approx(1600.0)
    assert values_by_symbol["y_step"] == pytest.approx(670.0)
    assert values_by_symbol["h_side"] == pytest.approx(395.0)
    assert values_by_symbol["h_center"] == pytest.approx(450.0)
    assert values_by_symbol["bottom_leg"] == pytest.approx(650.0)
    assert values_by_symbol["notch"] == pytest.approx(50.0)
    assert values_by_symbol["CL"] is None


def test_railway_u_girder_rejects_invalid_notch_relationship() -> None:
    params = dict(DEFAULT_PARAMS)
    params["top_wall_width_mm"] = 650

    with pytest.raises(ValueError, match="top wall width must be less than bottom side width"):
        default_registry.geometry("railway_u_girder")(**params)
