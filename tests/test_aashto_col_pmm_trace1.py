from __future__ import annotations

import plotly.graph_objects as go

from concrete_pmm_pro.core.design_code import PROJECT_CODE_AASHTO_LRFD
from concrete_pmm_pro.ui.analysis_page import (
    _append_pmm_traceability_to_figure_title,
    _apply_pmm_traceability_to_summary,
    _pmm_traceability_context_for_code,
    _pmm_traceability_summary_cards,
)


def test_aashto_col_pmm_trace1_context_identifies_aashto_route_and_units() -> None:
    context = _pmm_traceability_context_for_code(
        "AASHTO LRFD",
        "AASHTO LRFD 9th Edition",
        mode_label="RC PMM",
        prestress_included=False,
        bonded_prestress_included=False,
    )

    assert context["code_basis"] == PROJECT_CODE_AASHTO_LRFD
    assert context["code_edition"] == "AASHTO LRFD 9th Edition"
    assert context["pmm_route"] == "AASHTO LRFD Column/Pier PMM"
    assert "Section 5" in context["flexural_basis"]
    assert "AASHTO strain-controlled" in context["phi_basis"]
    assert "ksi/kips constants converted" in context["units_basis"]
    assert context["prestress_branch"] == "Ordinary rebar only"


def test_aashto_col_pmm_trace1_prestress_branch_is_not_confused_with_aci() -> None:
    context = _pmm_traceability_context_for_code(
        "AASHTO LRFD",
        "AASHTO LRFD 9th Edition",
        mode_label="RC + Active Bonded Prestress PMM",
        prestress_included=True,
        bonded_prestress_included=True,
        unbonded_ignored_count=2,
    )

    assert context["pmm_route"] == "AASHTO LRFD Column/Pier PMM"
    assert "Bonded prestress included" in context["prestress_branch"]
    assert "unbonded ignored 2" in context["prestress_branch"]
    assert "ACI" not in context["pmm_route"]


def test_aashto_col_pmm_trace1_summary_cards_include_code_route_phi_units() -> None:
    cards = _pmm_traceability_summary_cards(
        _pmm_traceability_context_for_code(
            "AASHTO LRFD",
            "AASHTO LRFD 9th Edition",
            mode_label="RC PMM",
            prestress_included=False,
            bonded_prestress_included=False,
        )
    )
    by_title = {card["title"]: card for card in cards}

    assert by_title["Code Basis"]["value"] == "AASHTO LRFD"
    assert by_title["PMM Route"]["value"] == "AASHTO LRFD Column/Pier PMM"
    assert by_title["φ / Units Trace"]["value"] == "AASHTO strain-controlled φ transition"
    assert "ksi/kips" in by_title["φ / Units Trace"]["detail"]


def test_aashto_col_pmm_trace1_selected_case_detail_fields_are_enriched() -> None:
    base_summary = {
        "selected_combo": "ULS-1",
        "analysis_mode": "RC PMM",
        "prestress_included": False,
    }
    context = _pmm_traceability_context_for_code(
        "AASHTO LRFD",
        "AASHTO LRFD 9th Edition",
        mode_label="RC PMM",
        prestress_included=False,
        bonded_prestress_included=False,
    )
    enriched = _apply_pmm_traceability_to_summary(base_summary, context)

    assert enriched["code_basis"] == "AASHTO LRFD"
    assert enriched["code_edition"] == "AASHTO LRFD 9th Edition"
    assert enriched["pmm_route"] == "AASHTO LRFD Column/Pier PMM"
    assert enriched["phi_basis"] == "AASHTO strain-controlled φ transition"
    assert enriched["units_basis"].startswith("SI solver units")
    assert base_summary.get("code_basis") is None


def test_aashto_col_pmm_trace1_plotly_title_gets_code_basis_subtitle_and_meta() -> None:
    context = _pmm_traceability_context_for_code(
        "AASHTO LRFD",
        "AASHTO LRFD 9th Edition",
        mode_label="RC PMM",
        prestress_included=False,
        bonded_prestress_included=False,
    )
    fig = go.Figure()
    fig.update_layout(title="PMM Mux-Muy Slice")

    traced = _append_pmm_traceability_to_figure_title(fig, context)

    assert "Code basis: AASHTO LRFD 9th Edition" in traced.layout.title.text
    assert "Route: AASHTO LRFD Column/Pier PMM" in traced.layout.title.text
    assert traced.layout.meta["pmm_code_trace"]["code_basis"] == "AASHTO LRFD"
