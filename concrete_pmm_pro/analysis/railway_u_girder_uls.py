"""Guarded Railway U-Girder ULS strength-check framework helpers.

ULS.RAIL.UGIRDER1 is a controlled bridge from the closed-out Railway U-Girder
SLS review package to a future final-design workflow.  It deliberately builds
code-basis/readiness/demand tables and a check matrix without promoting the
current application to final code-certified design.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import pandas as pd

from concrete_pmm_pro.analysis.capacity_check import check_uls_demands_against_rc_pmm
from concrete_pmm_pro.analysis.pmm_solver import run_rc_pmm_solver
from concrete_pmm_pro.analysis.uls_flexure_code_basis import apply_flexure_code_basis, beam_girder_flexure_code_basis
from concrete_pmm_pro.analysis.uls_strength_routing import bridge_beam_girder_uls_strength_route
from concrete_pmm_pro.core.analysis import AnalysisInput, AnalysisSettings
from concrete_pmm_pro.core.models import ConcreteMaterial, LoadCase, PrestressElement, Rebar, RebarMaterial, SectionGeometry
from concrete_pmm_pro.core.reinforcement_system import effective_prestress_for_analysis
from concrete_pmm_pro.geometry.summary import to_shapely_polygon
from concrete_pmm_pro.serviceability.girder_prestress_station import active_strand_groups_at_station
from concrete_pmm_pro.serviceability.girder_sls_load_components import BEAM_GIRDER_SYSTEM_SETTINGS_KEY, system_settings_from_mapping

RAILWAY_UGIRDER_ULS_FRAMEWORK_STATUS = "Railway U-Girder ULS Strength Check Framework - Guarded Review Ready"
RAILWAY_UGIRDER_ULS_FRAMEWORK_WARNING = (
    "ULS.RAIL.UGIRDER1 provides a guarded ULS strength-check framework and traceability matrix only. "
    "It is not final code-certified design and must not be used as an engineer certification."
)
RAILWAY_UGIRDER_ULS_CERTIFICATION_BOUNDARY = (
    "Framework-ready means ULS demand routing, code-basis guardrails, and check-readiness evidence are visible. "
    "Final design still requires validated Railway U-Girder flexure, shear, torsion, V+T, prestress development, "
    "anchorage/end-zone, time-dependent behavior, and Engineer-of-Record review."
)
RAILWAY_UGIRDER_ULS_REQUIRED_FUTURE_CHECKS = [
    "Railway U-Girder flexure calculation evidence benchmark validation",
    "PSC shear route including prestress effects, dv policy, and end-region checks",
    "Railway U-Girder torsion and combined V+T interaction",
    "transfer length force ramp",
    "development length and debonded strand anchorage",
    "anchorage / end-zone bursting and spalling",
    "lifting insert / local hardware check",
    "creep/shrinkage and time-dependent composite redistribution",
    "independent benchmark examples and final design report traceability",
]
RAILWAY_UGIRDER_ULS_FLEXURE_EVIDENCE_STATUS = "Railway U-Girder ULS Flexure Calculation Evidence - Engineering Review Ready"
RAILWAY_UGIRDER_ULS_FLEXURE_EVIDENCE_WARNING = (
    "ULS.RAIL.UGIRDER2 adds Railway U-Girder flexure section-strength calculation evidence using the existing "
    "strain-compatibility PMM engine and AASHTO LRFD prestressed flexure phi-routing layer. It remains engineering-review "
    "evidence only because Railway U-Girder-specific benchmark validation, development length, anchorage/end-zone, "
    "and time-dependent composite redistribution are not completed."
)
RAILWAY_UGIRDER_ULS_MAX_FLEXURE_EVIDENCE_ROWS = 8
_GIRDER_STRAND_FPU_MPA_DEFAULT = 1860.0
_GIRDER_STRAND_FPY_MPA_DEFAULT = 1670.0
_GIRDER_STRAND_EP_MPA_DEFAULT = 195000.0
_ULS_DEMAND_TOL = 1.0e-9

RAILWAY_UGIRDER_ULS_TABLE_KEYS = [
    "railway_u_girder_uls_closeout_boundary",
    "railway_u_girder_uls_code_basis",
    "railway_u_girder_uls_demand_summary",
    "railway_u_girder_uls_flexure_evidence",
    "railway_u_girder_uls_check_matrix",
    "railway_u_girder_uls_future_checks",
]


@dataclass(frozen=True)
class RailwayUGirderULSFrameworkPackage:
    """Report-ready tables for the guarded Railway U-Girder ULS framework."""

    available: bool
    status: str
    closeout_boundary: pd.DataFrame = field(default_factory=pd.DataFrame)
    code_basis: pd.DataFrame = field(default_factory=pd.DataFrame)
    demand_summary: pd.DataFrame = field(default_factory=pd.DataFrame)
    flexure_evidence: pd.DataFrame = field(default_factory=pd.DataFrame)
    check_matrix: pd.DataFrame = field(default_factory=pd.DataFrame)
    future_checks: pd.DataFrame = field(default_factory=pd.DataFrame)
    warnings: list[str] = field(default_factory=list)

    def tables(self) -> dict[str, pd.DataFrame]:
        return {
            "railway_u_girder_uls_closeout_boundary": self.closeout_boundary,
            "railway_u_girder_uls_code_basis": self.code_basis,
            "railway_u_girder_uls_demand_summary": self.demand_summary,
            "railway_u_girder_uls_flexure_evidence": self.flexure_evidence,
            "railway_u_girder_uls_check_matrix": self.check_matrix,
            "railway_u_girder_uls_future_checks": self.future_checks,
        }


def _get(mapping: Any, key: str, default: Any = None) -> Any:
    if mapping is None:
        return default
    if hasattr(mapping, "get"):
        try:
            return mapping.get(key, default)
        except (AttributeError, TypeError, ValueError):
            return default
    return getattr(mapping, key, default)


def _to_dataframe(value: Any) -> pd.DataFrame:
    if value is None:
        return pd.DataFrame()
    try:
        return pd.DataFrame(value).copy()
    except Exception:
        return pd.DataFrame()


def _float_or_zero(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if pd.isna(numeric):
        return 0.0
    return float(numeric)


def is_railway_u_girder_uls_context(session_state: Any) -> bool:
    """Return True when current project context is the Railway U-Girder preset."""

    geometry = _get(session_state, "section_geometry")
    metadata = getattr(geometry, "metadata", {}) or {}
    if isinstance(metadata, Mapping):
        for key in ("preset", "generator", "preset_key", "section_preset_key"):
            if str(metadata.get(key) or "").strip().casefold() == "railway_u_girder":
                return True
    geometry_name = str(getattr(geometry, "name", "") or "").casefold()
    if "railway" in geometry_name and "u-girder" in geometry_name:
        return True
    for state_key in ("section_preset_key", "section_preset_name", "active_section_preset_name"):
        text = str(_get(session_state, state_key, "") or "").casefold()
        if text == "railway_u_girder" or ("railway" in text and "u-girder" in text):
            return True
    params = _get(session_state, "section_parameters", {})
    if isinstance(params, Mapping):
        required = {"h1_step_height_mm", "h2_bottom_opening_mm", "h3_floor_side_thickness_mm", "h4_floor_center_thickness_mm"}
        if required.issubset({str(key) for key in params.keys()}):
            return True
    return False


def active_railway_u_girder_uls_demand_dataframe(session_state: Any) -> pd.DataFrame:
    """Return active ULS station-demand rows from Loads for Railway U-Girder checks."""

    columns = ["Active", "Station x (m)", "Case Name", "Mux", "Vuy", "Tu", "Muy", "Vux", "Nu", "Note"]
    table = _to_dataframe(_get(session_state, "beam_uls_loads_table", None))
    if not table.empty:
        for column in columns:
            if column not in table.columns:
                table[column] = "" if column in {"Case Name", "Note"} else 0.0
        table = table[columns].copy()
        active_mask = table["Active"].map(lambda value: bool(value) if not isinstance(value, str) else value.strip().casefold() not in {"false", "0", "no", "n", "off", ""})
        table = table.loc[active_mask].copy()
    else:
        rows: list[dict[str, Any]] = []
        for load in list(_get(session_state, "load_cases", []) or []):
            if not bool(_get(load, "active", True)):
                continue
            if str(_get(load, "load_type", "") or "").strip().upper() != "ULS":
                continue
            rows.append(
                {
                    "Active": True,
                    "Station x (m)": 0.0,
                    "Case Name": _get(load, "name", "ULS"),
                    "Mux": _float_or_zero(_get(load, "Mux_Nmm", 0.0)) / 1.0e6,
                    "Vuy": 0.0,
                    "Tu": 0.0,
                    "Muy": _float_or_zero(_get(load, "Muy_Nmm", 0.0)) / 1.0e6,
                    "Vux": 0.0,
                    "Nu": _float_or_zero(_get(load, "Pu_N", 0.0)) / 1.0e3,
                    "Note": _get(load, "note", "ULS LoadCase fallback; station/resultants should be defined in Loads table for girder design."),
                }
            )
        table = pd.DataFrame(rows, columns=columns)
    for numeric_column in ["Station x (m)", "Mux", "Vuy", "Tu", "Muy", "Vux", "Nu"]:
        table[numeric_column] = pd.to_numeric(table.get(numeric_column, pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    return table.reset_index(drop=True)




def _as_model(value: Any, model_type: Any) -> Any | None:
    if isinstance(value, model_type):
        return value
    if isinstance(value, Mapping):
        try:
            return model_type.model_validate(value)
        except Exception:
            return None
    return None


def _railway_uls_concrete_material_from_state(session_state: Any) -> ConcreteMaterial | None:
    """Return the concrete material used by the guarded ULS flexure evidence.

    ULS.RAIL.UGIRDER2 intentionally uses a single current PMM concrete material.
    For Railway U-Girder projects, the preferred source is the active concrete
    material if already assigned; otherwise the web f'c from stage settings is
    used.  The differential web/slab material model remains a certification
    blocker and is disclosed in the evidence table.
    """

    concrete = _as_model(_get(session_state, "concrete_material", None), ConcreteMaterial)
    if concrete is not None:
        return concrete
    stage = _get(session_state, "railway_u_girder_stage_settings", {}) or {}
    fc = _float_or_zero(_get(stage, "web_fc_MPa", 45.0)) or 45.0
    try:
        return ConcreteMaterial(name="Railway U-Girder ULS review concrete - web f'c", fc_MPa=float(fc))
    except Exception:
        return None


def _railway_uls_section_geometry_from_state(session_state: Any) -> SectionGeometry | None:
    return _as_model(_get(session_state, "section_geometry", None), SectionGeometry)


def _railway_uls_analysis_settings_from_state(session_state: Any) -> AnalysisSettings:
    raw = _get(session_state, "analysis_settings", None)
    if isinstance(raw, AnalysisSettings):
        settings = raw
    elif isinstance(raw, Mapping):
        try:
            settings = AnalysisSettings.model_validate(raw)
        except Exception:
            settings = AnalysisSettings()
    else:
        settings = AnalysisSettings()
    return settings.model_copy(
        update={
            "code": "AASHTO LRFD",
            "include_rebars": True,
            "include_prestress": True,
            "use_phi_factor": True,
            # Keep report/QA generation responsive while preserving the shared
            # strain-compatibility engine.  This is calculation evidence, not a
            # final certification benchmark run.
            "neutral_axis_angle_steps": 12,
            "neutral_axis_depth_steps": 36,
        }
    )


def _railway_uls_span_length_m(session_state: Any) -> float:
    system = system_settings_from_mapping(_get(session_state, BEAM_GIRDER_SYSTEM_SETTINGS_KEY, None))
    try:
        span = float(system.span_length_m)
    except (TypeError, ValueError):
        span = 10.0
    return span if span > 0.0 else 10.0


def _railway_uls_section_bounds(geometry: SectionGeometry) -> tuple[float, float, float, float]:
    polygon = to_shapely_polygon(geometry)
    minx, miny, maxx, maxy = polygon.bounds
    return float(minx), float(miny), float(maxx), float(maxy)


def _railway_uls_model_list(value: Any, model_type: Any) -> list[Any]:
    rows = [] if value is None else list(value)
    models: list[Any] = []
    for row in rows:
        parsed = _as_model(row, model_type)
        if parsed is not None:
            models.append(parsed)
    return models


def _railway_uls_girder_strand_elements_for_station(
    session_state: Any,
    *,
    geometry: SectionGeometry,
    x_m: float,
    span_length_m: float,
) -> tuple[list[PrestressElement], list[str]]:
    table = _get(session_state, "girder_strand_layout_table", None)
    if table is None:
        return [], ["No dedicated girder strand layout table is available for ULS flexure evidence."]
    _, y_min, _, _ = _railway_uls_section_bounds(geometry)
    try:
        groups = active_strand_groups_at_station(table, x_m=float(x_m), span_length_m=float(span_length_m))
    except Exception as exc:
        return [], [f"Station strand participation could not be evaluated: {exc}"]
    elements: list[PrestressElement] = []
    for group in groups:
        if group.no_strands <= 0 or group.area_per_strand_mm2 <= 0.0:
            continue
        pe_final_per_strand_n = max(0.0, float(group.pe_eff_final_per_strand_kN)) * 1000.0
        initial_stress_mpa = pe_final_per_strand_n / float(group.area_per_strand_mm2) if group.area_per_strand_mm2 > 0.0 else 0.0
        elements.append(
            PrestressElement(
                x_mm=0.0,
                y_mm=float(y_min) + float(group.y_mm_from_bottom),
                area_mm2=float(group.area_per_strand_mm2),
                steel_type="strand",
                material_name="Girder strand layout",
                fpy_mpa=_GIRDER_STRAND_FPY_MPA_DEFAULT,
                fpu_mpa=_GIRDER_STRAND_FPU_MPA_DEFAULT,
                ep_mpa=_GIRDER_STRAND_EP_MPA_DEFAULT,
                pe_eff_n=pe_final_per_strand_n,
                initial_stress_mpa=initial_stress_mpa,
                initial_strain=initial_stress_mpa / _GIRDER_STRAND_EP_MPA_DEFAULT if initial_stress_mpa > 0.0 else 0.0,
                bonded=True,
                count=int(group.no_strands),
                label=f"{group.group_id} @ x={float(x_m):.3f} m",
            )
        )
    if not elements:
        return [], ["No effective bonded strand group is available at this station; debonding/development must be reviewed."]
    return elements, [f"{sum(element.count for element in elements)} effective strand(s) included at x={float(x_m):.3f} m by the PS5 step-function debonding handoff."]


def _railway_uls_analysis_input_for_flexure_row(
    session_state: Any,
    *,
    row: Mapping[str, Any],
) -> tuple[AnalysisInput | None, list[str]]:
    messages: list[str] = []
    geometry = _railway_uls_section_geometry_from_state(session_state)
    concrete = _railway_uls_concrete_material_from_state(session_state)
    if geometry is None:
        return None, ["Section geometry is missing."]
    if concrete is None:
        return None, ["Concrete material / web f'c stage setting is missing."]
    settings = _railway_uls_analysis_settings_from_state(session_state)
    rebars = _railway_uls_model_list(_get(session_state, "rebars", []) or [], Rebar)
    rebars = list(rebars)  # ordinary rebar is preserved when the engineer enabled it.
    rebar_materials = _railway_uls_model_list(_get(session_state, "rebar_materials", []) or [], RebarMaterial)
    generic_prestress = _railway_uls_model_list(_get(session_state, "prestress_elements", []) or [], PrestressElement)
    generic_prestress = effective_prestress_for_analysis(generic_prestress, session_state, settings)
    span_m = _railway_uls_span_length_m(session_state)
    station_m = _float_or_zero(row.get("Station x (m)"))
    station_m = max(0.0, min(float(station_m), span_m))
    strand_elements, strand_messages = _railway_uls_girder_strand_elements_for_station(
        session_state,
        geometry=geometry,
        x_m=station_m,
        span_length_m=span_m,
    )
    messages.extend(strand_messages)
    prestress_elements = [*generic_prestress, *strand_elements]
    if not rebars and not prestress_elements:
        return None, messages + ["No active ordinary rebar or bonded prestress is available for flexure evidence."]
    mux = _float_or_zero(row.get("Mux"))
    if abs(mux) <= _ULS_DEMAND_TOL:
        return None, messages + ["Mux demand is zero; zero-moment rows are tracked in demand summary but excluded from flexure D/C evidence."]
    nu = _float_or_zero(row.get("Nu"))
    case = str(row.get("Case Name") or "ULS").strip() or "ULS"
    load = LoadCase(
        name=f"{case} @ x={station_m:.3f} m",
        Pu_N=float(nu) * 1000.0,
        Mux_Nmm=float(mux) * 1_000_000.0,
        Muy_Nmm=0.0,
        load_type="ULS",
        active=True,
    )
    return (
        AnalysisInput(
            section_geometry=geometry,
            concrete_material=concrete,
            rebar_materials=rebar_materials,
            prestress_materials=[],
            rebars=rebars,
            prestress_elements=prestress_elements,
            load_cases=[load],
            settings=settings,
        ),
        messages,
    )


def _railway_uls_nominal_flexure_capacity_nmm(analysis_input: AnalysisInput) -> tuple[float | None, list[str]]:
    messages: list[str] = []
    try:
        nominal_settings = analysis_input.settings.model_copy(update={"use_phi_factor": False})
        nominal_input = analysis_input.model_copy(update={"settings": nominal_settings})
        nominal_pmm = run_rc_pmm_solver(nominal_input)
        nominal_summary = check_uls_demands_against_rc_pmm(nominal_pmm, nominal_input.load_cases)
        nominal_result = nominal_summary.results[0] if nominal_summary.results else None
    except Exception as exc:
        return None, [f"Nominal flexure evidence solve failed: {exc}"]
    if nominal_result is None or nominal_result.capacity_phiMn_Nmm is None:
        return None, ["Nominal Mn could not be interpolated from the PMM point cloud."]
    if nominal_result.warning_count:
        messages.append(f"Nominal-capacity interpolation carried {nominal_result.warning_count} warning(s).")
    return float(nominal_result.capacity_phiMn_Nmm), messages


def _railway_uls_has_bonded_prestress(analysis_input: AnalysisInput | None) -> bool:
    if analysis_input is None:
        return False
    return any(element.bonded and element.count > 0 and element.area_mm2 > 0.0 for element in analysis_input.prestress_elements)


def _railway_uls_flexure_evidence_columns() -> list[str]:
    return [
        "Check",
        "Status",
        "Governing x (m)",
        "Case",
        "Demand Mux (kN-m)",
        "Nominal Mn (kN-m)",
        "φ",
        "φMn (kN-m)",
        "D/C",
        "Bending direction",
        "Tension face",
        "Effective strands",
        "Concrete basis",
        "Code basis",
        "Method",
        "Evidence status",
        "Blocked final claim",
        "Notes",
    ]


def railway_u_girder_uls_flexure_evidence_dataframe(session_state: Any, active_uls: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return guarded station flexure D/C evidence for Railway U-Girder ULS.

    ULS.RAIL.UGIRDER2 deliberately exposes calculation evidence, not final
    certification.  It uses the existing section PMM/strain-compatibility solver
    and the AASHTO LRFD prestressed flexure phi layer.  Remaining blockers are
    reported in every row so PASS/FAIL cannot be mistaken for code-certified
    girder design.
    """

    columns = _railway_uls_flexure_evidence_columns()
    active = active_uls.copy() if isinstance(active_uls, pd.DataFrame) else active_railway_u_girder_uls_demand_dataframe(session_state)
    if active.empty:
        return pd.DataFrame(columns=columns)
    active["__mux"] = pd.to_numeric(active.get("Mux", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    candidates = active.loc[active["__mux"].abs() > _ULS_DEMAND_TOL].copy()
    if candidates.empty:
        return pd.DataFrame(columns=columns)
    if len(candidates.index) > RAILWAY_UGIRDER_ULS_MAX_FLEXURE_EVIDENCE_ROWS:
        candidates = candidates.head(RAILWAY_UGIRDER_ULS_MAX_FLEXURE_EVIDENCE_ROWS).copy()
    rows: list[dict[str, Any]] = []
    for _, demand_row in candidates.iterrows():
        case = str(demand_row.get("Case Name") or "ULS")
        station = _float_or_zero(demand_row.get("Station x (m)"))
        demand = _float_or_zero(demand_row.get("Mux"))
        analysis_input, input_messages = _railway_uls_analysis_input_for_flexure_row(session_state, row=demand_row)
        if analysis_input is None:
            rows.append(
                {
                    "Check": "ULS flexure",
                    "Status": "REVIEW",
                    "Governing x (m)": station,
                    "Case": case,
                    "Demand Mux (kN-m)": demand,
                    "Nominal Mn (kN-m)": float("nan"),
                    "φ": float("nan"),
                    "φMn (kN-m)": float("nan"),
                    "D/C": float("nan"),
                    "Bending direction": "Sagging (+Mux)" if demand > 0.0 else "Hogging (-Mux)",
                    "Tension face": "Bottom face" if demand > 0.0 else "Top face",
                    "Effective strands": 0,
                    "Concrete basis": "single-material PMM evidence",
                    "Code basis": "AASHTO LRFD prestressed flexure route - not certified",
                    "Method": "not ready",
                    "Evidence status": RAILWAY_UGIRDER_ULS_FLEXURE_EVIDENCE_STATUS,
                    "Blocked final claim": "No final certification without benchmarks, development length, anchorage/end-zone, and time-dependent checks.",
                    "Notes": "; ".join(input_messages),
                }
            )
            continue
        flexure_basis = beam_girder_flexure_code_basis(
            bridge_beam_girder_uls_strength_route(),
            has_bonded_prestress=_railway_uls_has_bonded_prestress(analysis_input),
        )
        try:
            pmm_result = run_rc_pmm_solver(analysis_input)
            dc_summary = check_uls_demands_against_rc_pmm(pmm_result, analysis_input.load_cases)
            dc_result = dc_summary.results[0] if dc_summary.results else None
        except Exception as exc:
            rows.append(
                {
                    "Check": "ULS flexure",
                    "Status": "REVIEW",
                    "Governing x (m)": station,
                    "Case": case,
                    "Demand Mux (kN-m)": demand,
                    "Nominal Mn (kN-m)": float("nan"),
                    "φ": float("nan"),
                    "φMn (kN-m)": float("nan"),
                    "D/C": float("nan"),
                    "Bending direction": "Sagging (+Mux)" if demand > 0.0 else "Hogging (-Mux)",
                    "Tension face": "Bottom face" if demand > 0.0 else "Top face",
                    "Effective strands": sum(element.count for element in analysis_input.prestress_elements),
                    "Concrete basis": "single-material PMM evidence",
                    "Code basis": flexure_basis.capacity_label,
                    "Method": "solver error",
                    "Evidence status": RAILWAY_UGIRDER_ULS_FLEXURE_EVIDENCE_STATUS,
                    "Blocked final claim": "No final certification from a failed evidence solve.",
                    "Notes": f"Flexure evidence solve failed: {exc}",
                }
            )
            continue
        nominal_nmm, nominal_messages = _railway_uls_nominal_flexure_capacity_nmm(analysis_input)
        phi_capacity_nmm = None if dc_result is None else dc_result.capacity_phiMn_Nmm
        routed_capacity_nmm, routed_note = apply_flexure_code_basis(
            phi_capacity_nmm=phi_capacity_nmm,
            nominal_capacity_nmm=nominal_nmm,
            basis=flexure_basis,
        )
        phi_value = float("nan")
        if nominal_nmm is not None and nominal_nmm > 0.0 and routed_capacity_nmm is not None:
            phi_value = float(routed_capacity_nmm) / float(nominal_nmm)
        capacity_kNm = float(routed_capacity_nmm) / 1_000_000.0 if routed_capacity_nmm is not None else float("nan")
        nominal_kNm = float(nominal_nmm) / 1_000_000.0 if nominal_nmm is not None else float("nan")
        dc_value = abs(float(demand)) / capacity_kNm if capacity_kNm and pd.notna(capacity_kNm) and capacity_kNm > 0.0 else float("nan")
        status = "Engineering Review PASS" if pd.notna(dc_value) and dc_value <= 1.0 else "Engineering Review FAIL" if pd.notna(dc_value) else "REVIEW"
        notes = [
            RAILWAY_UGIRDER_ULS_FLEXURE_EVIDENCE_WARNING,
            "Section-strength evidence uses current PMM single-concrete-material model; differential web/slab material and final composite calibration remain future work.",
            routed_note,
        ]
        notes.extend(input_messages)
        notes.extend(nominal_messages)
        rows.append(
            {
                "Check": "ULS flexure",
                "Status": status,
                "Governing x (m)": station,
                "Case": case,
                "Demand Mux (kN-m)": float(demand),
                "Nominal Mn (kN-m)": nominal_kNm,
                "φ": phi_value,
                "φMn (kN-m)": capacity_kNm,
                "D/C": dc_value,
                "Bending direction": "Sagging (+Mux)" if demand > 0.0 else "Hogging (-Mux)",
                "Tension face": "Bottom face" if demand > 0.0 else "Top face",
                "Effective strands": sum(element.count for element in analysis_input.prestress_elements),
                "Concrete basis": f"{analysis_input.concrete_material.name}; f'c={analysis_input.concrete_material.fc_MPa:g} MPa; single-material evidence",
                "Code basis": flexure_basis.capacity_label,
                "Method": flexure_basis.method_label,
                "Evidence status": RAILWAY_UGIRDER_ULS_FLEXURE_EVIDENCE_STATUS,
                "Blocked final claim": "No code-certified or engineer-certified PASS until flexure benchmarks, development length, anchorage/end-zone, and time-dependent composite checks are complete.",
                "Notes": "; ".join([str(item) for item in notes if str(item).strip()]),
            }
        )
    return pd.DataFrame(rows, columns=columns)

def railway_u_girder_uls_code_basis_dataframe() -> pd.DataFrame:
    route = bridge_beam_girder_uls_strength_route()
    rows = [
        {"Item": "Workflow route", "Value": route.workflow_label, "Status": "LOCKED", "Evidence / Boundary": "Railway U-Girder is routed through Bridge Beam/Girder ULS, not Building ULS."},
        {"Item": "Design code basis", "Value": route.display_code_label, "Status": "GUARDED", "Evidence / Boundary": "Project-specific railway criteria and owner requirements still govern final adoption."},
        {"Item": "ULS load source", "Value": route.uls_load_source_label, "Status": "SOURCE OF TRUTH", "Evidence / Boundary": "Analysis consumes active station-resultant ULS rows from Loads."},
        {"Item": "Default strength combo label", "Value": route.default_combo_label, "Status": "REVIEW", "Evidence / Boundary": "Actual project load combinations must be reviewed before final design."},
        {"Item": "Flexure route", "Value": route.flexure_engine_label, "Status": "FRAMEWORK READY", "Evidence / Boundary": route.flexure_basis_note},
        {"Item": "Shear route", "Value": route.shear_engine_label, "Status": "GUARDED PREVIEW", "Evidence / Boundary": "Railway U-Girder PSC shear and end-region certification remain future work."},
        {"Item": "Torsion route", "Value": route.torsion_engine_label, "Status": "GUARDED PREVIEW", "Evidence / Boundary": "Railway U-Girder torsion and combined V+T calibration remain future work."},
        {"Item": "Certification boundary", "Value": "Not engineer-certified", "Status": "NOT CERTIFIED", "Evidence / Boundary": RAILWAY_UGIRDER_ULS_CERTIFICATION_BOUNDARY},
    ]
    return pd.DataFrame(rows, columns=["Item", "Value", "Status", "Evidence / Boundary"])


def railway_u_girder_uls_demand_summary_dataframe(active_uls: pd.DataFrame) -> pd.DataFrame:
    active_uls = active_uls.copy() if isinstance(active_uls, pd.DataFrame) else pd.DataFrame()
    if active_uls.empty:
        rows = [
            {"Demand Item": "Active ULS station rows", "Value": 0.0, "Unit": "rows", "Governing Case": "-", "Governing x (m)": "-", "Status": "INPUT REQUIRED"},
            {"Demand Item": "ULS demand readiness", "Value": "No active ULS Loads rows", "Unit": "-", "Governing Case": "-", "Governing x (m)": "-", "Status": "NOT READY"},
        ]
        return pd.DataFrame(rows, columns=["Demand Item", "Value", "Unit", "Governing Case", "Governing x (m)", "Status"])
    rows: list[dict[str, Any]] = [
        {"Demand Item": "Active ULS station rows", "Value": float(len(active_uls.index)), "Unit": "rows", "Governing Case": "-", "Governing x (m)": "-", "Status": "AVAILABLE"},
    ]
    demand_columns = [
        ("Mux", "Peak |Mux|", "kN-m"),
        ("Vuy", "Peak |Vuy|", "kN"),
        ("Tu", "Peak |Tu|", "kN-m"),
        ("Muy", "Peak |Muy|", "kN-m"),
        ("Vux", "Peak |Vux|", "kN"),
        ("Nu", "Peak |Nu|", "kN"),
    ]
    for column, label, unit in demand_columns:
        series = pd.to_numeric(active_uls.get(column, pd.Series(dtype=float)), errors="coerce").fillna(0.0)
        if series.empty:
            peak = 0.0
            idx = None
        else:
            abs_series = series.abs()
            idx = abs_series.idxmax()
            peak = float(abs_series.loc[idx]) if idx is not None else 0.0
        row = active_uls.loc[idx] if idx is not None and idx in active_uls.index else {}
        rows.append(
            {
                "Demand Item": label,
                "Value": peak,
                "Unit": unit,
                "Governing Case": str(_get(row, "Case Name", "-")),
                "Governing x (m)": float(_get(row, "Station x (m)", 0.0)) if idx is not None else "-",
                "Status": "AVAILABLE" if peak > 0.0 else "ZERO / REVIEW",
            }
        )
    return pd.DataFrame(rows, columns=["Demand Item", "Value", "Unit", "Governing Case", "Governing x (m)", "Status"])


def railway_u_girder_uls_check_matrix_dataframe(active_uls: pd.DataFrame) -> pd.DataFrame:
    has_loads = isinstance(active_uls, pd.DataFrame) and not active_uls.empty
    demand_status = "DEMAND AVAILABLE" if has_loads else "INPUT REQUIRED"
    rows = [
        {
            "Check Area": "ULS flexure",
            "Current Framework Status": "FRAMEWORK READY" if has_loads else "INPUT REQUIRED",
            "Demand Source": demand_status,
            "Capacity / Code Route": "ULS.RAIL.UGIRDER2 uses existing PMM strain-compatibility solver plus AASHTO LRFD prestressed flexure phi layer; Railway-specific benchmark validation still required",
            "Allowed Decision Wording": "Engineering Review PASS / FAIL allowed for flexure evidence only; not Certified PASS",
            "Blocked Final Claim": "No final design certification until Railway U-Girder flexure benchmarks, development length, anchorage/end-zone, and time-dependent checks are complete.",
        },
        {
            "Check Area": "ULS shear",
            "Current Framework Status": "GUARDED PREVIEW",
            "Demand Source": demand_status,
            "Capacity / Code Route": "Bridge shear gate available; PSC shear, prestress effects, dv/end-region route not final",
            "Allowed Decision Wording": "Review / Guarded Preview",
            "Blocked Final Claim": "No final shear certification until PSC shear + end-region benchmarks pass.",
        },
        {
            "Check Area": "ULS torsion",
            "Current Framework Status": "GUARDED PREVIEW",
            "Demand Source": demand_status,
            "Capacity / Code Route": "Bridge torsion gate available; Railway U-Girder torsion calibration not final",
            "Allowed Decision Wording": "Review / Guarded Preview",
            "Blocked Final Claim": "No final torsion certification until section-type torsion route is validated.",
        },
        {
            "Check Area": "Combined V+T",
            "Current Framework Status": "NOT CERTIFIED",
            "Demand Source": demand_status,
            "Capacity / Code Route": "Combined V+T must use validated shear and torsion routes together",
            "Allowed Decision Wording": "Not certified / Future work",
            "Blocked Final Claim": "Separate shear/torsion checks must not be read as final combined V+T PASS.",
        },
        {
            "Check Area": "Prestress development / anchorage",
            "Current Framework Status": "FUTURE WORK",
            "Demand Source": "Prestress/debonding input available from SLS workflow",
            "Capacity / Code Route": "Transfer length, development length, anchorage/end-zone bursting not implemented in ULS.RAIL.UGIRDER1",
            "Allowed Decision Wording": "Excluded from current framework",
            "Blocked Final Claim": "No final prestressed girder design without development and anchorage checks.",
        },
        {
            "Check Area": "Final design certification",
            "Current Framework Status": "NOT CERTIFIED",
            "Demand Source": "Framework evidence only",
            "Capacity / Code Route": "Requires Engineer-of-Record review, project load criteria, validated benchmarks, and final report",
            "Allowed Decision Wording": "Ready for engineering review",
            "Blocked Final Claim": "Do not use code-certified pass wording or final-design pass wording in this milestone.",
        },
    ]
    return pd.DataFrame(rows)


def railway_u_girder_uls_future_checks_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Priority": index,
                "Required Future Check": item,
                "Reason Final Certification Is Blocked": "Required before Railway U-Girder final code-certified design can be claimed.",
            }
            for index, item in enumerate(RAILWAY_UGIRDER_ULS_REQUIRED_FUTURE_CHECKS, start=1)
        ],
        columns=["Priority", "Required Future Check", "Reason Final Certification Is Blocked"],
    )


