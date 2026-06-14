from __future__ import annotations

from pathlib import Path


def test_app_uses_visual_only_commercial_tab_styles_without_new_navigation() -> None:
    source = Path("app.py").read_text(encoding="utf-8")

    assert "_COMMERCIAL_TAB_CSS" in source
    assert "_render_global_commercial_tab_styles()" in source
    assert "div[data-testid=\"stSegmentedControl\"]" in source
    assert "div[data-testid=\"stRadio\"] div[role=\"radiogroup\"]" in source
    assert "This does not add, move, or remove navigation controls" in source
    assert source.count('"Analysis": ["ULS / PMM", "SLS / Stress & Cracking", "SLS Deflection / Camber", "Report / QA"]') == 1
