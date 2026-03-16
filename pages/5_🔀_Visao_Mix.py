"""
Página 4 — Visão Mix
Análise de participação por segmento, gênero, público e faixa de preço.
Comparação com mix ideal da marca.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tema
from helpers import run_forecast_and_inventory, get_config, apply_professional_layout
from config import DEFAULT_PRICE_RANGES, DEFAULT_IDEAL_MIX
from engines.mix_analysis import calculate_mix, calculate_price_ranges, compare_with_ideal

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

def _make_comparison_chart(comp_df, dimension, title):
    if comp_df.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=comp_df[dimension], y=comp_df["pct_real"],
        name="Real", marker_color="#113476",
    ))
    fig.add_trace(go.Bar(
        x=comp_df[dimension], y=comp_df["pct_ideal"],
        name="Ideal", marker_color="#cbd5e0",
    ))
    fig.update_layout(
        title=title, barmode="group",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#f8fafc", height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def render():
    tema.aplicar_layout()
    st.header("🔀 Visão Mix")

    df_sell = st.session_state.get("df_sell_out")
    if df_sell is None or df_sell.empty:
        st.warning("⚠️ Importe os dados de Sell Out na aba **Importar Dados** para visualizar este dashboard.")
        return

    df_results = run_forecast_and_inventory()
    if df_results is None or df_results[0] is None:
        st.warning("⚠️ Importe os dados de Sell-Out para visualizar a análise de mix.")
        return
        
    df_inv, period_str = df_results
    st.info(f"📅 **Período de Referência (KPIs Atuais):** {period_str}")

    ideal_mix = get_config("ideal_mix", DEFAULT_IDEAL_MIX)
    price_ranges = get_config("price_ranges", DEFAULT_PRICE_RANGES)

    # --- LIMPEZA DE DADOS (Data Standardization) ---
    # Padroniza para MAIÚSCULO para evitar duplicações por case/espaço
    for col in ["segmento", "genero", "publico"]:
        if col in df_inv.columns:
            df_inv[col] = df_inv[col].astype(str).str.upper().str.strip()
    
    # Padroniza as chaves do Mix Ideal para garantir o Batimento (Match)
    if isinstance(ideal_mix, dict):
        new_ideal = {}
        for dim, mapping in ideal_mix.items():
            if isinstance(mapping, dict):
                new_ideal[dim] = {str(k).upper().strip(): v for k, v in mapping.items()}
            else:
                new_ideal[dim] = mapping
        ideal_mix = new_ideal

    # ─── Filtrar por cliente (Sidebar) ───
    with st.sidebar:
        st.divider()
        clientes = sorted(df_inv["cliente"].unique())
        choice = st.selectbox("Filtrar por cliente", ["📊 Todos os Clientes"] + clientes)

    if choice != "📊 Todos os Clientes":
        df_inv = df_inv[df_inv["cliente"] == choice]

    st.divider()

    # ─── Pies ───
    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.subheader("📊 Mix por Segmento")
        seg_mix = calculate_mix(df_inv, "segmento")
        if not seg_mix.empty:
            fig = px.pie(seg_mix, values="venda", names="segmento",
                         color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                              font_color="#ccd6f6", height=380)
            st.plotly_chart(fig, use_container_width=True)

    with chart_cols[1]:
        st.subheader("📊 Mix por Gênero")
        gen_mix = calculate_mix(df_inv, "genero")
        if not gen_mix.empty:
            fig = px.pie(gen_mix, values="venda", names="genero",
                         color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4)
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                              font_color="#ccd6f6", height=380)
            st.plotly_chart(fig, use_container_width=True)

    chart_cols2 = st.columns(2)
    with chart_cols2[0]:
        st.subheader("📊 Mix por Público")
        pub_mix = calculate_mix(df_inv, "publico")
        if not pub_mix.empty:
            fig = px.pie(pub_mix, values="venda", names="publico",
                         color_discrete_sequence=px.colors.qualitative.Safe, hole=0.4)
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                              font_color="#ccd6f6", height=380)
            st.plotly_chart(fig, use_container_width=True)

    with chart_cols2[1]:
        st.subheader("📊 Mix por Faixa de Preço")
        price_mix = calculate_price_ranges(df_inv, price_ranges)
        if not price_mix.empty:
            fig = px.pie(price_mix, values="venda", names="faixa_preco",
                         color_discrete_sequence=["#00b894", "#fdcb6e", "#e17055", "#6c5ce7"], hole=0.4)
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                              font_color="#ccd6f6", height=380)
            st.plotly_chart(fig, use_container_width=True)

    # ─── Comparação ───
    st.divider()
    st.subheader("🎯 Comparação com Mix Ideal")
    comparisons = {}
    dimensions = [("segmento", "Segmento"), ("genero", "Gênero"), ("publico", "Público")]
    comp_cols = st.columns(3)
    for i, (dim, label) in enumerate(dimensions):
        actual = calculate_mix(df_inv, dim)
        if not actual.empty and dim in ideal_mix:
            comp = compare_with_ideal(actual, ideal_mix[dim], dim)
            comparisons[dim] = comp
            with comp_cols[i]:
                fig = _make_comparison_chart(comp, dim, f"Real vs Ideal — {label}")
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Análise de Gaps")
    for dim, label in dimensions:
        if dim in comparisons:
            comp = comparisons[dim]
            st.markdown(f"**{label}**")
            styled = comp.style.format({
                "pct_real": "{:.1f}%", "pct_ideal": "{:.1f}%", "gap": "{:+.1f}pp",
            }).apply(
                lambda x: ["background-color: #742a2a; color: #f8fafc;" if v < -5 else
                           "background-color: #1a3a3a; color: #f8fafc;" if v > 5 else ""
                           for v in x], subset=["gap"],
            )
            st.dataframe(styled, use_container_width=True)


if __name__ == "__main__":
    render()