def railway_u_girder_uls_closeout_boundary_dataframe() -> pd.DataFrame:
    rows = [
        {"Item": "ULS framework milestone", "Status": RAILWAY_UGIRDER_ULS_FRAMEWORK_STATUS, "Evidence / Boundary": RAILWAY_UGIRDER_ULS_FRAMEWORK_WARNING},
        {"Item": "Allowed use", "Status": "READY FOR ENGINEERING REVIEW", "Evidence / Boundary": "Use for ULS workflow planning, demand traceability, and guarded design-check review."},
        {"Item": "Prohibited claim", "Status": "NOT CERTIFIED", "Evidence / Boundary": "Do not use code-certified pass wording, final-design pass wording, or engineer-certified wording from this milestone."},
        {"Item": "Final certification boundary", "Status": "FUTURE WORK", "Evidence / Boundary": RAILWAY_UGIRDER_ULS_CERTIFICATION_BOUNDARY},
    ]
    return pd.DataFrame(rows, columns=["Item", "Status", "Evidence / Boundary"])


def build_railway_u_girder_uls_framework_package(session_state: Any) -> RailwayUGirderULSFrameworkPackage:
    """Build guarded ULS framework tables for the active Railway U-Girder project."""

    if not is_railway_u_girder_uls_context(session_state):
        return RailwayUGirderULSFrameworkPackage(
            available=False,
            status="Not applicable — Railway U-Girder context not detected",
            warnings=["Railway U-Girder ULS framework package is only available for the Railway U-Girder preset."],
        )
    active_uls = active_railway_u_girder_uls_demand_dataframe(session_state)
    warnings = [RAILWAY_UGIRDER_ULS_FRAMEWORK_WARNING, RAILWAY_UGIRDER_ULS_FLEXURE_EVIDENCE_WARNING]
    if active_uls.empty:
        warnings.append("No active ULS Loads rows were found; define Strength ULS station-resultant rows before running design checks.")
    flexure_evidence = railway_u_girder_uls_flexure_evidence_dataframe(session_state, active_uls)
    if flexure_evidence.empty and not active_uls.empty:
        warnings.append("No nonzero Mux station rows were available for ULS.RAIL.UGIRDER2 flexure evidence.")
    return RailwayUGirderULSFrameworkPackage(
        available=True,
        status=RAILWAY_UGIRDER_ULS_FRAMEWORK_STATUS,
        closeout_boundary=railway_u_girder_uls_closeout_boundary_dataframe(),
        code_basis=railway_u_girder_uls_code_basis_dataframe(),
        demand_summary=railway_u_girder_uls_demand_summary_dataframe(active_uls),
        flexure_evidence=flexure_evidence,
        check_matrix=railway_u_girder_uls_check_matrix_dataframe(active_uls),
        future_checks=railway_u_girder_uls_future_checks_dataframe(),
        warnings=warnings,
    )
