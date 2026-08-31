import time
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from src.models.equipment import Equipment
from src.services.alert_service import AlertResult, AlertService
from src.services.equipment_service import EquipmentService, EquipmentValidationError
from src.services.sensor_service import (
    build_sensor_table,
    convert_raw_sensor_data,
    simulate_raw_sensor_data,
)
from src.services.telemetry_service import TelemetryService
from src.ui.components import (
    equipment_to_dataframe,
    inject_global_styles,
    render_empty_state,
    render_equipment_card,
    render_health_indicator,
    render_operational_message,
    render_simulated_nameplate,
    render_telemetry_card,
    status_badge_html,
)


MENU_OPTIONS = [
    "Dashboard",
    "Dashboard Operacional",
    "Cadastro Técnico",
    "Consulta de Equipamentos",
    "Dados Brutos",
    "Sobre o Projeto",
]


def render_app() -> None:
    inject_global_styles()
    service = EquipmentService()

    with st.sidebar:
        st.title("Motor Digital Twin")
        st.caption("Sprint 2 | Dashboard operacional de ativos")
        selected_page = st.radio("Menu principal", MENU_OPTIONS)
        st.divider()
        st.caption("Persistência local em JSON e CSV")

    if selected_page == "Dashboard":
        render_dashboard(service)
    elif selected_page == "Dashboard Operacional":
        render_operational_dashboard(service)
    elif selected_page == "Cadastro Técnico":
        render_registration_page(service)
    elif selected_page == "Consulta de Equipamentos":
        render_equipment_query_page(service)
    elif selected_page == "Dados Brutos":
        render_raw_data_page(service)
    else:
        render_about_page()


def render_dashboard(service: EquipmentService) -> None:
    st.title("Dashboard")
    st.write("Visão geral dos ativos cadastrados.")

    with st.spinner("Carregando indicadores dos equipamentos..."):
        time.sleep(0.3)
        equipments = service.list_equipments()

    total = len(equipments)
    operational = sum(1 for item in equipments if item.status_operacional == "Operacional")
    attention = sum(1 for item in equipments if item.status_operacional == "Atenção")
    critical = sum(1 for item in equipments if item.status_operacional in {"Crítico", "Inativo"})

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ativos cadastrados", total)
    col2.metric("Operacionais", operational)
    col3.metric("Em atenção", attention)
    col4.metric("Críticos/Inativos", critical)

    st.divider()
    st.subheader("Equipamentos recentes")
    if equipments:
        st.dataframe(equipment_to_dataframe(equipments), width="stretch", hide_index=True)
    else:
        render_empty_state("Nenhum equipamento cadastrado.")


def render_operational_dashboard(service: EquipmentService) -> None:
    st.title("Dashboard Operacional")
    st.write("Monitore os ativos por área, com telemetria simulada, histórico local e alertas visuais.")

    telemetry_service = TelemetryService()
    alert_service = AlertService()

    with st.spinner("Carregando ativos e histórico operacional..."):
        time.sleep(0.3)
        equipments = service.list_equipments()
        telemetry_service.ensure_history(equipments)

    if not equipments:
        render_empty_state("Cadastre um equipamento para visualizar o dashboard operacional.")
        return

    areas = sorted({equipment.local_instalacao for equipment in equipments if equipment.local_instalacao})
    selected_area = st.selectbox("Selecione a área/planta", areas)
    area_equipments = [
        equipment for equipment in equipments if equipment.local_instalacao == selected_area
    ]

    if not area_equipments:
        render_empty_state("Nenhum equipamento encontrado para a área selecionada.")
        return

    tag_options = [equipment.tag for equipment in area_equipments]
    selected_tag = st.selectbox("Selecione a TAG", tag_options)
    selected_equipment = next(
        (equipment for equipment in area_equipments if equipment.tag == selected_tag), None
    )

    if not selected_equipment:
        st.error("Equipamento não encontrado.")
        return

    if st.button("Gerar nova leitura simulada", width="stretch"):
        telemetry_service.append_current_snapshot(selected_equipment)
        st.toast("Nova leitura simulada adicionada ao histórico.", icon="✅")

    current_reading = telemetry_service.get_current_reading(selected_equipment)
    alerts = alert_service.evaluate_all(
        current_reading, selected_equipment.corrente_nominal
    )
    chart_data = telemetry_service.prepare_chart_data(selected_equipment)

    st.divider()
    render_operational_asset_header(selected_equipment)

    st.subheader("Saúde operacional")
    render_health_indicator(str(alerts["geral"]))

    render_operational_message(
        "As leituras são simuladas e gravadas no histórico local de execução, preservando o CSV de referência versionado para validar fluxo, histórico e alertas antes da integração com sensores reais."
    )

    st.subheader("Telemetria atual")
    render_telemetry_cards(current_reading, alerts, selected_equipment)

    latest_timestamp = pd.to_datetime(current_reading["timestamp"], errors="coerce")
    if pd.notna(latest_timestamp):
        st.caption(f"Última atualização do histórico: {latest_timestamp:%d/%m/%Y %H:%M:%S}")

    st.subheader("Histórico temporal")
    render_telemetry_charts(chart_data)

    st.subheader("Placa do Motor")
    render_simulated_nameplate(selected_equipment)


