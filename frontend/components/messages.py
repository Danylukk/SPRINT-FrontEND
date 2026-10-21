import streamlit as st


def render_messages(messages):
    if not messages:
        st.info("Sua conversa está pronta. Envie uma mensagem abaixo.")
    for message in messages:
        with st.chat_message(message["papel"]):
            st.markdown(message["conteudo"])


def render_composer():
    return st.chat_input("Pergunte sobre APIs, persistência ou motores...", max_chars=4000)
