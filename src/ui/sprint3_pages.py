from __future__ import annotations

from datetime import datetime

import streamlit as st

from src.repositories.event_repository import EventRepository
from src.services.equipment_service import EquipmentService
from src.services.operational_intelligence_service import OperationalIntelligenceService
from src.services.telemetry_service import TelemetryService
from src.ui.components import inject_global_styles
from src.ui.pages import (
    render_equipment_query_page,
    render_operational_dashboard,
    render_raw_data_page,
    render_registration_page,
)
from src.ui.sprint3_components import (
    STATUS_PRIORITY,
    render_alert_card,
    render_decision_support,
    render_equipment_states,
    render_event_history,
    render_intelligence_kpis,
)


MENU_OPTIONS = [
    "Painel de Alertas e Estados",
    "Dashboard Operacional",
    "Cadastro Técnico",
    "Consulta de Equipamentos",
    "Dados Brutos",
    "Sobre o Projeto",
]


def render_app() -> None:
    inject_global_styles()
    equipment_service = EquipmentService()

    with st.sidebar:
        st.title("Motor Digital Twin")
        st.caption("Sprint 3 | Inteligência operacional e apoio à decisão")
        selected_page = st.radio("Menu principal", MENU_OPTIONS)
        st.divider()
        st.caption("Front desacoplado · Alertas e NLP preparados para integração analítica")

    if selected_page == "Painel de Alertas e Estados":
        render_alerts_and_states_dashboard(equipment_service)
    elif selected_page == "Dashboard Operacional":
        render_operational_dashboard(equipment_service)
    elif selected_page == "Cadastro Técnico":
        render_registration_page(equipment_service)
    elif selected_page == "Consulta de Equipamentos":
        render_equipment_query_page(equipment_service)
    elif selected_page == "Dados Brutos":
        render_raw_data_page(equipment_service)
    else:
        render_sprint3_about_page()


def render_alerts_and_states_dashboard(equipment_service: EquipmentService) -> None:
    st.title("Painel de Alertas e Estados")
    st.write(
        "Visão inicial consolidada para acompanhar desvios operacionais antes da seleção de um equipamento."
    )

    telemetry_service = TelemetryService()
    intelligence_service = OperationalIntelligenceService()
    event_repository = EventRepository()

    equipments = equipment_service.list_equipments()
    if not equipments:
        st.info("Cadastre ao menos um equipamento para iniciar o monitoramento operacional.")
        return

    telemetry_service.ensure_history(equipments)

    if "sprint3_demo_alert_active" not in st.session_state:
        st.session_state.sprint3_demo_alert_active = False
    if "sprint3_last_update" not in st.session_state:
        st.session_state.sprint3_last_update = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    if "sprint3_statuses" not in st.session_state:
        st.session_state.sprint3_statuses = {}

    demo_target = next(
        (equipment for equipment in equipments if equipment.tag == "MTR-001"),
        next((equipment for equipment in equipments if equipment.status_operacional == "Operacional"), equipments[0]),
    )

    control_col, context_col = st.columns([1, 2])
    with control_col:
        refresh_clicked = st.button("↻ Atualizar informações", type="primary", use_container_width=True)
    with context_col:
        state_label = "anomalia simulada ativa" if st.session_state.sprint3_demo_alert_active else "baseline / regras atuais"
        st.caption(
            f"Última atualização: {st.session_state.sprint3_last_update} · Cenário: {state_label}."
        )

    if refresh_clicked:
        st.session_state.sprint3_demo_alert_active = not st.session_state.sprint3_demo_alert_active
        st.session_state.sprint3_last_update = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    snapshots = []
    for equipment in equipments:
        reading = telemetry_service.get_current_reading(equipment)
        snapshots.append(
            intelligence_service.analyze(
                equipment,
                reading,
                simulate_anomaly=(
                    equipment.tag == demo_target.tag and st.session_state.sprint3_demo_alert_active
                ),
            )
        )

    current_statuses = {snapshot.tag: snapshot.status for snapshot in snapshots}
    previous_statuses = dict(st.session_state.sprint3_statuses)

    if refresh_clicked and previous_statuses:
        changed = []
        for snapshot in snapshots:
            previous = previous_statuses.get(snapshot.tag)
            if previous and previous != snapshot.status:
                event = intelligence_service.build_transition_event(
                    snapshot,
                    previous_status=previous,
                )
                event_repository.append(event)
                changed.append(event)

        if changed:
            newest = changed[0]
            if newest.status_after == "Crítico":
                st.error(
                    f"Novo alerta: {newest.tag} mudou de {newest.status_before} para {newest.status_after}."
                )
            else:
                st.success(
                    f"Estado atualizado: {newest.tag} mudou de {newest.status_before} para {newest.status_after}."
                )

    st.session_state.sprint3_statuses = current_statuses

    render_intelligence_kpis(snapshots)

    st.divider()
    st.subheader("Alertas prioritários")
    priority_alerts = [snapshot for snapshot in snapshots if snapshot.status != "Saudável"]
    priority_alerts.sort(key=lambda snapshot: (STATUS_PRIORITY.get(snapshot.status, 9), snapshot.tag))

    if not priority_alerts:
        st.success("Todos os ativos estão dentro do baseline operacional no momento.")
    else:
        for snapshot in priority_alerts[:4]:
            render_alert_card(snapshot)

    st.info(
        "Transparência acadêmica: nesta Sprint, a classificação usa as regras já existentes como fallback. "
        f"O botão de atualização alterna um cenário controlado no ativo {demo_target.tag}; os resumos são mock NLP. "
        "A arquitetura está preparada para substituir essas fontes por resultados reais de ML e NLP sem acoplar o modelo à interface."
    )

    st.divider()
    left, right = st.columns([1.5, 1])
    with left:
        st.subheader("Estado dos equipamentos")
        render_equipment_states(snapshots)
    with right:
        st.subheader("Apoio inicial à decisão")
        render_decision_support(snapshots)

    st.divider()
    st.subheader("Histórico de eventos")
    render_event_history(event_repository.list_recent(limit=30))


def render_sprint3_about_page() -> None:
    st.title("Sobre o Projeto")
    st.write(
        "A Sprint 3 evolui o Motor Digital Twin das Sprints 1 e 2 com uma camada visual de "
        "inteligência operacional, alertas, estados e apoio inicial à decisão."
    )

    st.subheader("O que foi acrescentado")
    st.markdown(
        """
        - Painel inicial de Alertas e Estados antes da seleção do equipamento
        - Atualização dinâmica do estado operacional
        - Histórico persistente de mudanças de estado
        - Resumos textuais por adapter mock NLP
        - Cards de apoio inicial à decisão
        - Contrato desacoplado para futura integração com ML e NLP reais
        """
    )

    st.subheader("Transparência da demonstração")
    st.info(
        "A classificação atual reaproveita as regras analíticas da Sprint 2. O cenário disparado pelo "
        "botão de atualização é uma simulação controlada e os resumos são mock NLP, conforme permitido "
        "pelo enunciado enquanto os modelos reais não estiverem integrados."
    )

    st.subheader("Tecnologias")
    st.write("Python, Streamlit, Pandas, Plotly, JSON, CSV local e unittest.")
