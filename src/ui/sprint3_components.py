from __future__ import annotations

from datetime import datetime
from html import escape
from math import isfinite

import pandas as pd
import streamlit as st

from src.models.operational_event import OperationalEvent
from src.services.alert_service import STATUS_CRITICAL, STATUS_HEALTHY, STATUS_UNAVAILABLE, STATUS_WARNING
from src.services.operational_intelligence_service import OperationalSnapshot


STATUS_ICON = {STATUS_HEALTHY: "🟢", STATUS_WARNING: "🟡", STATUS_CRITICAL: "🔴", STATUS_UNAVAILABLE: "⚪"}
STATUS_PRIORITY = {STATUS_CRITICAL: 0, STATUS_WARNING: 1, STATUS_UNAVAILABLE: 2, STATUS_HEALTHY: 3}


def render_intelligence_kpis(snapshots: list[OperationalSnapshot]) -> None:
    total = len(snapshots)
    healthy = sum(snapshot.status == STATUS_HEALTHY for snapshot in snapshots)
    warning = sum(snapshot.status == STATUS_WARNING for snapshot in snapshots)
    critical = sum(snapshot.status == STATUS_CRITICAL for snapshot in snapshots)
    unavailable = sum(snapshot.status == STATUS_UNAVAILABLE for snapshot in snapshots)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ativos monitorados", total)
    col2.metric("Saudáveis", healthy)
    col3.metric("Em atenção", warning)
    col4.metric("Críticos", critical)
    if unavailable:
        st.caption(f"⚪ Dados indisponíveis: {unavailable}. Esse estado não representa anomalia.")


