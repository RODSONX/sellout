"""
Página 3 — Visão Produto
Dashboard por produto com vendas, estoque, cobertura e faturamento.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tema
from helpers import run_forecast_and_inventory, apply_professional_layout

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

def render():
    tema.aplicar_layout()
    st.header("📦 Visão Produto")

    df_sell = st.session_state.get("df_sell_out")
    if df_sell is None or df_sell.empty:
        st.warning("⚠️ Importe os dados de Sell Out na aba **Importar Dados** para visualizar este dashboard.")
        return

    df_results = run_forecast_and_inventory()
    if df_results is None or (isinstance(df_results, tuple) and df_results[0] is None):
        st.warning("⚠️ Importe os dados de Sell-Out para visualizar a análise por produto.")
        return

    df_inv, period_str = df_results
    st.info(f"📅 **Período de Referência (KPIs Atuais):** {period_str}")

    # ─── Filtros (Sidebar) ───
    def reset_filters():
        st.session_state.filter_seg = "Todos"
        st.session_state.filter_gen = "Todos"
        st.session_state.filter_pub = "Todos"
        st.session_state.filter_lin = "Todas"
        st.session_state.sapato_selecionado = None

    with st.sidebar:
        st.divider()
        segs = ["Todos"] + sorted(df_inv["segmento"].dropna().unique().tolist())
        sel_seg = st.selectbox("Segmento", segs, key="filter_seg")
        
        gens = ["Todos"] + sorted(df_inv["genero"].dropna().unique().tolist())
        sel_gen = st.selectbox("Gênero", gens, key="filter_gen")
        
        pubs = ["Todos"] + sorted(df_inv["publico"].dropna().unique().tolist())
        sel_pub = st.selectbox("Público", pubs, key="filter_pub")
        
        linhas = ["Todas"] + sorted(df_inv["linha"].dropna().unique().tolist())
        sel_lin = st.selectbox("Linha", linhas, key="filter_lin")

        st.divider()
        st.button("🗑️ Limpar Filtros", use_container_width=True, on_click=reset_filters)

    df = df_inv.copy()
    if sel_seg != "Todos":
        df = df[df["segmento"] == sel_seg]
    if sel_gen != "Todos":
        df = df[df["genero"] == sel_gen]
    if sel_pub != "Todos":
        df = df[df["publico"] == sel_pub]
    if sel_lin != "Todas":
        df = df[df["linha"] == sel_lin]

    # ─── Resumo por Produto ───
    prod_summary = df.groupby(["produto", "segmento", "linha", "genero", "publico"]).agg(
        venda_total=("venda", "sum"),
        estoque_total=("estoque", "sum"),
        demanda_prevista=("demanda_prevista", "sum"),
        faturamento=("faturamento_estimado", "sum"),
        preco_medio=("preco_pdv", "mean"),
        n_clientes=("cliente", "nunique"),
    ).reset_index()

    prod_summary["cobertura"] = (
        prod_summary["estoque_total"] / prod_summary["demanda_prevista"].replace(0, 1)
    ).round(2)
    prod_summary = prod_summary.sort_values("venda_total", ascending=False)

    # ─── KPIs ───
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.metric("🔢 Produtos", f"{prod_summary['produto'].nunique()}")
    with kpi_cols[1]:
        st.metric("🛒 Vendas Total", f"{prod_summary['venda_total'].sum():,.0f}")
    with kpi_cols[2]:
        st.metric("📦 Estoque Total", f"{prod_summary['estoque_total'].sum():,.0f}")
    with kpi_cols[3]:
        st.metric("💰 Faturamento", f"R$ {prod_summary['faturamento'].sum():,.2f}")

    # ─── Charts ───
    chart_cols = st.columns(2)

    with chart_cols[0]:
        st.subheader("🏆 Top 15 Produtos por Venda")
        top = prod_summary.head(15)
        fig = px.bar(
            top, x="venda_total", y="produto", orientation="h",
            color="segmento",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#f8fafc", height=450, yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with chart_cols[1]:
        st.subheader("🔄 Distribuição de Cobertura")
        fig2 = px.histogram(
            prod_summary, x="cobertura", nbins=20,
            color_discrete_sequence=["#113476"],
        )
        fig2.add_vline(x=1, line_dash="dash", line_color="#ff6b6b", annotation_text="1 mês")
        fig2.add_vline(x=0.5, line_dash="dot", line_color="#ff4444", annotation_text="Ruptura")
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#f8fafc", height=450,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ─── Tabela ───
    st.subheader("📋 Tabela de Produtos")
    st.dataframe(
        prod_summary.style.format({
            "venda_total": "{:.0f}",
            "estoque_total": "{:.0f}",
            "demanda_prevista": "{:.1f}",
            "faturamento": "R$ {:,.2f}",
            "preco_medio": "R$ {:,.2f}",
            "cobertura": "{:.1f}",
        }).apply(
            lambda x: [
                "background-color: #742a2a; color: #f8fafc; font-weight: bold;" if v < 0.33 else
                "background-color: #9b2c2c; color: #f8fafc;" if v < 0.6 else
                "background-color: #744210; color: #f8fafc;" if v < 1.0 else
                "background-color: #22543d; color: #f8fafc;" for v in x
            ],
            subset=["cobertura"]
        ),
        use_container_width=True,
        height=500,
    )

    # ─── Export ───
    buffer = BytesIO()
    prod_summary.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    st.download_button(
        "📥 Exportar para Excel",
        data=buffer,
        file_name="visao_produto.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    render()
