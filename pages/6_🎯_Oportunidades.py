"""
Página 5 — Oportunidades e Alertas
Detecção de oportunidades, substituição de produtos e alertas automáticos.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import tema
from helpers import run_all_engines, apply_professional_layout, get_config
from config import DEFAULT_RETAIL_EVENTS, DEFAULT_IDEAL_MIX, DEFAULT_SEASON_CALENDAR, DEFAULT_CLIENT_REGIONS

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')
def render():
    tema.aplicar_layout()
    st.header("🎯 Oportunidades & Alertas")

    df_sell = st.session_state.get("df_sell_out")
    if df_sell is None or df_sell.empty:
        st.warning("⚠️ Importe os dados de Sell Out na aba **Importar Dados** para visualizar este dashboard.")
        return

    results = run_all_engines()
    if results is None:
        st.warning("⚠️ Dados insuficientes para gerar análises.")
        return

    opps, subs, alerts, df_inv, period_str = results
    st.info(f"📅 **Período de Referência (KPIs Atuais):** {period_str}")

    # Removemos o filtro de cliente individual para focar na visão consolidada
    selected_client = "Todos"

    # ─── Alertas ───
    st.subheader("🚨 Alertas Automáticos")
    if alerts is not None and not alerts.empty:
        alert_counts = alerts["tipo"].value_counts()
        n_cols = min(len(alert_counts), 6)
        a_cols = st.columns(n_cols)
        for i, (tipo, count) in enumerate(alert_counts.items()):
            with a_cols[i % n_cols]:
                st.markdown(f"""
                <div class="v-card" style="padding: 12px; margin: 0; background: #0f172a; border: 1px solid #1e293b; border-radius: 12px;">
                    <p style="color: #cbd5e0; font-size: 0.75rem; margin: 0; font-weight:600;">{tipo}</p>
                    <p style="color: #38bdf8; font-size: 1.8rem; font-weight: 800; margin: 4px 0;">{count}</p>
                </div>
                """, unsafe_allow_html=True)

        with st.expander("📋 Ver todos os alertas", expanded=False):
            # Preparar DF para exibição profissional
            df_alert_show = alerts.copy()
            
            # Renomear colunas técnicas para nomes amigáveis
            rename_map = {
                "tipo": "Tipo de Alerta",
                "severidade": "Severidade",
                "cliente": "Cliente",
                "produto_desc": "Produto (Ref / Desc)",
                "data_ultimo_mes_ano": "Último Recebimento",
                "venda_recente": "Qtde Venda",
                "estoque_atual": "Qtde Estoque",
                "segmento": "Produto - Segmento",
                "linha": "Produto - Linha",
                "publico": "Produto - Publico",
                "genero": "Produto - Genero",
                "detalhe": "Detalhes"
            }
            
            # Ordenação baseada em Venda (DESC) e Estoque (ASC) para destacar riscos
            if "venda_recente" in df_alert_show.columns:
                df_alert_show = df_alert_show.sort_values(
                    by=["venda_recente", "estoque_atual"], 
                    ascending=[False, True]
                )

            df_alert_show = df_alert_show.rename(columns=rename_map)
            
            # Selecionar e ordenar colunas (se existirem)
            cols_order = [c for c in rename_map.values() if c in df_alert_show.columns]
            df_alert_show = df_alert_show[cols_order]
            
            st.dataframe(df_alert_show, use_container_width=True, height=400)
    else:
        st.success("✅ Nenhum alerta ativo. Tudo em ordem!")

    st.subheader("💡 Insights Inteligentes (Visão Consolidada)")
    
    # Preparar dados Consolidados
    df_client_inv = df_inv
    df_client_sell = df_sell

    # 1. Card: Ruptura de Categorias (Gênero + Segmento)
    # Identificar onde vendeu no passado mas hoje está com estoque + transito 0
    hist_sales = df_client_sell.groupby(["genero", "segmento"])["venda"].sum().reset_index()
    curr_stock = df_client_inv.groupby(["genero", "segmento"]).agg({
        "estoque": "sum",
        "estoque_transito": "sum"
    }).reset_index()
    
    df_ruptura = pd.merge(hist_sales, curr_stock, on=["genero", "segmento"], how="left").fillna(0)
    df_ruptura = df_ruptura[
        (df_ruptura["venda"] > 0) & 
        ((df_ruptura["estoque"] + df_ruptura["estoque_transito"]) == 0)
    ].sort_values("venda", ascending=False)

    # 2. Card: Alerta de Mix Pobre (Mantido)
    # Categorias com apenas 1 ou 2 modelos distintos em estoque
    df_mix = df_client_inv[df_client_inv["estoque"] > 0].groupby(["genero", "segmento"])["produto"].nunique().reset_index()
    df_mix.columns = ["genero", "segmento", "quantidade_modelos"]
    df_mix_pobre = df_mix[df_mix["quantidade_modelos"] <= 2].sort_values("quantidade_modelos")

    # 3. Card: Campeões com Risco de Ruptura
    # Modelos com venda alta mas estoque < 1 mês de venda
    df_campeoes = df_client_inv.copy()
    df_campeoes["giro_mensal"] = df_campeoes["venda"].clip(lower=1)
    
    # NOVA FÓRMULA: Sugestão = Giro - (Estoque + Trânsito)
    df_campeoes["sugestao_reposicao"] = (df_campeoes["giro_mensal"] * 1.5 - (df_campeoes["estoque"] + df_campeoes["estoque_transito"])).round(0)
    
    # Filtrar Campeões com Risco (Giro >= 5 e Sugestão > 0)
    # Supressão Inteligente: Se Sugestão <= 0, oculta a recomendação
    df_campeoes_risco = df_campeoes[
        (df_campeoes["giro_mensal"] >= 5) & 
        (df_campeoes["sugestao_reposicao"] > 0)
    ].copy()
    
    df_campeoes_risco = df_campeoes_risco[["produto", "segmento", "venda", "estoque", "estoque_transito", "sugestao_reposicao"]].sort_values("venda", ascending=False)

    # RENDERIZAÇÃO DOS ACCORDIONS (EXPANDERS)
    
    # 🟢 Accordion 1: Rupturas
    with st.expander(f"🚩 Ruptura de Categorias ({len(df_ruptura)})", expanded=False):
        if not df_ruptura.empty:
            st.markdown("Categorias que já venderam no cliente mas hoje estão com **Estoque Zero**:")
            st.table(df_ruptura.rename(columns={"venda": "Venda Histórica", "estoque": "Estoque Atual"}))
        else:
            st.success("Nenhuma categoria zerada com histórico de vendas detectada.")

    # 🟠 Accordion 2: Mix Pobre
    with st.expander(f"⚖️ Alerta de Mix Pobre ({len(df_mix_pobre)})", expanded=False):
        if not df_mix_pobre.empty:
            st.markdown("Categorias com baixa variedade (apenas 1 ou 2 modelos em estoque):")
            st.table(df_mix_pobre.rename(columns={"quantidade_modelos": "Modelos Ativos"}))
            st.warning("Recomendação: Aumente o mix desses segmentos para oferecer mais opções ao consumidor.")
        else:
            st.success("O cliente possui boa variedade de modelos em todos os segmentos ativos.")

    # 🔵 Accordion 3: Campeões com Risco (Transparência na Recomendação)
    with st.expander(f"🔥 Campeões com Risco de Ruptura ({len(df_campeoes_risco)})", expanded=False):
        if not df_campeoes_risco.empty:
            st.markdown("Produtos de alto giro com necessidade de reposição (considerando o trânsito):")
            
            # Exibição Transparente: Estoque Loja | Em Trânsito | Sugestão
            df_campeoes_display = df_campeoes_risco.rename(columns={
                "produto": "Código", 
                "venda": "Giro", 
                "estoque": "Estoque Loja", 
                "estoque_transito": "Em Trânsito",
                "sugestao_reposicao": "Sugestão Pedido"
            })
            
            st.dataframe(df_campeoes_display, use_container_width=True)
            st.markdown("> **Cálculo:** `Sugestão = Giro - (Estoque Atual + Trânsito)`")
            st.caption("A sugestão é suprimida automaticamente se o estoque atual + trânsito cobrirem a demanda.")
        else:
            st.success("Todos os produtos campeões possuem estoque físico + trânsito suficiente para a demanda projetada.")

    # 🔵 Accordion 4: Sazonalidade e Recebimento Programado
    lead_time = get_config("lead_time_days", 60)
    hoje = datetime.now()
    data_entrega_estimada = hoje + pd.Timedelta(days=lead_time)
    mes_foco = data_entrega_estimada.month
    estacoes = get_config("season_calendar", DEFAULT_SEASON_CALENDAR)
    estacao_entrega = estacoes.get(mes_foco, "Geral")
    retail_events = get_config("retail_events", DEFAULT_RETAIL_EVENTS)
    evento = next((e for e in retail_events if e["mes"] == mes_foco), None)

    # Lógica Regional (Visão Consolidada usa Região Geral ou Mix Consolidado)
    cliente_regiao = "Geral"
    prioridade = []
    if (cliente_regiao == "Sul" or cliente_regiao == "Sudeste") and estacao_entrega.lower() == "inverno":
        prioridade = ["bota", "pantufa", "trekking"]
    elif estacao_entrega.lower() == "verão" or estacao_entrega.lower() == "verao":
        prioridade = ["sandalia", "chinelo", "drive"]
    
    # 🟡 Accordion 4: Sazonalidade e Recebimento Programado
    with st.expander(f"🚚 Sazonalidade (Próxima Entrega: {data_entrega_estimada.strftime('%m/%Y')})", expanded=False):
        st.markdown(f"Análise focada para o mês de recebimento: **{estacao_entrega.capitalize()}**.")
        if evento:
            st.info(f"🎁 Janela de novos recebimentos para: **{evento['evento']}**.")
        
        if prioridade:
            st.markdown(f"**Prioridade estratégica para {cliente_regiao}:**")
            df_prioridade = df_client_inv[df_client_inv["segmento"].isin(prioridade)].groupby("segmento").agg({
                "estoque": "sum",
                "estoque_transito": "sum"
            }).reset_index()
            
            df_prioridade["recomendacao"] = np.where(
                (df_prioridade["estoque"] + df_prioridade["estoque_transito"]) < 10,
                "Reforçar 🚩", "Monitorar"
            )
            
            st.table(df_prioridade.rename(columns={
                "segmento": "Segmento", 
                "estoque": "Estoque Atual", 
                "estoque_transito": "Em Trânsito",
                "recomendacao": "Ação"
            }))
        else:
            st.markdown("Continue mantendo o equilíbrio do mix para a próxima estação.")

    # 🕒 Accordion 5: Comparativo Histórico (Ano a Ano)
    df_client_sell["_periodo"] = pd.to_numeric(df_client_sell["ano_venda"], errors="coerce") * 100 + pd.to_numeric(df_client_sell["mes_venda"], errors="coerce")
    periodo_max = df_client_sell["_periodo"].max()
    if pd.isna(periodo_max):
        periodo_max = 0
    periodo_ap = periodo_max - 100
    
    df_ap = df_client_sell[df_client_sell["_periodo"] == periodo_ap].groupby("segmento")["venda"].sum().reset_index()
    df_curr = df_client_inv.groupby("segmento").agg({
        "estoque": "sum",
        "estoque_transito": "sum"
    }).reset_index()
    
    yoy_merge = pd.merge(df_ap, df_curr, on="segmento", how="left").fillna(0)
    # Gap = (Estoque + Trânsito) - Venda Ano Anterior
    yoy_merge["diferenca"] = (yoy_merge["estoque"] + yoy_merge["estoque_transito"]) - yoy_merge["venda"]
    
    mes_ap = int(periodo_ap % 100)
    ano_ap = int(periodo_ap // 100)
    
    with st.expander(f"🕒 Comparativo Histórico (vs {mes_ap:02d}/{ano_ap})", expanded=False):
        if not df_ap.empty:
            st.markdown("Estoque atual comparado ao volume de vendas do **mesmo mês do ano anterior**:")
            def color_yoy(val):
                color = '#f87171' if val < 0 else '#4ade80'
                return f'color: {color}'
            
            st.dataframe(
                yoy_merge.rename(columns={
                    "segmento": "Segmento", 
                    "venda": "Vendeu em 2024", 
                    "estoque": "Estoque Hoje", 
                    "diferenca": "Gap Cobertura"
                }).style.applymap(color_yoy, subset=["Gap Cobertura"]),
                use_container_width=True
            )
            if (yoy_merge["diferenca"] < 0).any():
                st.warning("Atenção: Segmentos em vermelho não possuem estoque suficiente para repetir o volume do ano passado.")
        else:
            st.info("Sem dados de vendas do ano anterior para este período.")

    # 👑 Accordion 6: Alerta Pareto (Regra 80/20)
    df_pareto_calc = df_client_inv.copy()
    df_pareto_calc = df_pareto_calc.sort_values("venda", ascending=False)
    total_vendas_cliente = df_pareto_calc["venda"].sum()
    
    if total_vendas_cliente > 0:
        df_pareto_calc["cum_venda"] = df_pareto_calc["venda"].cumsum()
        df_pareto_calc["cum_pct"] = df_pareto_calc["cum_venda"] / total_vendas_cliente
        df_pareto_core = df_pareto_calc[df_pareto_calc["cum_pct"] <= 0.81] # Tolerância p/ 80%
        
        with st.expander(f"🏆 Regra de Ouro Pareto (TOP 80% Volume)", expanded=False):
            st.markdown(f"Estes **{len(df_pareto_core)} modelos** representam **80% do faturamento** deste cliente:")
            
            def highlight_low_stock_pareto(row):
                # Flag de Alerta: Estoque + Transito <= 2
                if (row["Estoque"] + row["Trânsito"]) <= 2:
                    return ['background-color: #7f1d1d'] * len(row)
                return [''] * len(row)

            st.dataframe(
                df_pareto_core[["produto", "segmento", "venda", "estoque", "estoque_transito"]].rename(columns={
                    "produto": "Modelo", "venda": "Giro", "estoque": "Estoque", "estoque_transito": "Trânsito"
                }).style.apply(highlight_low_stock_pareto, axis=1),
                use_container_width=True
            )
            st.info("💡 Mantenha estes itens sempre abastecidos; eles são o motor das vendas do cliente.")
    else:
         with st.expander(f"🏆 Regra de Ouro Pareto", expanded=False):
             st.info("Dados de venda insuficientes para calcular a curva ABC.")

    st.divider()

    df_results = run_all_engines()
    if df_results is None or df_results[3] is None:
        st.warning("⚠️ Importe os dados de Sell-Out para calcular as oportunidades.")
        return
        
    opps, subs, alerts, df_inv, period_str = df_results # Unpack only after safety check
    
    # ─── Oportunidades ───
    opp_tabs = st.tabs([
        "🏆 Campeões Não Vendidos",
        "📉 Abaixo da Média",
        "🚚 Sem Recebimento Recente",
        "🌟 Sazonalidade & Eventos",
    ])

    if opps is not None:
        with opp_tabs[0]:
            st.subheader("🏆 Produtos Campeões Não Vendidos pelo Cliente")
            df_camp = opps.get("campeoes_nao_vendidos", pd.DataFrame())
            if not df_camp.empty:
                st.metric("Total de oportunidades", len(df_camp))
                st.dataframe(df_camp, use_container_width=True, height=400)
            else:
                st.info("Nenhuma oportunidade deste tipo encontrada.")

        with opp_tabs[1]:
            st.subheader("📉 Produtos Vendidos Abaixo da Média do Segmento")
            df_below = opps.get("abaixo_media", pd.DataFrame())
            if not df_below.empty:
                st.metric("Produtos abaixo da média", len(df_below))
                st.dataframe(
                    df_below.style.format({
                        "venda": "{:.0f}", "media_segmento": "{:.1f}", "gap_venda": "{:.0f}",
                    }),
                    use_container_width=True, height=400,
                )
            else:
                st.info("Nenhuma oportunidade deste tipo encontrada.")

        with opp_tabs[2]:
            st.subheader("🚚 Produtos Sem Recebimento Recente")
            df_nc = opps.get("sem_recebimento_recente", pd.DataFrame())
            if not df_nc.empty:
                df_nc_display = df_nc.copy()
                
                # Renomear para nomes amigáveis conforme solicitado
                rename_cols = {
                    "venda": "Venda Recente",
                    "estoque": "Estoque Atual",
                    "segmento": "Segmento",
                    "genero": "Gênero",
                    "publico": "Público",
                    "dias_sem_receber": "Dias sem Reposição"
                }
                df_nc_display = df_nc_display.rename(columns=rename_cols)

                # Terminology adjustment for delivery date
                if "data_ultimo_recebimento" in df_nc_display.columns:
                    # Formatar data e tratar NaNs
                    df_nc_display["Último Recebimento"] = df_nc_display["data_ultimo_recebimento"].dt.strftime("%m/%Y").fillna("Sem Registro")
                    
                    # Tratar Dias sem Reposição (NaN -> Crítico)
                    if "Dias sem Reposição" in df_nc_display.columns:
                        df_nc_display["Dias sem Reposição"] = df_nc_display["Dias sem Reposição"].fillna(999).astype(int)
                        # Opcional: transformar 999 em texto no display? Melhor manter numérico para ordenação, 
                        # ou usar .style para destacar.
                    
                    # Manter as colunas solicitadas visíveis
                    cols_to_show = [
                        "cliente", "produto", "Segmento", "Gênero", "Público",
                        "Venda Recente", "Estoque Atual", "Último Recebimento", "Dias sem Reposição"
                    ]
                    # Filtrar apenas as colunas que existem
                    cols_to_show = [c for c in cols_to_show if c in df_nc_display.columns]
                    df_nc_display = df_nc_display[cols_to_show]
                
                st.metric("Produtos sem recebimento recente", len(df_nc_display))
                
                # Ordenação: Primeiro os que nunca receberam (dias == 999) ou os com maior atraso
                df_sorted = df_nc_display.sort_values(["Dias sem Reposição", "Estoque Atual"], ascending=[False, True])
                
                st.dataframe(df_sorted, use_container_width=True, height=400)
            else:
                st.info("Nenhum produto com atraso crítico de recebimento detectado.")

        with opp_tabs[3]:
            st.subheader("🌟 Oportunidades por Estação e Eventos")
            st.markdown("Recomendações baseadas na estação futura (lead time) e calendário comercial.")
            
            df_saz = opps.get("sazonais", pd.DataFrame())
            if not df_saz.empty:
                st.metric("Oportunidades sazonais", len(df_saz))
                
                # Formatação amigável
                for _, row in df_saz.iterrows():
                    with st.expander(f"📌 {row['tipo_oportunidade']} — {row['cliente']}"):
                        st.markdown(f"**Produto/Ação:** {row['produto']}")
                        st.info(row['detalhe'])
                        if row['cobertura_meses'] > 0:
                            st.markdown(f"**Cobertura atual:** {row['cobertura_meses']:.1f} meses")
            else:
                st.success("✅ O mix está bem preparado para as próximas estações e eventos!")

    st.divider()

    # --- Export ---
    st.divider()
    if alerts is not None and not alerts.empty:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            alerts.to_excel(writer, sheet_name="Alertas", index=False)
            if opps:
                for key, df in opps.items():
                    if not df.empty:
                        df.to_excel(writer, sheet_name=key[:31], index=False)
        buffer.seek(0)
        st.download_button(
            "📥 Exportar Tudo para Excel",
            data=buffer,
            file_name="oportunidades_alertas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


if __name__ == "__main__":
    render()
