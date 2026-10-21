"""Páginas integradas das sprints: apresentação e HTTP, sem persistência ou inferência local."""
from functools import wraps
from types import SimpleNamespace

import pandas as pd
import streamlit as st

from components.motor import equipment_to_dataframe, render_equipment_card, render_simulated_nameplate
from components.motor_alerts import (
    render_alert_card, render_decision_support, render_equipment_states,
    render_event_history, render_intelligence_kpis,
)
from components.motor_details import render_technical_sheet, render_telemetry_charts
from components.session import show_error
from navigation import open_chat
from services.api_client import APIClient, APIError


def api_page(function):
    @wraps(function)
    def wrapped():
        try:
            return function(APIClient(st.session_state.token))
        except APIError as error:
            show_error(error)
    return wrapped


def objects(items):
    return [SimpleNamespace(**item) for item in items]


def talk_about(client, equipment):
    if st.button(f"Conversar sobre {equipment.tag}", type="primary"):
        conversation = client.create_conversation()
        st.session_state.conversa_ativa = conversation["id"]
        # Navega mesmo se o provider falhar: a conversa pode ser retomada sem repetir a criação.
        try:
            client.send_message(conversation["id"], f"Como está o equipamento {equipment.tag}?")
        except APIError as error:
            st.session_state["chat_notice"] = str(error)
            open_chat()
        open_chat()


@api_page
def render_dashboard(client):
    st.title("Dashboard")
    st.write("Motor Digital Twin · Sprints 1–3 e CP6 no mesmo sistema.")
    fleet = objects(client.fleet())
    cols = st.columns(4)
    cols[0].metric("Ativos cadastrados", len(fleet))
    cols[1].metric("Operacionais", sum(item.status_operacional == "Operacional" for item in fleet))
    cols[2].metric("Em atenção", sum(item.status_operacional == "Atenção" for item in fleet))
    cols[3].metric("Críticos / Inativos", sum(item.status_operacional in {"Crítico", "Inativo"} for item in fleet))
    st.info("Use o menu lateral para acessar todos os módulos. Na consulta de equipamentos, abra o assistente pela TAG.")
    st.subheader("Cadastro consolidado")
    if fleet:
        st.dataframe(equipment_to_dataframe(fleet), hide_index=True, use_container_width=True)
        st.subheader("Destaques do cadastro")
        for item in fleet[:3]:
            render_equipment_card(item)
    else:
        st.info("Nenhum equipamento cadastrado.")


@api_page
def render_alerts(client):
    st.title("Painel de Alertas e Estados")
    include = st.checkbox("Incluir histórico de referência versionado", value=False)
    data = client.motor_panel(include)
    if not data["equipamentos"]:
        st.info("Cadastre um equipamento para iniciar o monitoramento.")
        return
    tags = [item["tag"] for item in data["equipamentos"]]
    tag = st.selectbox("Equipamento da DEMO", tags, index=tags.index("MTR-001") if "MTR-001" in tags else 0)
    if st.button("↻ Atualizar informações", type="primary", use_container_width=True):
        result = client.motor_refresh(tag, demo=True)
        st.success(result["mensagem"])
        data = client.motor_panel(include)
    snapshots = objects(data["snapshots"])
    render_intelligence_kpis(snapshots)
    st.caption("Estado analítico e leitura vêm do backend. Atualizar informações alterna a DEMO saudável/crítico da Sprint 3.")
    st.subheader("Alertas prioritários")
    priorities = {"Crítico": 0, "Atenção": 1, "Indisponível": 2, "Saudável": 3}
    alerts = sorted((item for item in snapshots if item.status != "Saudável"), key=lambda item: priorities[item.status])
    for item in alerts[:4]:
        render_alert_card(item)
    if not alerts:
        st.success("Nenhum desvio nas leituras disponíveis.")
    st.info("RulesAnalyticsProvider e mock_nlp preservados das sprints. Leituras simuladas, sem ML ou NLP real.")
    st.subheader("Estado analítico dos equipamentos")
    render_equipment_states(snapshots)
    st.subheader("Apoio inicial à decisão")
    render_decision_support(snapshots)
    st.subheader("Histórico de eventos")
    render_event_history(objects(data["eventos"]))


def select_equipment(client, label, key):
    fleet = client.fleet()
    if not fleet:
        st.info("Nenhum equipamento cadastrado.")
        return None
    tag = st.selectbox(label, [item["tag"] for item in fleet], key=key)
    return client.motor_detail(tag)


def reading_metrics(snapshot):
    reading = snapshot["reading"]
    specs = [("Temperatura", "temperatura_c", "°C"), ("Vibração", "vibracao_mm_s", "mm/s"),
             ("Corrente", "corrente_a", "A"), ("Rotação", "rotacao_rpm", "RPM")]
    for column, (label, key, unit) in zip(st.columns(4), specs):
        value = reading[key]
        column.metric(label, "Indisponível" if value is None else f"{value:g} {unit}")
    st.caption(f"Última leitura: {snapshot['timestamp']} · Origem: {snapshot['source']} · ID: {snapshot['reading_id']}")
    if snapshot["is_stale"]:
        st.warning("Dados desatualizados. A idade da leitura não é tratada como anomalia.")


