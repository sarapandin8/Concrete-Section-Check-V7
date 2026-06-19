"""Global Plotly readability polish for Concrete Section Pro UI figures.

UI.PLOT5 applies presentation-only defaults to every Plotly figure rendered by
``st.plotly_chart``.  It deliberately does not alter figure data, calculated
values, trace coordinates, result tables, solver logic, or project state.
"""

from __future__ import annotations

from typing import Any

try:  # pragma: no cover - import guard for non-Plotly documentation builds
    import plotly.graph_objects as go
except Exception:  # pragma: no cover
    go = None  # type: ignore[assignment]

_CP_FONT_FAMILY = "Arial, Inter, Segoe UI, sans-serif"
_CP_TEXT = "#0f172a"
_CP_TEXT_SOFT = "#1f2937"
_CP_GRID = "rgba(15,23,42,0.13)"
_CP_AXIS = "rgba(15,23,42,0.78)"
_CP_LEGEND_BORDER = "rgba(15,23,42,0.18)"
_CP_LEGEND_BG = "rgba(255,255,255,0.94)"


def apply_global_plot_readability(fig: Any) -> Any:
    """Make a Plotly figure text/axes/legend easier to read in the app.

    This is intentionally a soft global style layer.  Existing figure-specific
    settings remain mostly intact, but labels that were too small or too pale get
    a stronger minimum font treatment.  Trace data and engineering calculations
    are not touched.
    """

    if go is None or not isinstance(fig, go.Figure):
        return fig

    # Layout-level defaults.  Keep existing title text/height/margins unless a
    # given figure already overrides them, but strengthen the text color/size.
    fig.update_layout(
        font={"family": _CP_FONT_FAMILY, "size": 14, "color": _CP_TEXT},
        title_font={"family": _CP_FONT_FAMILY, "size": 20, "color": _CP_TEXT},
        legend={
            "font": {"family": _CP_FONT_FAMILY, "size": 13, "color": _CP_TEXT},
            "bgcolor": _CP_LEGEND_BG,
            "bordercolor": _CP_LEGEND_BORDER,
            "borderwidth": 1,
            "itemsizing": "constant",
        },
        hoverlabel={
            "font": {"family": _CP_FONT_FAMILY, "size": 13},
            "bgcolor": "#ffffff",
            "bordercolor": "rgba(15,23,42,0.22)",
        },
    )

    fig.update_xaxes(
        tickfont={"family": _CP_FONT_FAMILY, "size": 13, "color": _CP_TEXT_SOFT},
        title_font={"family": _CP_FONT_FAMILY, "size": 15, "color": _CP_TEXT},
        gridcolor=_CP_GRID,
        linecolor=_CP_AXIS,
        zerolinecolor="rgba(15,23,42,0.42)",
    )
    fig.update_yaxes(
        tickfont={"family": _CP_FONT_FAMILY, "size": 13, "color": _CP_TEXT_SOFT},
        title_font={"family": _CP_FONT_FAMILY, "size": 15, "color": _CP_TEXT},
        gridcolor=_CP_GRID,
        linecolor=_CP_AXIS,
        zerolinecolor="rgba(15,23,42,0.42)",
    )

    # Plotly 3D/ternary/polar figures do not use normal x/y axes.  Strengthen the
    # common 3D scene labels without assuming every figure owns a scene.
    try:
        fig.update_scenes(
            xaxis={
                "tickfont": {"family": _CP_FONT_FAMILY, "size": 12, "color": _CP_TEXT_SOFT},
                "title": {"font": {"family": _CP_FONT_FAMILY, "size": 13, "color": _CP_TEXT}},
                "gridcolor": _CP_GRID,
                "linecolor": _CP_AXIS,
            },
            yaxis={
                "tickfont": {"family": _CP_FONT_FAMILY, "size": 12, "color": _CP_TEXT_SOFT},
                "title": {"font": {"family": _CP_FONT_FAMILY, "size": 13, "color": _CP_TEXT}},
                "gridcolor": _CP_GRID,
                "linecolor": _CP_AXIS,
            },
            zaxis={
                "tickfont": {"family": _CP_FONT_FAMILY, "size": 12, "color": _CP_TEXT_SOFT},
                "title": {"font": {"family": _CP_FONT_FAMILY, "size": 13, "color": _CP_TEXT}},
                "gridcolor": _CP_GRID,
                "linecolor": _CP_AXIS,
            },
        )
    except Exception:
        pass

    # Strengthen annotation text used by governing labels and limit labels.  Do
    # not move annotations or alter their engineering content.
    for annotation in getattr(fig.layout, "annotations", ()) or ():
        try:
            font_obj = getattr(annotation, "font", None)
            font = font_obj.to_plotly_json() if hasattr(font_obj, "to_plotly_json") else dict(font_obj or {})
            font.setdefault("family", _CP_FONT_FAMILY)
            font["size"] = max(int(font.get("size") or 0), 12)
            font.setdefault("color", _CP_TEXT)
            annotation.font = font
        except Exception:
            continue

    return fig


def install_streamlit_plotly_readability_patch(st_module: Any) -> None:
    """Patch ``st.plotly_chart`` once so every UI chart gets readable text.

    The wrapper is intentionally installed in ``app.py`` rather than inside each
    page.  That keeps coverage broad across Analysis, Sections, Prestress, Rebar,
    Reports, and future pages without changing widget keys or rendering order.
    """

    if bool(getattr(st_module, "_cpmm_plot_readability_patch_installed", False)):
        return

    original_plotly_chart = st_module.plotly_chart

    def _cpmm_plotly_chart_with_readability(figure_or_data: Any = None, *args: Any, **kwargs: Any) -> Any:
        apply_global_plot_readability(figure_or_data)
        return original_plotly_chart(figure_or_data, *args, **kwargs)

    st_module._cpmm_original_plotly_chart = original_plotly_chart
    st_module.plotly_chart = _cpmm_plotly_chart_with_readability
    st_module._cpmm_plot_readability_patch_installed = True
