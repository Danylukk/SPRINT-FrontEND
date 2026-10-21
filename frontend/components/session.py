import streamlit as st

from services.api_client import APIError


def clear_session():
    for key in list(st.session_state):
        del st.session_state[key]


def show_error(error: APIError):
    if error.status_code == 401:
        clear_session()
        st.warning(str(error))
        if st.button("Voltar para o login", type="primary"):
            st.rerun()
        st.stop()
    st.error(str(error))
    if st.button("Tentar novamente"):
        # Recarrega a leitura; nunca repete automaticamente um POST.
        st.rerun()
