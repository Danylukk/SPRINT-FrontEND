from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from src.models.operational_event import OperationalEvent
from src.services.alert_service import STATUS_CRITICAL, STATUS_HEALTHY, STATUS_WARNING
from src.services.operational_intelligence_service import OperationalSnapshot


STATUS_ICON = {
    STATUS_HEALTHY: "🟢",
    STATUS_WARNING: "🟡",
    STATUS_CRITICAL: "🔴",
}

STATUS_PRIORITY = {
    STATUS_CRITICAL: 0,
    STATUS_WARNING: 1,
    STATUS_HEALTHY: 2,
}


def render_intelligence_kpis(snapshots: list[OperationalSnapshot]) -> None:
    total = len(snapshots)
    healthy = sum(snapshot.status == STATUS_HEALTHY for snapshot in snapshots)
    warning = sum(snapshot.status == STATUS_WARNING for snapshot in snapshots)
    critical = sum(snapshot.status == STATUS_CRITICAL for snapshot in snapshots)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ativos monitorados", total)
    col2.metric("Saudáveis", healthy)
    col3.metric("Em atenção", warning)
    col4.metric("Críticos", critical)


def render_alert_card(snapshot: OperationalSnapshot) -> None:
    icon = STATUS_ICON.get(snapshot.status, "⚪")
    border = {
        STATUS_CRITICAL: "#ef4444",
        STATUS_WARNING: "#f59e0b",
        STATUS_HEALTHY: "#22c55e",
    }.get(snapshot.status, "#64748b")

    st.markdown(
        f"""
        <div style="border-left:5px solid {border};background:rgba(15,23,42,.72);padding:1rem 1.1rem;border-radius:.65rem;margin:.4rem 0 1rem 0;">
            <div style="font-size:1.02rem;font-weight:700;">{icon} {escape(snapshot.tag)} · {escape(snapshot.status)}</div>
            <div style="color:#94a3b8;margin-top:.18rem;">{escape(snapshot.area)} · {escape(snapshot.dominant_metric)}: {escape(snapshot.dominant_value)}</div>
            <div style="margin-top:.8rem;font-weight:650;">Resumo inteligente</div>
            <div style="color:#dbeafe;margin-top:.2rem;">{escape(snapshot.summary)}</div>
            <div style="margin-top:.75rem;font-weight:650;">Apoio inicial à decisão</div>
            <div style="color:#e2e8f0;margin-top:.2rem;">{escape(snapshot.recommendation)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if snapshot.source == "simulation":
        st.caption("Origem analítica: simulação controlada da Sprint 3 · Resumo: mock NLP")
    else:
        st.caption("Origem analítica: regras desacopladas da Sprint 2 · Resumo: mock NLP")


def render_equipment_states(snapshots: list[OperationalSnapshot]) -> None:
    ordered = sorted(
        snapshots,
        key=lambda snapshot: (STATUS_PRIORITY.get(snapshot.status, 9), snapshot.tag),
    )
    rows = []
    for snapshot in ordered:
        reading = snapshot.reading
        rows.append(
            {
                "Estado": f"{STATUS_ICON.get(snapshot.status, '⚪')} {snapshot.status}",
                "TAG": snapshot.tag,
                "Área / Planta": snapshot.area,
                "Temperatura": f"{float(reading['temperatura_c']):.1f} °C",
                "Vibração": f"{float(reading['vibracao_mm_s']):.2f} mm/s",
                "Corrente": f"{float(reading['corrente_a']):.2f} A",
                "Origem": "Simulação Sprint 3" if snapshot.source == "simulation" else "Regras Sprint 2",
            }
        )

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_decision_support(snapshots: list[OperationalSnapshot]) -> None:
    actionable = [snapshot for snapshot in snapshots if snapshot.status != STATUS_HEALTHY]
    actionable.sort(key=lambda snapshot: (STATUS_PRIORITY.get(snapshot.status, 9), snapshot.tag))

    if not actionable:
        st.success("Nenhuma ação prioritária sugerida. Manter monitoramento de rotina.")
        return

    for snapshot in actionable[:3]:
        icon = "🚨" if snapshot.status == STATUS_CRITICAL else "⚠️"
        with st.container():
            st.markdown(f"**{icon} {snapshot.tag} · Prioridade {snapshot.severity}**")
            st.write(snapshot.recommendation)
            st.caption(f"Foco: {snapshot.dominant_metric} · {snapshot.dominant_value}")


def render_event_history(events: list[OperationalEvent]) -> None:
    if not events:
        st.info(
            "Nenhuma mudança de estado foi registrada nesta Sprint. "
            "Use 'Atualizar informações' para executar o cenário controlado de demonstração."
        )
        return

    rows = [
        {
            "Data/Hora": event.timestamp.replace("T", " "),
            "TAG": event.tag,
            "Área": event.area,
            "Severidade": event.severity,
            "Mudança": f"{event.status_before} → {event.status_after}",
            "Métrica": event.metric,
            "Valor": event.measured_value,
            "Origem": "Simulação" if event.source == "simulation" else "Regras",
        }
        for event in events
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("Ver detalhes textuais dos eventos"):
        for event in events[:10]:
            st.markdown(f"**{event.tag} · {event.status_before} → {event.status_after}**")
            st.write(event.summary)
            st.caption(f"Ação sugerida: {event.recommendation}")
            st.divider()
