"""Navigation helpers for Concrete PMM Pro UI.

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
    selectors for Streamlit internals.
    """

    if not options:
        raise ValueError("Navigation options must not be empty.")

    if st.session_state.get(key) not in options:
        st.session_state[key] = options[0]
    active = str(st.session_state.get(key, options[0]))

    st.markdown(f'<div class="cpmm-nav-label">{escape(label)}</div>', unsafe_allow_html=True)
    st.markdown('<div class="cpmm-deterministic-nav-row">', unsafe_allow_html=True)

    if horizontal:
        widths = [max(1.25, min(3.0, 0.35 + len(option) / 7.5)) for option in options]
        columns = st.columns(widths)
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
