from __future__ import annotations

from concrete_pmm_pro.core.reinforcement_system import (
    ORDINARY_REBAR_FLAG_KEY,
    PRESTRESSING_STEEL_FLAG_KEY,
    ordinary_rebar_enabled,
    prestressing_steel_enabled,
)


def test_reinforcement_flags_fall_back_to_project_metadata_when_top_level_missing() -> None:
    state = {
        "project_metadata": {
            ORDINARY_REBAR_FLAG_KEY: False,
            PRESTRESSING_STEEL_FLAG_KEY: True,
        }
    }

    assert ordinary_rebar_enabled(state, default=True) is False
    assert prestressing_steel_enabled(state, default=False) is True


def test_top_level_reinforcement_flags_override_project_metadata() -> None:
    state = {
        ORDINARY_REBAR_FLAG_KEY: True,
        PRESTRESSING_STEEL_FLAG_KEY: False,
        "project_metadata": {
            ORDINARY_REBAR_FLAG_KEY: False,
            PRESTRESSING_STEEL_FLAG_KEY: True,
        },
    }

    assert ordinary_rebar_enabled(state, default=False) is True
    assert prestressing_steel_enabled(state, default=True) is False
