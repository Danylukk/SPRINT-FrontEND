import streamlit as st

from ui_pages.chat import render_chat
from ui_pages.login import render_login

st.set_page_config(page_title="CP6 | Motor Digital Twin Chat", page_icon="💬", layout="wide")

# A navegação é derivada da autenticação; não existe histórico na sessão.
page = (st.Page(render_chat, title="Conversas", default=True) if st.session_state.get("token")
        else st.Page(render_login, title="Entrar", default=True))
st.navigation([page], position="hidden").run()