def render_alert_card(snapshot: OperationalSnapshot) -> None:
    icon = STATUS_ICON.get(snapshot.status, "⚪")
    border = {
        STATUS_CRITICAL: "#ef4444",
        STATUS_WARNING: "#f59e0b",
        STATUS_HEALTHY: "#22c55e",
        STATUS_UNAVAILABLE: "#94a3b8",
    }.get(snapshot.status, "#64748b")
    freshness = "Dados desatualizados" if snapshot.is_stale else "Leitura atual"
    st.markdown(
        f"""
        <div style="border-left:5px solid {border};background:rgba(15,23,42,.72);padding:1rem 1.1rem;border-radius:.65rem;margin:.4rem 0 1rem 0;">
            <div style="font-size:1.02rem;font-weight:700;">{icon} {escape(snapshot.tag)} · {escape(snapshot.status)}</div>
            <div style="color:#94a3b8;margin-top:.18rem;">{escape(snapshot.area)} · {escape(snapshot.dominant_metric)}: {escape(snapshot.dominant_value)}</div>
            <div style="color:#cbd5e1;margin-top:.35rem;">Última leitura: {escape(_format_timestamp(snapshot.timestamp))} · {freshness}</div>
            <div style="margin-top:.8rem;font-weight:650;">Resumo inteligente</div>
            <div style="color:#dbeafe;margin-top:.2rem;">{escape(snapshot.summary)}</div>
            <div style="margin-top:.75rem;font-weight:650;">Apoio inicial à decisão</div>
            <div style="color:#e2e8f0;margin-top:.2rem;">{escape(snapshot.recommendation)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        f"Origem: {_source_label(snapshot.source)} · Análise: {snapshot.analytics_provider} · "
        f"Resumo: {snapshot.nlp_provider} · Leitura: {snapshot.reading_id}"
    )


def render_equipment_states(snapshots: list[OperationalSnapshot]) -> None:
    ordered = sorted(snapshots, key=lambda snapshot: (STATUS_PRIORITY.get(snapshot.status, 9), snapshot.tag))
    rows = []
    for snapshot in ordered:
        reading = snapshot.reading
        rows.append(
            {
                "Estado analítico": f"{STATUS_ICON.get(snapshot.status, '⚪')} {snapshot.status}",
                "TAG": snapshot.tag,
                "Área / Planta": snapshot.area,
                "Temperatura": _format_metric(reading.get("temperatura_c"), "°C", 1),
                "Vibração": _format_metric(reading.get("vibracao_mm_s"), "mm/s", 2),
                "Corrente": _format_metric(reading.get("corrente_a"), "A", 2),
                "Última leitura": _format_timestamp(snapshot.timestamp),
                "Dados": "Desatualizados" if snapshot.is_stale else "Atuais",
                "Origem": _source_label(snapshot.source),
            }
        )
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def render_decision_support(snapshots: list[OperationalSnapshot]) -> None:
    actionable = [snapshot for snapshot in snapshots if snapshot.status in {STATUS_WARNING, STATUS_CRITICAL}]
    unavailable = [snapshot for snapshot in snapshots if snapshot.status == STATUS_UNAVAILABLE]
    actionable.sort(key=lambda snapshot: (STATUS_PRIORITY.get(snapshot.status, 9), snapshot.tag))
    if not actionable:
        st.success("Nenhuma ação prioritária sugerida. Manter monitoramento de rotina.")
    else:
        for snapshot in actionable[:3]:
            icon = "🚨" if snapshot.status == STATUS_CRITICAL else "⚠️"
            with st.container():
                st.markdown(f"**{icon} {snapshot.tag} · Prioridade {snapshot.severity}**")
                st.write(snapshot.recommendation)
                st.caption(
                    f"Foco: {snapshot.dominant_metric} · {snapshot.dominant_value} · "
                    f"{_format_timestamp(snapshot.timestamp)} · {_source_label(snapshot.source)}"
                )
    if unavailable:
        st.info("Há ativos com dados indisponíveis. Verifique a origem da leitura antes de tomar decisão.")


def render_event_history(events: list[OperationalEvent]) -> None:
    if not events:
        st.info("Nenhuma transição foi registrada nesta execução. Use 'Atualizar informações' para gerar a leitura DEMO.")
        return
    tags = ["Todos"] + sorted({event.tag for event in events})
    severities = ["Todas"] + sorted({event.severity for event in events})
    filter_col, severity_col, limit_col = st.columns(3)
    selected_tag = filter_col.selectbox("Equipamento", tags, key="sprint3_history_tag")
    selected_severity = severity_col.selectbox("Severidade", severities, key="sprint3_history_severity")
    limit = limit_col.selectbox("Eventos recentes", [10, 30, 50], index=1, key="sprint3_history_limit")
    filtered = [
        event for event in events
        if (selected_tag == "Todos" or event.tag == selected_tag)
        and (selected_severity == "Todas" or event.severity == selected_severity)
    ][:limit]
    if not filtered:
        st.info("Nenhum evento encontrado para os filtros selecionados.")
        return
    rows = [
        {
            "Data/Hora": _format_timestamp(event.timestamp),
            "TAG": event.tag,
            "Área": event.area,
            "Severidade": event.severity,
            "Mudança": f"{event.status_before} → {event.status_after}",
            "Métrica": event.metric,
            "Valor": event.measured_value,
            "Origem": _source_label(event.source),
        }
        for event in filtered
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    with st.expander("Ver detalhes textuais dos eventos"):
        for event in filtered[:10]:
            st.markdown(f"**{event.tag} · {event.status_before} → {event.status_after}**")
            st.write(event.summary)
            st.caption(
                f"Ação sugerida: {event.recommendation} · Leitura: {event.reading_id or 'legado'} · "
                f"Inferência: {event.inference_id or 'legada'}"
            )
            st.divider()


def _format_timestamp(value: str) -> str:
    try:
        return datetime.fromisoformat(value).strftime("%d/%m/%Y %H:%M:%S")
    except (TypeError, ValueError):
        return "Indisponível"


def _format_metric(value: object, unit: str, decimals: int) -> str:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "Indisponível"
    if not isfinite(numeric_value):
        return "Indisponível"
    return f"{numeric_value:.{decimals}f} {unit}"


def _source_label(source: str) -> str:
    labels = {
        "demo_sprint3": "DEMO Sprint 3",
        "simulation_sprint2": "Simulação Sprint 2",
        "seed_history": "Histórico de referência",
        "runtime_simulation": "Execução local",
    }
    return labels.get(source, source or "Indisponível")
