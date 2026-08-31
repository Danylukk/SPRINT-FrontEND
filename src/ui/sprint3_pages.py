from __future__ import annotations

import streamlit as st

from src.repositories.errors import RepositoryDataError
from src.repositories.event_repository import EventRepository
from src.services.alert_service import STATUS_CRITICAL
from src.services.equipment_service import EquipmentService
from src.services.operational_intelligence_service import OperationalIntelligenceService, OperationalSnapshot
from src.services.telemetry_service import TelemetryService
from src.ui.components import inject_global_styles
from src.ui.pages import render_equipment_query_page, render_operational_dashboard, render_raw_data_page, render_registration_page
from src.ui.sprint3_components import STATUS_PRIORITY, render_alert_card, render_decision_support, render_equipment_states, render_event_history, render_intelligence_kpis


MENU_OPTIONS = ["Painel de Alertas e Estados", "Dashboard Operacional", "Cadastro Técnico", "Consulta de Equipamentos", "Dados Brutos", "Sobre o Projeto"]
SNAPSHOTS_KEY = "sprint3_analytic_snapshots"
LAST_EVENT_KEY = "sprint3_last_event_message"


def render_app() -> None:
    inject_global_styles()
    equipment_service = EquipmentService()
    with st.sidebar:
        st.title("Motor Digital Twin")
        st.caption("Sprint 3 | Inteligência operacional e apoio à decisão")
        selected_page = st.radio("Menu principal", MENU_OPTIONS)
        st.divider()
        st.caption("Provider analítico desacoplado · NLP mock identificado")
    try:
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
    except RepositoryDataError as error:
        st.error(f"Não foi possível carregar os dados locais com segurança. {error}")


def render_alerts_and_states_dashboard(equipment_service: EquipmentService) -> None:
    st.title("Painel de Alertas e Estados")
    st.write("Visão inicial consolidada para acompanhar desvios antes da seleção de um equipamento.")
    telemetry_service = TelemetryService()
    intelligence_service = OperationalIntelligenceService()
    event_repository = EventRepository()
    equipments = equipment_service.list_equipments()
    if not equipments:
        st.info("Cadastre ao menos um equipamento para iniciar o monitoramento operacional.")
        return
    telemetry_service.ensure_history(equipments)
    snapshots = _ensure_snapshots(equipments, telemetry_service, intelligence_service)
    demo_target = next((equipment for equipment in equipments if equipment.tag == "MTR-001"), equipments[0])
    control_col, context_col = st.columns([1, 2])
    with control_col:
        refresh_clicked = st.button("↻ Atualizar informações", type="primary", width="stretch")
    if refresh_clicked:
        snapshots, event_message = _create_demo_inference(demo_target, snapshots, telemetry_service, intelligence_service, event_repository)
        st.session_state[SNAPSHOTS_KEY] = snapshots
        st.session_state[LAST_EVENT_KEY] = event_message
    current_target = snapshots[demo_target.tag]
    with context_col:
        next_scenario = "baseline saudável" if current_target.status == STATUS_CRITICAL else "desvio crítico"
        st.caption(
            f"Última leitura de {demo_target.tag}: {current_target.timestamp.replace('T', ' ')} · "
            f"Origem: {_source_label(current_target.source)} · Próxima atualização DEMO: {next_scenario}."
        )
    if st.session_state.get(LAST_EVENT_KEY):
        message, is_critical = st.session_state[LAST_EVENT_KEY]
        (st.error if is_critical else st.success)(message)
    snapshot_list = list(snapshots.values())
    render_intelligence_kpis(snapshot_list)
    st.divider()
    st.subheader("Alertas prioritários")
    priority_alerts = [snapshot for snapshot in snapshot_list if snapshot.status != "Saudável"]
    priority_alerts.sort(key=lambda snapshot: (STATUS_PRIORITY.get(snapshot.status, 9), snapshot.tag))
    if not priority_alerts:
        st.success("Todos os ativos estão dentro do baseline operacional no momento.")
    else:
        for snapshot in priority_alerts[:4]:
            render_alert_card(snapshot)
    st.info(
        "Transparência acadêmica: o provider atual é RulesAnalyticsProvider, baseado nos thresholds existentes. "
        "A DEMO cria uma nova leitura persistida localmente e a UI consome apenas o OperationalSnapshot. "
        "Não há ML nem NLP real; os resumos usam mock_nlp determinístico."
    )
    st.divider()
    left, right = st.columns([1.5, 1])
    with left:
        st.subheader("Estado analítico dos equipamentos")
        render_equipment_states(snapshot_list)
    with right:
        st.subheader("Apoio inicial à decisão")
        render_decision_support(snapshot_list)
    st.divider()
    st.subheader("Histórico de eventos desta execução")
    include_reference = st.checkbox("Incluir histórico de referência versionado", value=False)
    render_event_history(event_repository.list_recent(limit=50, include_seed=include_reference))