def render_operational_asset_header(equipment: Equipment) -> None:
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1.2])
    col1.metric("TAG", equipment.tag)
    col2.metric("Modelo", equipment.modelo)
    col3.metric("Fabricante", equipment.fabricante)
    with col4:
        st.markdown(
            f"""
            <div class="info-section">
                <h4>Cadastro e local</h4>
                <p><strong>Status:</strong> {status_badge_html(equipment.status_operacional)}</p>
                <p><strong>Local:</strong> {escape(equipment.local_instalacao)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_telemetry_cards(
    reading: dict, alerts: dict[str, AlertResult | str], equipment: Equipment
) -> None:
    temp_alert = alerts["temperatura"]
    vibration_alert = alerts["vibracao"]
    current_alert = alerts["corrente"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_telemetry_card(
            "Temperatura",
            f"{reading['temperatura_c']:.1f} °C",
            temp_alert.status,
            temp_alert.message,
        )
    with col2:
        render_telemetry_card(
            "Vibração",
            f"{reading['vibracao_mm_s']:.2f} mm/s",
            vibration_alert.status,
            vibration_alert.message,
        )
    with col3:
        render_telemetry_card(
            "Corrente",
            f"{reading['corrente_a']:.2f} A",
            current_alert.status,
            current_alert.message,
        )
    with col4:
        render_telemetry_card(
            "Rotação",
            f"{reading['rotacao_rpm']:.0f} RPM",
            str(alerts["geral"]),
            f"Referência nominal: {equipment.rotacao_nominal:g} RPM.",
        )


def render_telemetry_charts(chart_data: pd.DataFrame) -> None:
    if chart_data.empty:
        render_empty_state("Histórico ainda não disponível para esta TAG.")
        return

    chart_data = chart_data.sort_values("timestamp")
    chart_specs = [
        ("temperatura_c", "Temperatura (°C)", "#f97316"),
        ("vibracao_mm_s", "Vibração (mm/s)", "#38bdf8"),
        ("corrente_a", "Corrente (A)", "#22c55e"),
    ]

    for column, title, color in chart_specs:
        fig = px.line(
            chart_data,
            x="timestamp",
            y=column,
            markers=True,
            title=title,
        )
        fig.update_traces(line_color=color, marker_color=color)
        fig.update_layout(
            template="plotly_dark",
            margin=dict(l=10, r=10, t=48, b=10),
            height=300,
            xaxis_title="Horário",
            yaxis_title=title,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.5)",
        )
        st.plotly_chart(fig, width="stretch")


def render_registration_page(service: EquipmentService) -> None:
    st.title("Cadastro Técnico")
    st.write("Cadastre motores e equipamentos com os dados necessários para consulta técnica.")
    st.caption("Os campos com * são obrigatórios. A gravação exige confirmação humana antes do salvamento.")

    if "equipment_form_version" not in st.session_state:
        st.session_state.equipment_form_version = 0

    def form_key(field_name: str) -> str:
        return f"equipment_{field_name}_{st.session_state.equipment_form_version}"

    with st.form("equipment_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            tag = st.text_input("TAG de identificação *", placeholder="Ex.: MTR-001", key=form_key("tag"))
            modelo = st.text_input("Modelo *", placeholder="Ex.: W22 IR3", key=form_key("modelo"))
            fabricante = st.text_input("Fabricante *", placeholder="Ex.: WEG", key=form_key("fabricante"))
            potencia = st.number_input(
                "Potência *", min_value=0.0, step=0.5, format="%.2f", key=form_key("potencia")
            )
            unidade_potencia = st.selectbox(
                "Unidade da potência *", ["kW", "CV"], key=form_key("unidade_potencia")
            )
        with col2:
            tensao = st.number_input(
                "Tensão em V *", min_value=0.0, step=10.0, format="%.2f", key=form_key("tensao")
            )
            corrente = st.number_input(
                "Corrente nominal em A *",
                min_value=0.0,
                step=0.5,
                format="%.2f",
                key=form_key("corrente"),
            )
            rotacao = st.number_input(
                "Rotação nominal em RPM *",
                min_value=0.0,
                step=50.0,
                format="%.2f",
                key=form_key("rotacao"),
            )
            local = st.text_input(
                "Local de instalação *", placeholder="Ex.: Linha de Produção A", key=form_key("local")
            )
            status = st.selectbox(
                "Status operacional *",
                ["Operacional", "Atenção", "Crítico", "Inativo"],
                key=form_key("status"),
            )

        observacoes = st.text_area(
            "Observações *",
            placeholder="Registre detalhes técnicos relevantes.",
            key=form_key("observacoes"),
        )
        confirm_save = st.checkbox(
            "Confirmo que revisei os dados e desejo salvar este cadastro.",
            key=form_key("confirm_save"),
        )

        submitted = st.form_submit_button("Salvar equipamento", type="primary", width="stretch")

    if submitted:
        payload = {
            "tag": tag,
            "modelo": modelo,
            "fabricante": fabricante,
            "potencia": potencia,
            "unidade_potencia": unidade_potencia,
            "tensao": tensao,
            "corrente_nominal": corrente,
            "rotacao_nominal": rotacao,
            "local_instalacao": local,
            "status_operacional": status,
            "observacoes": observacoes,
        }
        with st.spinner("Validando e salvando equipamento..."):
            time.sleep(0.3)
            try:
                equipment = service.create_equipment(payload, confirm_save=confirm_save)
            except EquipmentValidationError as error:
                st.error(str(error))
            else:
                st.success(f"Equipamento {equipment.tag} cadastrado com sucesso.")
                st.info("O cadastro já está disponível na consulta, nos dados brutos e no dashboard operacional.")

    with st.expander("Limpeza do formulário"):
        st.warning("Para evitar perda acidental de informações digitadas, confirme antes de limpar.")
        confirm_clear = st.checkbox("Confirmo que desejo limpar os dados preenchidos.", key="confirm_clear")
        if st.button("Limpar tela de cadastro", disabled=not confirm_clear):
            st.session_state.equipment_form_version += 1
            st.rerun()


def render_equipment_query_page(service: EquipmentService) -> None:
    st.title("Consulta de Equipamentos")
    st.write("Consulte os ativos cadastrados e abra a ficha técnica individual.")

    with st.spinner("Consultando arquivo local de equipamentos..."):
        time.sleep(0.3)
        equipments = service.list_equipments()

    if not equipments:
        render_empty_state("Nenhum equipamento cadastrado.")
        return

    df = equipment_to_dataframe(equipments)
    st.dataframe(df, width="stretch", hide_index=True)

    selected_tag = st.selectbox("Selecione um equipamento para abrir a ficha técnica", df["TAG"].tolist())
    selected_equipment = service.get_by_tag(selected_tag)

    if selected_equipment:
        st.divider()
        render_technical_sheet(selected_equipment)


def render_technical_sheet(equipment: Equipment) -> None:
    st.subheader("Ficha técnica")
    render_equipment_card(equipment)

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="info-section">
                <h4>Identificação</h4>
                <p><strong>TAG:</strong> {escape(equipment.tag)}</p>
                <p><strong>Modelo:</strong> {escape(equipment.modelo)}</p>
                <p><strong>Fabricante:</strong> {escape(equipment.fabricante)}</p>
                <p><strong>Cadastro:</strong> {escape(equipment.data_cadastro)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="info-section">
                <h4>Especificações</h4>
                <p><strong>Potência:</strong> {equipment.potencia:g} {escape(equipment.unidade_potencia)}</p>
                <p><strong>Tensão:</strong> {equipment.tensao:g} V</p>
                <p><strong>Corrente nominal:</strong> {equipment.corrente_nominal:g} A</p>
                <p><strong>Rotação nominal:</strong> {equipment.rotacao_nominal:g} RPM</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="info-section">
                <h4>Instalação e condição</h4>
                <p><strong>Local:</strong> {escape(equipment.local_instalacao)}</p>
                <div class="status-row">
                    <strong>Status operacional:</strong>
                    {status_badge_html(equipment.status_operacional)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Observações técnicas")
    st.info(equipment.observacoes)


def render_raw_data_page(service: EquipmentService) -> None:
    st.title("Dados Brutos")
    st.write("Visualização de leituras simuladas de sensores com conversão para unidades compreensíveis.")
    st.info(
        "Nesta Sprint, os dados são simulados para validar a interface. Nas próximas fases, "
        "essa camada poderá receber dados reais via ESP32 e MQTT."
    )

    equipments = service.list_equipments()
    if not equipments:
        render_empty_state("Cadastre um equipamento para visualizar dados simulados.")
        return

    tag_options = [equipment.tag for equipment in equipments]
    selected_tag = st.selectbox("Selecione o ativo monitorado", tag_options)
    selected_equipment = service.get_by_tag(selected_tag)
    if not selected_equipment:
        st.error("Equipamento não encontrado.")
        return

    st.warning("Leituras exibidas somente para demonstração acadêmica. Não representam sensores reais conectados.")

    with st.spinner("Simulando leitura bruta e convertendo valores..."):
        time.sleep(0.4)
        raw_data = simulate_raw_sensor_data(selected_equipment)
        converted_data = convert_raw_sensor_data(raw_data, selected_equipment)
        table_data = build_sensor_table(raw_data, converted_data)

    col1, col2, col3 = st.columns(3)
    col1.metric("Temperatura", f"{converted_data['temperatura_c']} °C")
    col2.metric("Corrente", f"{converted_data['corrente_a']} A")
    col3.metric("Rotação", f"{converted_data['rotacao_rpm']:.0f} RPM")

    st.subheader("Tabela de conversão simulada")
    st.dataframe(pd.DataFrame(table_data), width="stretch", hide_index=True)

    with st.expander("Contexto da simulação"):
        st.write(
            "Os campos `temperatura_raw`, `corrente_raw` e `rotacao_raw` representam leituras "
            "numéricas simuladas, semelhantes ao que poderia chegar de um microcontrolador. "
            "Em sprint futura, esta camada pode receber mensagens MQTT de dispositivos como ESP32."
        )


def render_about_page() -> None:
    st.title("Sobre o Projeto")
    st.write(
        "Projeto acadêmico evoluído para a Sprint 2, mantendo cadastro técnico, consulta, ficha "
        "técnica e dados brutos simulados da Sprint 1."
    )

    st.subheader("Objetivo")
    st.write(
        "Criar uma base organizada para evoluir um Digital Twin de motores e equipamentos, "
        "incluindo histórico operacional, alertas e visão por área."
    )

    st.subheader("Tecnologias")
    st.write("Python, Streamlit, Pandas, Plotly, JSON e CSV local.")

    st.subheader("Requisitos atendidos")
    st.markdown(
        """
        - Cadastro técnico de ativos
        - Consulta de equipamentos
        - Ficha técnica organizada
        - Visualização de dados brutos simulados
        - Dashboard Operacional por área e TAG
        - Histórico local em CSV
        - Gráficos temporais com Plotly
        - Alertas visuais por temperatura, vibração e corrente
        - Placa simulada em card HTML dinâmico
        """
    )

    st.subheader("Próximas Sprints")
    st.markdown(
        """
        - Integração com ESP32
        - Comunicação via MQTT
        - Autenticação de usuários
        - Banco de dados externo
        - OCR para leitura real de placas de motores
        """
    )
