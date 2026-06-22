from __future__ import annotations

from pathlib import Path

SOURCE = Path("concrete_pmm_pro/ui/prestress_page.py").read_text(encoding="utf-8")


def _plot_function_source() -> str:
    start = SOURCE.index("def _plot_girder_strand_cross_section_layout")
    end = SOURCE.index("\n\ndef ", start + 1)
    return SOURCE[start:end]


def test_strand_layout_uses_single_marker_layer_not_per_strand_shapes() -> None:
    body = _plot_function_source()

    assert 'type="circle"' not in body
    assert '"size": 8' in body
    assert "_add_strand_trace" in body


def test_strand_layout_uses_compact_row_summary_not_y_tied_labels() -> None:
    body = _plot_function_source()

    assert "Strand row summary" in body
    assert 'yref="paper"' in body
    assert 'yref="y"' not in body
    assert "label_leader_x1" not in body


def test_strand_layout_has_explicit_title_to_avoid_undefined_plot_title() -> None:
    body = _plot_function_source()

    assert "Prestress strand cross-section layout" in body
    assert '"text": "Prestress strand cross-section layout"' in body


def test_strand_layout_keeps_drawing_symbols_lightweight() -> None:
    body = _plot_function_source()

    assert '"size": 8' in body
    assert '"color": "rgba(15, 23, 42, 0.70)"' in body
    assert '"width": 1.0' in body