def _ensure_snapshots(equipments: list, telemetry_service: TelemetryService, intelligence_service: OperationalIntelligenceService) -> dict[str, OperationalSnapshot]:
    existing = st.session_state.get(SNAPSHOTS_KEY)
    expected_tags = {equipment.tag for equipment in equipments}
    if isinstance(existing, dict) and set(existing) == expected_tags:
        return existing
    snapshots = {equipment.tag: intelligence_service.analyze(equipment, telemetry_service.get_current_reading(equipment)) for equipment in equipments}
    st.session_state[SNAPSHOTS_KEY] = snapshots
    return snapshots


def _create_demo_inference(equipment, snapshots: dict[str, OperationalSnapshot], telemetry_service: TelemetryService, intelligence_service: OperationalIntelligenceService, event_repository: EventRepository) -> tuple[dict[str, OperationalSnapshot], tuple[str, bool]]:
    previous = snapshots[equipment.tag]
    scenario = "baseline" if previous.status == STATUS_CRITICAL else "critical"
    reading = telemetry_service.append_demo_reading(equipment, scenario=scenario)
    current = intelligence_service.analyze(equipment, reading)
    updated = dict(snapshots)
    updated[equipment.tag] = current
    if previous.status == current.status:
        return updated, (f"Nova leitura criada para {equipment.tag}; o estado analítico permaneceu {current.status}.", False)
    event = intelligence_service.build_transition_event(current, previous_status=previous.status)
    if event is None:
        return updated, (f"Nova leitura criada para {equipment.tag}; o estado analítico permaneceu {current.status}.", False)
    event_repository.append_if_new(event)
    message = f"Estado atualizado: {event.tag} mudou de {event.status_before} para {event.status_after}."
    return updated, (message, event.status_after == STATUS_CRITICAL)


def render_sprint3_about_page() -> None:
    st.title("Sobre o Projeto")
    st.write("A Sprint 3 adiciona inteligência operacional, alertas, histórico e apoio inicial à decisão.")
    st.subheader("O que foi acrescentado")
    st.markdown("""
        - Painel inicial de Alertas e Estados antes da seleção do equipamento
        - Leitura DEMO persistida com timestamp e identificador
        - Provider analítico desacoplado para futura integração de ML
        - Histórico runtime de transições sem alterar os arquivos versionados
        - Resumos textuais por adapter mock_nlp
        - Cards de apoio inicial à decisão
        """)
    st.subheader("Transparência da demonstração")
    st.info("A classificação atual é RulesAnalyticsProvider, baseado em thresholds. A DEMO gera leituras determinísticas e o NLP é mock_nlp. Um MLAnalyticsProvider futuro pode implementar o mesmo contrato.")
    st.subheader("Tecnologias")
    st.write("Python, Streamlit, Pandas, Plotly, JSON, CSV local e unittest.")


def _source_label(source: str) -> str:
    return "DEMO Sprint 3" if source == "demo_sprint3" else "Histórico de referência" if source == "seed_history" else source
