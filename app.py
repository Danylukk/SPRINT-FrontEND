import streamlit as st

from src.ui.sprint3_pages import render_app


def main() -> None:
    st.set_page_config(
        page_title="Sprint 3 | Motor Digital Twin",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    render_app()


if __name__ == "__main__":
    main()
