import streamlit as st

from services.api_client import APIClient, APIError


def render_login():
    st.title("Motor Digital Twin · Chat")
    st.write("Um espaço para organizar suas conversas sobre tecnologia e motores.")
    st.caption("CP6 · Front-end em Sistemas de IA · FastAPI + Streamlit")
    st.info("Bot simulado por regras. Funciona sem chave de IA e não consulta sensores reais.")
    client = APIClient()
    try:
        health = client.health()
        st.caption(f"API conectada · Provider: {health['provider']} · Modelo: {health['modelo']}")
        if health["status"] != "ok":
            st.warning("A API está acessível, mas o modelo está indisponível.")
    except APIError as error:
        st.warning(str(error))
    login_tab, register_tab = st.tabs(["Entrar", "Criar conta"])
    with login_tab:
        with st.form("login", clear_on_submit=True):
            username = st.text_input("Usuário", max_chars=40)
            password = st.text_input("Senha", type="password", max_chars=128)
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        if submitted:
            try:
                result = client.login(username.strip(), password)
                st.session_state.token = result["access_token"]
                st.session_state.usuario = result["usuario"]
                st.session_state.conversa_ativa = None
                st.rerun()
            except APIError as error:
                st.error("Usuário ou senha inválidos." if error.status_code == 401 else str(error))
    with register_tab:
        st.caption("Use um nome de usuário de 3 a 40 caracteres (letras, números, ponto, _ ou -) "
                   "e uma senha de 8 a 128 caracteres. Para avaliar o isolamento, crie duas contas.")
        with st.form("register", clear_on_submit=True):
            username = st.text_input("Novo usuário", max_chars=40)
            password = st.text_input("Nova senha", type="password", max_chars=128)
            submitted = st.form_submit_button("Criar conta", use_container_width=True)
        if submitted:
            try:
                client.register(username.strip(), password)
                st.success("Conta criada. Use a aba Entrar para acessar.")
            except APIError as error:
                st.error(str(error))
