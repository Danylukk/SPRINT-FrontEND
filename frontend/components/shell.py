import streamlit as st

from components.session import clear_session
from services.api_client import APIClient, APIError


def render_shell():
    with st.sidebar:
        st.markdown("**Motor Digital Twin**")
        st.caption(f"{st.session_state.usuario['usuario']} · Sprints 1–3 + CP6")
        if st.button("Sair", use_container_width=True):
            try:
                APIClient(st.session_state.token).logout()
            except APIError as error:
                if error.status_code != 401:
                    st.error("Não foi possível revogar a sessão na API. Tente novamente.")
                    return
            clear_session()
            st.rerun()
        st.divider()
