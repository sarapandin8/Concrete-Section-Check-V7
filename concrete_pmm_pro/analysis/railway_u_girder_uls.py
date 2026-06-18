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

from concrete_pmm_pro.analysis.uls_strength_routing import bridge_beam_girder_uls_strength_route
from concrete_pmm_pro.core.models import LoadCase

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
    "Railway U-Girder section-type-specific flexure validation",
    "PSC shear route including prestress effects, dv policy, and end-region checks",
    "Railway U-Girder torsion and combined V+T interaction",
    "transfer length force ramp",
    "development length and debonded strand anchorage",
    "anchorage / end-zone bursting and spalling",
    "lifting insert / local hardware check",
    "creep/shrinkage and time-dependent composite redistribution",
    "independent benchmark examples and final design report traceability",
]
RAILWAY_UGIRDER_ULS_TABLE_KEYS = [
    "railway_u_girder_uls_closeout_boundary",
    "railway_u_girder_uls_code_basis",
    "railway_u_girder_uls_demand_summary",
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
    check_matrix: pd.DataFrame = field(default_factory=pd.DataFrame)
    future_checks: pd.DataFrame = field(default_factory=pd.DataFrame)
    warnings: list[str] = field(default_factory=list)

    def tables(self) -> dict[str, pd.DataFrame]:
        return {
            "railway_u_girder_uls_closeout_boundary": self.closeout_boundary,
            "railway_u_girder_uls_code_basis": self.code_basis,
            "railway_u_girder_uls_demand_summary": self.demand_summary,
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
            "Capacity / Code Route": "Bridge Beam/Girder flexure route; Railway-specific benchmark validation still required",
            "Allowed Decision Wording": "Engineering Review PASS / FAIL only after calculation evidence; not Certified PASS",
            "Blocked Final Claim": "No final design certification until Railway U-Girder flexure benchmark evidence is added.",
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
    warnings = [RAILWAY_UGIRDER_ULS_FRAMEWORK_WARNING]
    if active_uls.empty:
        warnings.append("No active ULS Loads rows were found; define Strength ULS station-resultant rows before running design checks.")
    return RailwayUGirderULSFrameworkPackage(
        available=True,
        status=RAILWAY_UGIRDER_ULS_FRAMEWORK_STATUS,
        closeout_boundary=railway_u_girder_uls_closeout_boundary_dataframe(),
        code_basis=railway_u_girder_uls_code_basis_dataframe(),
        demand_summary=railway_u_girder_uls_demand_summary_dataframe(active_uls),
        check_matrix=railway_u_girder_uls_check_matrix_dataframe(active_uls),
        future_checks=railway_u_girder_uls_future_checks_dataframe(),
        warnings=warnings,
    )
