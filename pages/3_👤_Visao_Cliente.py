"""
Página 2 — Visão Cliente
Dashboard por cliente com KPIs e tabela detalhada.
Inclui região do cliente e estação futura.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tema
from helpers import run_forecast_and_inventory, get_analysis_regions, get_config, apply_professional_layout

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

def render():
    tema.aplicar_layout()
    st.header("👤 Visão Cliente")

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

    # ─── Seletor de Cliente (Mover para Sidebar) ───
    with st.sidebar:
        st.divider()
        clientes = sorted(df_inv["cliente"].unique())
        all_option = "📊 Todos os Clientes"
        choice = st.selectbox("Selecione o cliente", [all_option] + clientes)

    if choice == all_option:
        df = df_inv.copy()
    else:
        df = df_inv[df_inv["cliente"] == choice].copy()

    analysis_regions = get_analysis_regions()
    regiao_display = " + ".join(analysis_regions) if analysis_regions else "Brasil inteiro"
    estacao_futura = df["estacao_futura"].iloc[0] if "estacao_futura" in df.columns and len(df) > 0 else "—"
    lead_time = df["lead_time_dias"].iloc[0] if "lead_time_dias" in df.columns and len(df) > 0 else 60

    info_cols = st.columns(3)
    info_style = """
        background: #0f172a; 
        border-radius: 12px; padding: 16px; text-align: center;
        border: 1px solid #1e293b;
    """
    with info_cols[0]:
        st.markdown(f"""
        <div style="{info_style}">
            <p style="color: #cbd5e0; font-size: 0.75rem; margin: 0; font-weight:600;">Região Analisada</p>
            <p style="color: #38bdf8; font-size: 1.1rem; font-weight: 700; margin: 4px 0;">{regiao_display}</p>
        </div>
        """, unsafe_allow_html=True)
    with info_cols[1]:
        st.markdown(f"""
        <div style="{info_style}">
            <p style="color: #cbd5e0; font-size: 0.75rem; margin: 0; font-weight:600;">Estação Futura</p>
            <p style="color: #38bdf8; font-size: 1.3rem; font-weight: 700; margin: 4px 0;">{estacao_futura.capitalize()}</p>
        </div>
        """, unsafe_allow_html=True)
    with info_cols[2]:
        st.markdown(f"""
        <div style="{info_style}">
            <p style="color: #cbd5e0; font-size: 0.75rem; margin: 0; font-weight:600;">Lead Time Logístico</p>
            <p style="color: #38bdf8; font-size: 1.3rem; font-weight: 700; margin: 4px 0;">{lead_time} dias</p>
        </div>
        """, unsafe_allow_html=True)
    
    # --- Alerta de Evento ---
    eventos_ativos = df[df["evento_nome"] != ""]["evento_nome"].unique()
    if len(eventos_ativos) > 0:
        ev_str = ", ".join(eventos_ativos)
        st.warning(f"🚀 **Ajuste Comercial Ativo:** Os pedidos sugeridos para este período consideram o evento: **{ev_str}**")

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── KPIs ───
    total_venda = df["venda"].sum()
    total_estoque = df["estoque"].sum()
    demanda_total = df["demanda_projetada"].sum() if "demanda_projetada" in df.columns else df["demanda_prevista"].sum()
    cobertura_geral = total_estoque / demanda_total if demanda_total > 0 else 0
    pedido_total = df["pedido_sugerido"].sum()
    faturamento = df["faturamento_estimado"].sum()
    ticket = faturamento / total_venda if total_venda > 0 else 0

    kpi_cols = st.columns(6)
    kpi_data = [
        ("🛒 Sell Out", f"{total_venda:,.0f}", "pares"),
        ("📦 Estoque", f"{total_estoque:,.0f}", "pares"),
        ("📈 Demanda Projetada", f"{demanda_total:,.0f}", "pares"),
        ("🔄 Cobertura", f"{cobertura_geral:.1f}", "meses"),
        ("🛍️ Pedido Sugerido", f"{pedido_total:,.0f}", "pares"),
        ("💰 Ticket Médio", f"R$ {ticket:,.2f}", ""),
    ]

    for col, (label, value, unit) in zip(kpi_cols, kpi_data):
        with col:
            st.markdown(f"""
            <div style="background: #0f172a; border-radius: 16px; padding: 20px; text-align: center; border: 1px solid #1e293b;">
                <p style="color: #cbd5e0; font-size: 0.8rem; font-weight: 600; margin: 0;">{label}</p>
                <p style="color: #f8fafc; font-size: 1.6rem; font-weight: 800; margin: 4px 0;">{value}</p>
                <p style="color: #94a3b8; font-size: 0.7rem; margin: 0; text-transform: uppercase;">{unit}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Gráficos ───
    chart_cols = st.columns(2)

    # Definir paleta de cores consistente para os segmentos
    segmentos_focados = sorted(df["segmento"].unique())
    # Usamos uma paleta qualitativa fixa mapeada para cada segmento
    color_map = {seg: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] 
                 for i, seg in enumerate(segmentos_focados)}

    with chart_cols[0]:
        st.subheader("Vendas por Segmento")
        seg_data = df.groupby("segmento")["venda"].sum().reset_index()
        fig = px.bar(
            seg_data, x="segmento", y="venda",
            color="segmento",
            color_discrete_map=color_map,
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#f8fafc",
            showlegend=False,
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

    with chart_cols[1]:
        st.subheader("Cobertura de Estoque")
        cov_data = df.groupby("segmento").agg(
            estoque=("estoque", "sum"),
            demanda=("demanda_projetada", "sum"),
        ).reset_index()
        cov_data["cobertura"] = cov_data["estoque"] / cov_data["demanda"].replace(0, 1)
        fig2 = px.bar(
            cov_data, x="segmento", y="cobertura",
            color="segmento",
            color_discrete_map=color_map,
        )
        fig2.add_hline(y=1, line_dash="dash", line_color="#ff6b6b", annotation_text="1 mês")
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#f8fafc",
            showlegend=False,
            height=350,
            yaxis_title="Cobertura (meses)",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ─── Nova Seção: Evolução de Vendas e Estoque ───
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📈 Análise de Vendas e Estoque")

    # Preparar dados históricos do cliente selecionado
    df_hist_full = df_sell.copy()
    if choice != all_option:
        df_hist_full = df_hist_full[df_hist_full["cliente"] == choice]
    
    # Criar coluna de período
    df_hist_full["periodo_dt"] = pd.to_datetime(
        df_hist_full["ano_venda"].astype(str) + "-" + df_hist_full["mes_venda"].astype(str).str.zfill(2) + "-01",
        errors="coerce"
    )
    df_hist_full = df_hist_full.dropna(subset=["periodo_dt"]).sort_values("periodo_dt")
    df_hist_full["periodo_str"] = df_hist_full["periodo_dt"].dt.strftime("%m/%y")

    # Agrupar por mês
    df_evo = df_hist_full.groupby("periodo_dt").agg({
        "venda": "sum",
        "estoque": "sum",
        "periodo_str": "first"
    }).reset_index()

    meses_unicos = df_evo["periodo_dt"].unique()
    
    if len(meses_unicos) > 1:
        # REGRA 1: MAIS DE 1 MÊS -> Gráfico de Linhas
        fig_evo = go.Figure()
        fig_evo.add_trace(go.Scatter(
            x=df_evo["periodo_str"], y=df_evo["venda"],
            name="Vendas", line=dict(color="#38bdf8", width=3),
            mode='lines+markers'
        ))
        fig_evo.add_trace(go.Scatter(
            x=df_evo["periodo_str"], y=df_evo["estoque"],
            name="Estoque", line=dict(color="#fb923c", width=3),
            mode='lines+markers'
        ))
        fig_evo.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#f8fafc",
            height=300,
            margin=dict(t=20, b=20, l=40, r=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_evo, use_container_width=True)

        # Indicadores de Performance por Segmento (MoM)
        st.markdown("<p style='font-size: 0.9rem; color: #94a3b8; font-weight: 600; margin-bottom: 10px;'>Variação por Segmento (Mês Atual vs. Anterior)</p>", unsafe_allow_html=True)
        
        # Calcular deltas por segmento
        ultimo_mes = meses_unicos[-1]
        penultimo_mes = meses_unicos[-2]
        
        df_seg_curr = df_hist_full[df_hist_full["periodo_dt"] == ultimo_mes].groupby("segmento").agg({"venda": "sum", "estoque": "sum"}).reset_index()
        df_seg_prev = df_hist_full[df_hist_full["periodo_dt"] == penultimo_mes].groupby("segmento").agg({"venda": "sum", "estoque": "sum"}).reset_index()
        
        df_deltas = pd.merge(df_seg_curr, df_seg_prev, on="segmento", suffixes=("_curr", "_prev"), how="left").fillna(0)
        
        delta_cols = st.columns(len(df_deltas) if not df_deltas.empty else 1)
        for i, row in df_deltas.iterrows():
            with delta_cols[i % len(delta_cols)]:
                v_var = ((row["venda_curr"] / row["venda_prev"]) - 1) * 100 if row["venda_prev"] > 0 else 0
                e_var = ((row["estoque_curr"] / row["estoque_prev"]) - 1) * 100 if row["estoque_prev"] > 0 else 0
                
                v_color = "#4ade80" if v_var >= 0 else "#f87171"
                e_color = "#4ade80" if e_var >= 0 else "#f87171"
                
                st.markdown(f"""
                <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; padding: 10px; margin-bottom: 10px;">
                    <p style="margin:0; font-size: 0.75rem; color: #cbd5e0; font-weight: 700; text-align:center;">{row['segmento']}</p>
                    <div style="display: flex; justify-content: space-around; margin-top: 5px;">
                        <div style="text-align:center;">
                            <p style="margin:0; font-size: 0.65rem; color: #94a3b8;">Vendas</p>
                            <p style="margin:0; font-size: 0.85rem; color: {v_color}; font-weight: 700;">{v_var:+.1f}%</p>
                        </div>
                        <div style="text-align:center;">
                            <p style="margin:0; font-size: 0.65rem; color: #94a3b8;">Estoque</p>
                            <p style="margin:0; font-size: 0.85rem; color: {e_color}; font-weight: 700;">{e_var:+.1f}%</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        # REGRA 2: APENAS 1 MÊS -> Gráfico de Barras Totais
        df_single = df_evo.iloc[0] if not df_evo.empty else {"venda": 0, "estoque": 0, "periodo_str": "—"}
        bar_data = pd.DataFrame({
            "Métrica": ["Vendas", "Estoque"],
            "Valor": [df_single["venda"], df_single["estoque"]]
        })
        fig_bar = px.bar(
            bar_data, x="Métrica", y="Valor",
            color="Métrica",
            color_discrete_map={"Vendas": "#38bdf8", "Estoque": "#fb923c"},
            text_auto=True
        )
        fig_bar.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#f8fafc",
            height=300,
            showlegend=False,
            margin=dict(t=20, b=20, l=40, r=40)
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.info("💡 Dados históricos insuficientes para análise de tendência (exibindo apenas totais atuais).")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ─── Nova Seção: Pedidos Futuros e Mix de Entregas ───
    st.divider()
    st.subheader("🚚 Pedidos Futuros e Mix de Entregas")
    
    df_rp = st.session_state.get("df_recebimento_programado")
    if df_rp is not None and not df_rp.empty:
        # 1. Preparar e Filtrar Dados
        df_future = df_rp.copy()
        if choice != "📊 Todos os Clientes":
            # Filtra pelo cliente selecionado OU pelo 'Global'
            df_future = df_future[(df_future["cliente"] == choice) | (df_future["cliente"] == "Global")]
        
        # Garantir tipo datetime
        df_future["data_entrega"] = pd.to_datetime(df_future["data_entrega"])
        
        # Filtrar mês atual e futuro
        hoje = datetime.now()
        primeiro_dia_mes = datetime(hoje.year, hoje.month, 1)
        df_future = df_future[df_future["data_entrega"] >= primeiro_dia_mes]
        
        if not df_future.empty:
            col_timeline, col_pie = st.columns([1, 1])
            
            with col_timeline:
                st.markdown("<p style='font-size: 0.95rem; color: #94a3b8; font-weight: 600;'>📅 Cronograma de Recebimento</p>", unsafe_allow_html=True)
                
                # Agrupar por mês
                df_future["mes_referencia"] = df_future["data_entrega"].dt.strftime("%m/%Y")
                df_future["sort_key"] = df_future["data_entrega"].dt.strftime("%Y-%m")
                
                meses_entrando = sorted(df_future["sort_key"].unique())
                
                for m_key in meses_entrando:
                    df_m = df_future[df_future["sort_key"] == m_key]
                    total_m = df_m["quantidade"].sum()
                    mes_label = df_m["mes_referencia"].iloc[0]
                    
                    with st.expander(f"📦 {mes_label} — Total: {total_m:,.0f} pares", expanded=True):
                        # Detalhe por produto
                        df_m_detail = df_m.groupby("produto")["quantidade"].sum().reset_index().sort_values("quantidade", ascending=False)
                        st.dataframe(
                            df_m_detail.rename(columns={"produto": "Referência", "quantidade": "Qtd"}), 
                            hide_index=True, 
                            use_container_width=True
                        )
            
            with col_pie:
                st.markdown("<p style='font-size: 0.95rem; color: #94a3b8; font-weight: 600;'>📊 Distribuição do Mix Futuro (%)</p>", unsafe_allow_html=True)
                
                # Três gráficos de pizza
                pie_tabs = st.tabs(["Segmento", "Gênero", "Público"])
                
                with pie_tabs[0]:
                    if "segmento" in df_future.columns:
                        df_seg = df_future.groupby("segmento")["quantidade"].sum().reset_index()
                        fig_p1 = px.pie(df_seg, values="quantidade", names="segmento", hole=0.4)
                        fig_p1.update_traces(textposition='inside', textinfo='percent+label')
                        fig_p1.update_layout(height=350, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc")
                        st.plotly_chart(fig_p1, use_container_width=True)
                    else:
                        st.caption("Dados de segmento indisponíveis nos pedidos.")

                with pie_tabs[1]:
                    if "genero" in df_future.columns:
                        df_gen = df_future.groupby("genero")["quantidade"].sum().reset_index()
                        fig_p2 = px.pie(df_gen, values="quantidade", names="genero", hole=0.4)
                        fig_p2.update_traces(textposition='inside', textinfo='percent+label')
                        fig_p2.update_layout(height=350, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc")
                        st.plotly_chart(fig_p2, use_container_width=True)
                    else:
                        st.caption("Dados de gênero indisponíveis nos pedidos.")

                with pie_tabs[2]:
                    if "publico" in df_future.columns:
                        df_pub = df_future.groupby("publico")["quantidade"].sum().reset_index()
                        fig_p3 = px.pie(df_pub, values="quantidade", names="publico", hole=0.4)
                        fig_p3.update_traces(textposition='inside', textinfo='percent+label')
                        fig_p3.update_layout(height=350, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc")
                        st.plotly_chart(fig_p3, use_container_width=True)
                    else:
                        st.caption("Dados de público indisponíveis nos pedidos.")
        else:
            st.info("ℹ️ Não foram encontrados pedidos programados para o período atual ou futuro deste cliente.")
    else:
        st.info("ℹ️ Importe a matriz de **Recebimento Programado** para visualizar o cronograma futuro.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Tabela Detalhada ───
    st.subheader("📋 Tabela Detalhada")

    display_cols = [
        "cliente", "produto", "segmento", "venda", "estoque", 
        "estoque_transito", "data_entrega",
        "demanda_base", "demanda_projetada", "cobertura_meses", 
        "venda_durante_leadtime", "pedido_sugerido", "evento_nome", 
        "fatur_est", "preco_pdv",
    ]
    available_cols = [c for c in display_cols if c in df.columns]
    df_display = df[available_cols].copy()
    
    # Filtro: Remover itens sem movimentação (venda 0 E estoque 0)
    # Mantemos se houver venda OU estoque OU se houver algo em trânsito (para não sumir o que está chegando)
    if "venda" in df_display.columns and "estoque" in df_display.columns:
        transito_col = "estoque_transito" if "estoque_transito" in df_display.columns else None
        if transito_col:
            df_display = df_display[
                (df_display["venda"] > 0) | 
                (df_display["estoque"] > 0) | 
                (df_display[transito_col] > 0)
            ]
        else:
            df_display = df_display[(df_display["venda"] > 0) | (df_display["estoque"] > 0)]

    fmt = {
        "venda": "{:.0f}",
        "estoque": "{:.0f}",
        "estoque_transito": "{:.0f}",
        "data_entrega": lambda x: x.strftime("%m/%Y") if pd.notna(x) else "—",
        "demanda_projetada": "{:.1f}",
        "demanda_base": "{:.1f}",
        "cobertura_meses": "{:.1f}",
        "venda_durante_leadtime": "{:.0f}",
        "pedido_sugerido": "{:.0f}",
        "fator_evento": "{:.2f}x",
        "fatur_est": "R$ {:,.2f}",
        "preco_pdv": "R$ {:,.2f}",
    }
    valid_fmt = {k: v for k, v in fmt.items() if k in available_cols}

    if "faturamento_estimado" in df_display.columns:
        df_display.rename(columns={"faturamento_estimado": "fatur_est"}, inplace=True)
        if "faturamento_estimado" in valid_fmt:
            valid_fmt["fatur_est"] = valid_fmt.pop("faturamento_estimado")

    # Rename for display
    df_display.rename(columns={
        "estoque_transito": "Em Trânsito",
        "data_entrega": "Mês de Entrega"
    }, inplace=True)
    
    if "estoque_transito" in valid_fmt:
        valid_fmt["Em Trânsito"] = valid_fmt.pop("estoque_transito")
    if "data_entrega" in valid_fmt:
        valid_fmt["Mês de Entrega"] = valid_fmt.pop("data_entrega")

    st.dataframe(
        df_display.style.format(valid_fmt).apply(
            lambda x: [
                "background-color: #742a2a; color: #f8fafc; font-weight: bold;" if v < 0.33 else
                "background-color: #9b2c2c; color: #f8fafc;" if v < 0.6 else
                "background-color: #744210; color: #f8fafc;" if v < 1.0 else
                "background-color: #22543d; color: #f8fafc;" for v in x
            ],
            subset=["cobertura_meses"]
        ).apply(
            lambda x: [
                "color: #38bdf8; font-weight: bold;" if v > 0 else "" for v in x
            ],
            subset=["Em Trânsito"]
        ),
        use_container_width=True,
        height=500,
    )

    # ─── Export ───
    buffer = BytesIO()
    df_display.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    st.download_button(
        "📥 Exportar para Excel",
        data=buffer,
        file_name=f"visao_cliente_{choice.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    render()
