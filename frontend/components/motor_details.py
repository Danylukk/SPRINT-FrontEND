"""Renderização de ficha e gráficos das entregas anteriores, alimentada por DTOs HTTP."""
from html import escape
from types import SimpleNamespace as Equipment
import pandas as pd
import plotly.express as px
import streamlit as st
from components.motor import render_empty_state, render_equipment_card, render_simulated_nameplate, status_badge_html

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
            plot_bgcolor="#F8FAFC",
            font_color="#0F172A",
        )
        st.plotly_chart(fig, use_container_width=True)


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
