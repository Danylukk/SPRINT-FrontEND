import streamlit as st

from components.motor import inject_global_styles
from components.shell import render_shell
from navigation import PAGES
from ui_pages.chat import render_chat
from ui_pages.login import render_login
from ui_pages.motor import (
    render_alerts, render_dashboard, render_equipment_query, render_operational,
    render_raw, render_registration, render_about,
)

st.set_page_config(page_title="Motor Digital Twin | Sprints + CP6", page_icon="⚙️", layout="wide")
inject_global_styles()

if not st.session_state.get("token"):
    st.navigation([st.Page(render_login, title="Entrar", default=True)], position="hidden").run()
else:
    render_shell()
    PAGES.clear()
    PAGES.update({
        "dashboard": st.Page(render_dashboard, title="Dashboard", default=True),
        "alerts": st.Page(render_alerts, title="Painel de Alertas e Estados", url_path="alertas"),
        "operational": st.Page(render_operational, title="Dashboard Operacional", url_path="operacional"),
        "register": st.Page(render_registration, title="Cadastro Técnico", url_path="cadastro"),
        "query": st.Page(render_equipment_query, title="Consulta de Equipamentos", url_path="equipamentos"),
        "raw": st.Page(render_raw, title="Dados Brutos", url_path="sensores"),
        "chat": st.Page(render_chat, title="Assistente IA", url_path="chat"),
        "about": st.Page(render_about, title="Sobre o Projeto", url_path="sobre"),
    })
    st.navigation({"Monitoramento": [PAGES["dashboard"], PAGES["alerts"], PAGES["operational"]],
                   "Equipamentos": [PAGES["register"], PAGES["query"], PAGES["raw"]],
                   "Assistente e projeto": [PAGES["chat"], PAGES["about"]]}).run()
