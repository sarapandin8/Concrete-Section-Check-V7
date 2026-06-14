"""Navigation helpers for Concrete Section Pro UI.

These helpers render existing app navigation choices with deterministic active
state styling.  They intentionally do not change the available navigation
options or execute inactive workspaces.
"""

from __future__ import annotations

from html import escape
import re

import streamlit as st


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip()).strip("_").lower()
    return slug or "option"


def render_active_choice(label: str, options: list[str], *, key: str, horizontal: bool = True) -> str:
    """Render a deterministic tab-like navigation choice.

    Streamlit segmented controls have version-dependent selected-state DOM.
    This renderer uses the app's own ``session_state`` value to draw the active
    option as a styled pill, while inactive options remain real buttons.  The
    result is predictable active-tab highlighting without relying on fragile CSS
    selectors for Streamlit internals.  The visual tab cluster is kept compact
    and left-aligned so it reads as navigation instead of full-width action
    buttons.
    """

    if not options:
        raise ValueError("Navigation options must not be empty.")

    if st.session_state.get(key) not in options:
        st.session_state[key] = options[0]
    active = str(st.session_state.get(key, options[0]))

    st.markdown(f'<div class="cpmm-nav-label">{escape(label)}</div>', unsafe_allow_html=True)
    st.markdown('<div class="cpmm-deterministic-nav-row cpmm-deterministic-nav-row--compact">', unsafe_allow_html=True)

    if horizontal:
        # UI.ACTIVE.TABS2: keep the existing navigation location/choices, but
        # stop stretching each tab across the full viewport.  The trailing
        # spacer column leaves the tab cluster compact and left-aligned like a
        # commercial desktop tab bar, while each tab remains a real Streamlit
        # button for stable state handling.
        # UI.ACTIVE.TABS3 tightens the cluster further.  Keep each option close
        # to text width and push the unused page width into a large trailing
        # spacer so the nav reads as a tab strip rather than action buttons.
        tab_widths = [max(0.62, min(1.08, 0.42 + len(option) / 22.0)) for option in options]
        trailing_spacer = max(9.5, 17.0 - sum(tab_widths))
        columns = st.columns([*tab_widths, trailing_spacer], gap="small")[: len(options)]
    else:
        columns = [st.container() for _ in options]

    for index, option in enumerate(options):
        option_text = str(option)
        widget_key = f"{key}__nav_button__{_slug(option_text)}"
        with columns[index]:
            if option_text == active:
                st.markdown(
                    f'<div class="cpmm-nav-tab-pill cpmm-nav-tab-active" aria-current="page">{escape(option_text)}</div>',
                    unsafe_allow_html=True,
                )
            else:
                clicked = st.button(
                    option_text,
                    key=widget_key,
                    use_container_width=True,
                    help=f"Go to {option_text}",
                )
                if clicked:
                    st.session_state[key] = option_text
                    rerun = getattr(st, "rerun", None)
                    if callable(rerun):
                        rerun()
                    return option_text

    st.markdown('</div>', unsafe_allow_html=True)
    return active
