from __future__ import annotations

from pathlib import Path


SOURCE = Path("concrete_pmm_pro/ui/analysis_page.py").read_text(encoding="utf-8")
APP_SOURCE = Path("app.py").read_text(encoding="utf-8")


def test_beam_uls_diagram_render_avoids_backend_kaleido_export() -> None:
    start = SOURCE.index("def _render_beam_uls_static_plotly_figure")
    end = SOURCE.index("\n\nBEAM_ULS_CHECK_TAB_LABELS", start)
    body = SOURCE[start:end]

    assert "fig.to_image(" not in body
    assert "st.image(image_bytes" not in body
    assert "st.plotly_chart(" in body
    assert "STATE.RESULT.PERSIST3A" in body


def test_result_summary_diagram_render_avoids_backend_kaleido_export() -> None:
    start = APP_SOURCE.index("def _render_results_static_plotly_figure")
    end = APP_SOURCE.index("\n\ndef _results_available_diagram_figures", start)
    body = APP_SOURCE[start:end]

    assert "fig.to_image(" not in body
    assert "st.image(image_bytes" not in body
    assert "st.plotly_chart(" in body
