"""Componentes de apresentação reaproveitados das Sprints 1–2; sem acesso a dados locais."""
from html import escape

import pandas as pd
import streamlit as st

from types import SimpleNamespace as Equipment


STATUS_COLORS = {
    "Operacional": "#1f9d55",
    "Atenção": "#d99a00",
    "Crítico": "#c92a2a",
    "Inativo": "#c92a2a",
    "Saudável": "#1f9d55",
}

HEALTH_STYLES = {
    "Saudável": {
        "color": "#22c55e",
        "background": "rgba(34, 197, 94, 0.12)",
        "border": "rgba(34, 197, 94, 0.35)",
        "message": "Ativo em condição operacional saudável.",
    },
    "Atenção": {
        "color": "#f59e0b",
        "background": "rgba(245, 158, 11, 0.13)",
        "border": "rgba(245, 158, 11, 0.4)",
        "message": "Ativo em atenção. Acompanhar tendência operacional.",
    },
    "Crítico": {
        "color": "#ef4444",
        "background": "rgba(239, 68, 68, 0.13)",
        "border": "rgba(239, 68, 68, 0.42)",
        "message": "Ativo em condição crítica. Priorizar verificação técnica.",
    },
}


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            .status-pill {
                display: inline-block;
                padding: 0.25rem 0.7rem;
                border-radius: 999px;
                color: white;
                font-weight: 700;
                font-size: 0.85rem;
            }
            .info-section,
            .telemetry-card,
            .health-card,
            .nameplate-card,
            .operational-message {
                border: 1px solid rgba(148, 163, 184, 0.28);
                border-radius: 8px;
                background: rgba(15, 23, 42, 0.72);
                color: #e5e7eb;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.16);
            }
            .info-section {
                padding: 1rem;
                min-height: 120px;
            }
            .info-section h4,
            .telemetry-card h4,
            .nameplate-card h4 {
                color: #f8fafc;
                margin: 0 0 0.75rem 0;
                font-size: 1rem;
                font-weight: 700;
            }
            .info-section p {
                color: #d1d5db;
                margin: 0.35rem 0;
                line-height: 1.45;
            }
            .info-section strong {
                color: #f8fafc;
            }
            .info-section .status-row {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-top: 0.35rem;
                flex-wrap: wrap;
            }
            .info-section .status-row strong,
            .info-section .status-pill {
                margin: 0;
            }
            .muted-text {
                color: #94a3b8;
                font-size: 0.95rem;
            }
            .health-card {
                padding: 1.1rem 1.2rem;
            }
            .health-label {
                color: #cbd5e1;
                font-size: 0.86rem;
                font-weight: 700;
                letter-spacing: 0;
                text-transform: uppercase;
            }
            .health-status {
                margin-top: 0.45rem;
                font-size: 2rem;
                font-weight: 800;
                line-height: 1.1;
            }
            .health-message {
                color: #cbd5e1;
                margin-top: 0.55rem;
                line-height: 1.45;
            }
            .telemetry-card {
                padding: 1rem;
                min-height: 142px;
            }
            .telemetry-value {
                color: #f8fafc;
                font-size: 1.8rem;
                font-weight: 800;
                line-height: 1.2;
                margin: 0.35rem 0;
            }
            .telemetry-status {
                display: inline-block;
                padding: 0.18rem 0.55rem;
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 800;
                margin-top: 0.2rem;
            }
            .telemetry-note {
                color: #cbd5e1;
                margin-top: 0.55rem;
                font-size: 0.9rem;
                line-height: 1.35;
            }
            .operational-message {
                padding: 0.85rem 1rem;
                border-left: 4px solid #38bdf8;
                background: rgba(14, 116, 144, 0.15);
                color: #dbeafe;
                line-height: 1.45;
            }
            .nameplate-card {
                padding: 1.2rem;
                background:
                    linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.92));
            }
            .nameplate-visual {
                position: relative;
                overflow: hidden;
                border: 1px solid rgba(226, 232, 240, 0.45);
                border-radius: 6px;
                padding: 1rem;
                margin-bottom: 1rem;
                background:
                    linear-gradient(135deg, rgba(226, 232, 240, 0.96), rgba(148, 163, 184, 0.92) 48%, rgba(241, 245, 249, 0.88)),
                    repeating-linear-gradient(90deg, rgba(15, 23, 42, 0.08) 0, rgba(15, 23, 42, 0.08) 1px, transparent 1px, transparent 8px);
                color: #0f172a;
                box-shadow:
                    inset 0 1px 0 rgba(255, 255, 255, 0.72),
                    inset 0 -1px 0 rgba(15, 23, 42, 0.18),
                    0 12px 28px rgba(0, 0, 0, 0.22);
            }
            .nameplate-rivet {
                position: absolute;
                width: 0.58rem;
                height: 0.58rem;
                border-radius: 999px;
                background: radial-gradient(circle at 35% 30%, #f8fafc, #64748b 62%, #334155);
                box-shadow: inset 0 1px 1px rgba(255,255,255,0.75), 0 1px 2px rgba(15,23,42,0.45);
            }
            .nameplate-rivet.top-left { top: 0.55rem; left: 0.55rem; }
            .nameplate-rivet.top-right { top: 0.55rem; right: 0.55rem; }
            .nameplate-rivet.bottom-left { bottom: 0.55rem; left: 0.55rem; }
            .nameplate-rivet.bottom-right { bottom: 0.55rem; right: 0.55rem; }
            .nameplate-visual-header {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 1rem;
                padding: 0 0.35rem 0.65rem;
                border-bottom: 2px solid rgba(15, 23, 42, 0.35);
            }
            .nameplate-manufacturer {
                font-size: 1.45rem;
                font-weight: 900;
                line-height: 1.05;
                color: #0f172a;
            }
            .nameplate-model-line {
                color: #334155;
                font-size: 0.82rem;
                font-weight: 800;
                margin-top: 0.2rem;
                letter-spacing: 0;
                text-transform: uppercase;
            }
            .nameplate-tag-box {
                border: 2px solid rgba(15, 23, 42, 0.7);
                border-radius: 4px;
                padding: 0.35rem 0.55rem;
                min-width: 8rem;
                text-align: center;
                background: rgba(248, 250, 252, 0.55);
            }
            .nameplate-tag-box span {
                display: block;
                color: #475569;
                font-size: 0.68rem;
                font-weight: 900;
                text-transform: uppercase;
            }
            .nameplate-tag-box strong {
                color: #020617;
                display: block;
                font-size: 1.05rem;
                margin-top: 0.08rem;
            }
            .nameplate-visual-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.45rem;
                margin: 0.8rem 0.35rem 0;
            }
            .nameplate-visual-field {
                display: grid;
                grid-template-columns: 6.7rem minmax(0, 1fr);
                align-items: center;
                border: 1px solid rgba(15, 23, 42, 0.42);
                min-height: 2.15rem;
                background: rgba(248, 250, 252, 0.35);
            }
            .nameplate-visual-field span {
                height: 100%;
                display: flex;
                align-items: center;
                padding: 0 0.45rem;
                border-right: 1px solid rgba(15, 23, 42, 0.42);
                color: #334155;
                font-size: 0.72rem;
                font-weight: 900;
                text-transform: uppercase;
            }
            .nameplate-visual-field strong {
                color: #020617;
                font-size: 0.95rem;
                font-weight: 900;
                padding: 0 0.55rem;
                word-break: break-word;
            }
            .nameplate-ocr-row {
                display: grid;
                grid-template-columns: 1fr auto;
                align-items: center;
                gap: 0.8rem;
                margin: 0.85rem 0.35rem 0;
            }
            .nameplate-barcode {
                height: 2.15rem;
                border: 1px solid rgba(15, 23, 42, 0.45);
                background:
                    repeating-linear-gradient(90deg, #0f172a 0 2px, transparent 2px 5px, #0f172a 5px 6px, transparent 6px 10px);
                opacity: 0.82;
            }
            .nameplate-ocr-badge {
                border: 1px solid rgba(15, 23, 42, 0.52);
                border-radius: 999px;
                padding: 0.28rem 0.6rem;
                color: #0f172a;
                background: rgba(250, 204, 21, 0.38);
                font-size: 0.72rem;
                font-weight: 900;
                white-space: nowrap;
            }
            .nameplate-header {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 1rem;
                border-bottom: 1px solid rgba(148, 163, 184, 0.26);
                padding-bottom: 0.8rem;
                margin-bottom: 0.8rem;
            }
            .nameplate-title {
                color: #f8fafc;
                font-weight: 800;
                font-size: 1.25rem;
                line-height: 1.2;
            }
            .nameplate-subtitle {
                color: #cbd5e1;
                margin-top: 0.2rem;
            }
            .nameplate-simulated {
                color: #fde68a;
                background: rgba(180, 83, 9, 0.24);
                border: 1px solid rgba(245, 158, 11, 0.4);
                border-radius: 999px;
                padding: 0.2rem 0.55rem;
                font-size: 0.76rem;
                font-weight: 800;
                white-space: nowrap;
            }
            .nameplate-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.55rem 0.9rem;
            }
            .nameplate-item {
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 6px;
                padding: 0.65rem;
                background: rgba(2, 6, 23, 0.24);
            }
            .nameplate-item span {
                color: #94a3b8;
                display: block;
                font-size: 0.78rem;
                font-weight: 700;
                text-transform: uppercase;
            }
            .nameplate-item strong {
                color: #f8fafc;
                display: block;
                font-size: 1rem;
                margin-top: 0.2rem;
            }
            .nameplate-footnote {
                color: #cbd5e1;
                margin-top: 0.85rem;
                font-size: 0.88rem;
                line-height: 1.35;
            }
            @media (max-width: 720px) {
                .nameplate-visual-header,
                .nameplate-ocr-row {
                    display: block;
                }
                .nameplate-tag-box,
                .nameplate-ocr-badge {
                    display: inline-block;
                    margin-top: 0.55rem;
                }
                .nameplate-visual-grid {
                    grid-template-columns: 1fr;
                }
                .nameplate-visual-field {
                    grid-template-columns: 6rem minmax(0, 1fr);
                }
                .nameplate-grid {
                    grid-template-columns: 1fr;
                }
                .nameplate-header {
                    display: block;
                }
                .nameplate-simulated {
                    display: inline-block;
                    margin-top: 0.55rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> None:
    st.markdown(status_badge_html(status), unsafe_allow_html=True)


def status_badge_html(status: str) -> str:
    color = STATUS_COLORS.get(status, "#667085")
    return f"<span class='status-pill' style='background:{color}'>{escape(status)}</span>"


def equipment_to_dataframe(equipments: list[Equipment]) -> pd.DataFrame:
    rows = [
        {
            "TAG": item.tag,
            "Modelo": item.modelo,
            "Fabricante": item.fabricante,
            "Potência": f"{item.potencia:g} {item.unidade_potencia}",
            "Tensão": f"{item.tensao:g} V",
            "Local": item.local_instalacao,
            "Status": item.status_operacional,
            "Data de cadastro": item.data_cadastro,
        }
        for item in equipments
    ]
    return pd.DataFrame(rows)


def render_equipment_card(equipment: Equipment) -> None:
    left, middle, right = st.columns([1.2, 1, 1])

    with left:
        st.subheader(equipment.tag)
        st.caption(f"{equipment.fabricante} | {equipment.modelo}")
        status_badge(equipment.status_operacional)

    with middle:
        st.metric("Potência", f"{equipment.potencia:g} {equipment.unidade_potencia}")
        st.metric("Tensão", f"{equipment.tensao:g} V")

    with right:
        st.metric("Corrente nominal", f"{equipment.corrente_nominal:g} A")
        st.metric("Rotação nominal", f"{equipment.rotacao_nominal:g} RPM")


def render_health_indicator(status: str) -> None:
    style = HEALTH_STYLES.get(status, HEALTH_STYLES["Atenção"])
    st.markdown(
        f"""
        <div class="health-card" style="border-color: {style["border"]}; background: {style["background"]};">
            <div class="health-label">Saúde geral do ativo</div>
            <div class="health-status" style="color: {style["color"]};">{escape(status)}</div>
            <div class="health-message">{escape(style["message"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_telemetry_card(title: str, value: str, status: str, message: str) -> None:
    style = HEALTH_STYLES.get(status, HEALTH_STYLES["Atenção"])
    st.markdown(
        f"""
        <div class="telemetry-card">
            <h4>{escape(title)}</h4>
            <div class="telemetry-value">{escape(value)}</div>
            <span class="telemetry-status" style="color: {style["color"]}; background: {style["background"]}; border: 1px solid {style["border"]};">
                {escape(status)}
            </span>
            <div class="telemetry-note">{escape(message)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_operational_message(message: str) -> None:
    st.markdown(
        f"""<div class="operational-message">{escape(message)}</div>""",
        unsafe_allow_html=True,
    )


def render_simulated_nameplate(equipment: Equipment) -> None:
    st.markdown(
        f"""
        <div class="nameplate-card">
            <div class="nameplate-visual" role="img" aria-label="Imagem simulada da placa do motor {escape(equipment.tag)}">
                <span class="nameplate-rivet top-left"></span>
                <span class="nameplate-rivet top-right"></span>
                <span class="nameplate-rivet bottom-left"></span>
                <span class="nameplate-rivet bottom-right"></span>
                <div class="nameplate-visual-header">
                    <div>
                        <div class="nameplate-manufacturer">{escape(equipment.fabricante)}</div>
                        <div class="nameplate-model-line">Motor elétrico | modelo {escape(equipment.modelo)}</div>
                    </div>
                    <div class="nameplate-tag-box">
                        <span>TAG do ativo</span>
                        <strong>{escape(equipment.tag)}</strong>
                    </div>
                </div>
                <div class="nameplate-visual-grid">
                    <div class="nameplate-visual-field">
                        <span>Modelo</span>
                        <strong>{escape(equipment.modelo)}</strong>
                    </div>
                    <div class="nameplate-visual-field">
                        <span>Fabricante</span>
                        <strong>{escape(equipment.fabricante)}</strong>
                    </div>
                    <div class="nameplate-visual-field">
                        <span>Potência</span>
                        <strong>{equipment.potencia:g} {escape(equipment.unidade_potencia)}</strong>
                    </div>
                    <div class="nameplate-visual-field">
                        <span>Tensão</span>
                        <strong>{equipment.tensao:g} V</strong>
                    </div>
                    <div class="nameplate-visual-field">
                        <span>Corrente</span>
                        <strong>{equipment.corrente_nominal:g} A</strong>
                    </div>
                    <div class="nameplate-visual-field">
                        <span>Rotação</span>
                        <strong>{equipment.rotacao_nominal:g} RPM</strong>
                    </div>
                </div>
                <div class="nameplate-ocr-row">
                    <div class="nameplate-barcode"></div>
                    <div class="nameplate-ocr-badge">SIMULADA | OCR FUTURO</div>
                </div>
            </div>
            <div class="nameplate-header">
                <div>
                    <div class="nameplate-title">{escape(equipment.tag)}</div>
                    <div class="nameplate-subtitle">{escape(equipment.fabricante)} | {escape(equipment.modelo)}</div>
                </div>
                <div class="nameplate-simulated">PLACA SIMULADA</div>
            </div>
            <h4>Dados técnicos vinculados ao cadastro</h4>
            <div class="nameplate-grid">
                <div class="nameplate-item">
                    <span>Modelo</span>
                    <strong>{escape(equipment.modelo)}</strong>
                </div>
                <div class="nameplate-item">
                    <span>Fabricante</span>
                    <strong>{escape(equipment.fabricante)}</strong>
                </div>
                <div class="nameplate-item">
                    <span>Potência</span>
                    <strong>{equipment.potencia:g} {escape(equipment.unidade_potencia)}</strong>
                </div>
                <div class="nameplate-item">
                    <span>Tensão</span>
                    <strong>{equipment.tensao:g} V</strong>
                </div>
                <div class="nameplate-item">
                    <span>Corrente nominal</span>
                    <strong>{equipment.corrente_nominal:g} A</strong>
                </div>
                <div class="nameplate-item">
                    <span>Rotação nominal</span>
                    <strong>{equipment.rotacao_nominal:g} RPM</strong>
                </div>
            </div>
            <div class="nameplate-footnote">
                Card visual simulado, preparado para futura visão computacional/OCR a partir de imagens reais de placa.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(message: str) -> None:
    st.info(message)
