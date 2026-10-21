import streamlit as st

from components.session import clear_session
from services.api_client import APIError


def render_conversation_list(client, conversations):
    with st.sidebar:
        st.markdown("### Motor Digital Twin")
        st.caption("CP6 · Assistente de estudos")
        st.caption(f"Conectado como {st.session_state.usuario['usuario']}")
        if st.button("Nova conversa", type="primary", use_container_width=True):
            result = client.create_conversation()
            st.session_state.conversa_ativa = result["id"]
            st.rerun()
        st.markdown("#### Suas conversas")
        if not conversations:
            st.caption("Nenhuma conversa ainda. Crie a primeira para começar.")
        for item in conversations:
            selected = item["id"] == st.session_state.get("conversa_ativa")
            if st.button(item["titulo"], key=f"conversation_{item['id']}",
                         type="primary" if selected else "secondary", use_container_width=True):
                st.session_state.conversa_ativa = item["id"]
                st.rerun()
        st.divider()
        st.caption("Histórico salvo no backend · SQLite")
        if st.button("Sair", use_container_width=True):
            try:
                client.logout()
            except APIError as error:
                if error.status_code != 401:
                    st.error("Não foi possível revogar a sessão na API. Tente sair novamente.")
                    return
            clear_session()
            st.rerun()
