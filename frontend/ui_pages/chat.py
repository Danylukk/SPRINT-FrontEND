import streamlit as st

from components.conversation_list import render_conversation_list
from components.messages import render_composer, render_messages
from components.session import show_error
from services.api_client import APIClient, APIError


def render_chat():
    client = APIClient(st.session_state.token)
    try:
        conversations = client.list_conversations()
        render_conversation_list(client, conversations)
    except APIError as error:
        show_error(error)
        st.stop()

    st.title("Assistente Motor Digital Twin")
    if notice := st.session_state.pop("chat_notice", None):
        st.error(notice)
    st.caption("Bot por regras · Dados operacionais da API ao mencionar uma TAG · Conversas privadas por conta")
    st.caption("Em celulares, abra o menu lateral no canto superior esquerdo para acessar suas conversas.")
    if st.button("Atualizar histórico"):
        st.rerun()
    active = st.session_state.get("conversa_ativa")
    if active is None:
        st.info("Selecione uma conversa na barra lateral ou clique em Nova conversa.")
        st.markdown("**Experimente perguntar**\n\n- Como está o MTR-001?\n- O que é uma API?\n- Como o histórico é persistido?")
        return
    try:
        detail = client.get_conversation(active)
    except APIError as error:
        if error.status_code == 404:
            st.session_state.conversa_ativa = None
        show_error(error)
        return
    st.subheader(detail["titulo"])
    # Histórico é sempre lido por HTTP; não é armazenado na sessão do front.
    render_messages(detail["mensagens"])
    if content := render_composer():
        if not content.strip():
            st.warning("Digite uma mensagem antes de enviar.")
            return
        try:
            with st.spinner("Aguardando a API..."):
                client.send_message(active, content)
            st.rerun()
        except APIError as error:
            show_error(error)