@api_page
def render_operational(client):
    st.title("Dashboard Operacional")
    fleet = client.fleet()
    if not fleet:
        st.info("Nenhum equipamento cadastrado.")
        return
    area = st.selectbox("Selecione a área/planta", sorted({item["local_instalacao"] for item in fleet}))
    tag = st.selectbox("Selecione a TAG", [item["tag"] for item in fleet if item["local_instalacao"] == area])
    if st.button("Gerar nova leitura simulada", use_container_width=True):
        result = client.motor_refresh(tag)
        st.success(result["mensagem"])
    data = client.motor_detail(tag)
    render_equipment_card(SimpleNamespace(**data["equipamento"]))
    st.subheader("Telemetria atual")
    reading_metrics(data["snapshot"])
    render_alert_card(SimpleNamespace(**data["snapshot"]))
    chart_data = pd.DataFrame(data["historico"])
    if not chart_data.empty:
        chart_data["timestamp"] = pd.to_datetime(chart_data["timestamp"])
    st.subheader("Histórico temporal")
    render_telemetry_charts(chart_data)
    st.subheader("Placa do Motor")
    render_simulated_nameplate(SimpleNamespace(**data["equipamento"]))
    talk_about(client, SimpleNamespace(**data["equipamento"]))


@api_page
def render_registration(client):
    st.title("Cadastro Técnico")
    st.caption("Campos obrigatórios. Cadastro compartilhado entre as contas do projeto; gravação no backend.")
    version = st.session_state.get("equipment_form_version", 0)
    with st.form(f"equipment_form_{version}", clear_on_submit=False):
        left, right = st.columns(2)
        with left:
            tag = st.text_input("TAG de identificação *")
            model = st.text_input("Modelo *")
            maker = st.text_input("Fabricante *")
            power = st.number_input("Potência *", min_value=0.0, step=0.5)
            unit = st.selectbox("Unidade da potência *", ["kW", "CV"])
        with right:
            voltage = st.number_input("Tensão em V *", min_value=0.0, step=10.0)
            current = st.number_input("Corrente nominal em A *", min_value=0.0, step=0.5)
            rpm = st.number_input("Rotação nominal em RPM *", min_value=0.0, step=50.0)
            place = st.text_input("Local de instalação *")
            status = st.selectbox("Status operacional *", ["Operacional", "Atenção", "Crítico", "Inativo"])
        notes = st.text_area("Observações *")
        confirm = st.checkbox("Confirmo que revisei os dados e desejo salvar este cadastro.")
        submitted = st.form_submit_button("Salvar equipamento", type="primary")
    if submitted:
        if not confirm:
            st.warning("Confirme a gravação antes de salvar o cadastro.")
            return
        result = client.register_equipment({"tag": tag, "modelo": model, "fabricante": maker,
            "potencia": power, "unidade_potencia": unit, "tensao": voltage, "corrente_nominal": current,
            "rotacao_nominal": rpm, "local_instalacao": place, "status_operacional": status,
            "observacoes": notes, "confirmar": confirm})
        st.success(f"Equipamento {result['tag']} cadastrado com sucesso.")
        st.info("Disponível no dashboard, consulta, telemetria, alertas e assistente pela TAG.")
    with st.expander("Limpeza do formulário"):
        st.warning("Confirme antes de limpar os dados preenchidos.")
        clear = st.checkbox("Confirmo que desejo limpar os dados preenchidos.")
        if st.button("Limpar tela de cadastro", disabled=not clear):
            st.session_state.equipment_form_version = version + 1
            st.rerun()


@api_page
def render_equipment_query(client):
    st.title("Consulta de Equipamentos")
    data = select_equipment(client, "Selecione a TAG", "query_tag")
    if data:
        equipment = SimpleNamespace(**data["equipamento"])
        render_technical_sheet(equipment)
        st.subheader("Estado operacional na API")
        reading_metrics(data["snapshot"])
        talk_about(client, equipment)


@api_page
def render_raw(client):
    st.title("Dados Brutos")
    data = select_equipment(client, "Selecione o ativo monitorado", "raw_tag")
    if data:
        raw = client.raw_sensors(data["equipamento"]["tag"])
        st.warning(raw["origem"])
        for column, row in zip(st.columns(3), raw["tabela"]):
            column.metric(row["sensor"], row["convertido"])
        st.subheader("Tabela de conversão simulada")
        st.dataframe(pd.DataFrame(raw["tabela"]).rename(columns={"sensor": "Nome do sensor", "bruto": "Valor bruto",
            "formula": "Fórmula/conversão aplicada", "convertido": "Valor convertido"}),
            hide_index=True, use_container_width=True)
        st.caption("As fórmulas da Sprint 1 são executadas no backend. Não há ESP32 ou MQTT conectado.")


def render_about():
    st.title("Sobre o Projeto")
    st.markdown("""**Motor Digital Twin · Sprints 1–3 + CP6**

- Sprint 1: cadastro, consulta por TAG, ficha técnica, placa simulada e conversão de dados brutos.
- Sprint 2: dashboard por área, telemetria simulada e gráficos históricos.
- Sprint 3: estados, DEMO saudável/crítico, eventos, RulesAnalyticsProvider e mock_nlp.
- CP6: API em camadas, login, autorização, múltiplas conversas SQLite e assistente integrado pela TAG.

Todo o sistema usa a mesma navegação e autenticação. O front acessa os dados exclusivamente pelo cliente HTTP.
Equipamentos são compartilhados no projeto; conversas são privadas por usuário.
As simulações e regras são acadêmicas, sem sensores reais, ML, NLP real ou LLM externo.
""")
