"""
Funções auxiliares compartilhadas entre páginas.
Centraliza a execução dos motores com todos os parâmetros regionais e de lead time.
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from config import (
    DEFAULT_SEASON_CALENDAR, DEFAULT_SEASONALITY, DEFAULT_SAFETY_STOCK_PCT,
    DEFAULT_REGIONAL_SEASONALITY_SEGMENT, DEFAULT_CLIENT_REGIONS, DEFAULT_LEAD_TIME_DAYS,
    DEFAULT_DAYS_WITHOUT_PURCHASE, DEFAULT_COVERAGE_RUPTURE_THRESHOLD,
    DEFAULT_COVERAGE_EXCESS_THRESHOLD, DEFAULT_IDEAL_MIX,
    DEFAULT_MONTHLY_SEASONALITY, DEFAULT_RETAIL_EVENTS,
    DEFAULT_DAYS_SAFETY, DEFAULT_MONTHLY_CAPACITY, DEFAULT_RECEIPT_WINDOW_MONTHS,
)
from engines.forecast import run_forecast_engine
from engines.inventory import calculate_inventory
from engines.opportunities import run_opportunity_engine
from engines.alerts import generate_alerts
from engines.mix_analysis import calculate_mix, compare_with_ideal


def apply_professional_layout():
    """Aplica o CSS global para transformar a interface em um SaaS moderno."""
    st.markdown('''
        <style>
            /* --- SaaS Design Tokens --- */
            :root {
                --brand-blue: #113476;
                --brand-bg-light: #F8F9FA;
                --brand-card-light: #FFFFFF;
                --brand-text-dark: #2D3748;
                --brand-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }

            /* Main Container Adjustments */
            .block-container { 
                padding-top: 1.5rem !important; 
                padding-bottom: 2rem !important; 
                padding-left: 2rem !important; 
                padding-right: 2rem !important; 
                max-width: 100%; 
            }
            
            /* Sidebar Styling */
            [data-testid='stSidebarNav'] { background-color: transparent !important; }
            section[data-testid="stSidebar"] {
                border-right: 1px solid rgba(0,0,0,0.05);
                box-shadow: 2px 0 10px rgba(0,0,0,0.02);
            }

            /* SaaS Card Style */
            .v-card {
                background: white;
                border-radius: 12px;
                padding: 1.25rem;
                box-shadow: var(--brand-shadow);
                border: 1px solid #edf2f7;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                margin-bottom: 1rem;
            }
            .v-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            }

            /* Badge System */
            .v-badge {
                padding: 4px 10px;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            /* Typography & Headers */
            h1, h2, h3 { 
                color: var(--brand-blue) !important; 
                font-family: 'Inter', sans-serif;
                font-weight: 700 !important;
            }

            /* Customizing Streamlit widgets to match brand */
            .stButton > button {
                border-radius: 8px !important;
                font-weight: 600 !important;
                transition: all 0.2s !important;
            }
            .stButton > button[kind="primary"] {
                background-color: var(--brand-blue) !important;
                color: white !important;
                border: none !important;
            }
            .stButton > button:hover {
                box-shadow: 0 4px 12px rgba(17, 52, 118, 0.2) !important;
            }
            
            /* BI Table/DataFrame Styling */
            [data-testid="stDataFrame"] {
                border-radius: 10px;
                overflow: hidden;
                border: 1px solid #edf2f7;
            }

            /* Responsive Adjustments */
            @media (max-width: 768px) {
                .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
            }
        </style>
    ''', unsafe_allow_html=True)


def get_config(key, default):
    return st.session_state.get(f"cfg_{key}", default)


def _filter_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """
    Refatorado: Não filtra mais linhas.
    Retorna o DF completo para garantir visibilidade total.
    """
    return df


def get_analysis_regions() -> list[str]:
    """Retorna lista de regiões selecionadas manualmente pelo usuário."""
    return st.session_state.get("cfg_analysis_regions", [])


def run_forecast_and_inventory():
    """Executa forecast + inventory com todos os parâmetros atuais."""
    df_sell_all = st.session_state.get("df_sell_out")
    if df_sell_all is None or df_sell_all.empty:
        return None, "Importe os dados de Sell-Out para começar."

    # 1. Identificar Período Mais Recente GLOBAL (Arquivo Inteiro)
    df_temp = df_sell_all.copy()
    df_temp["_y"] = pd.to_numeric(df_temp["ano_venda"], errors="coerce").fillna(0).astype(int)
    df_temp["_m"] = pd.to_numeric(df_temp["mes_venda"], errors="coerce").fillna(0).astype(int)
    df_temp["_period_score"] = df_temp["_y"] * 100 + df_temp["_m"]
    
    # Maior período global no arquivo
    periodo_recente_global = df_temp["_period_score"].max()
    
    if periodo_recente_global == 0:
        return None, "Período inválido (Ano/Mês faltando)"

    # Formatar string de período para UI
    ult_ano = periodo_recente_global // 100
    ult_mes = periodo_recente_global % 100
    period_str = f"{ult_mes:02d}/{ult_ano}"
    
    # Pegar os metadados (modelo, linha, etc) da linha MAIS RECENTE de cada SKU
    df_sorted = df_temp.sort_values("_period_score", ascending=False)
    
    # Colunas de metadados a preservar
    meta_cols = ["cliente", "produto", "segmento", "linha", "modelo", "genero", "publico", "preco_pdv", "ano_venda", "mes_venda", "descricao_produto"]
    for c in ["status", "classificacao", "status_estrategico", "referencia"]:
        if c in df_sorted.columns:
            meta_cols.append(c)
            
    all_skus = df_sorted.drop_duplicates(["cliente", "produto"])[meta_cols].copy()
    
    # Separar Atual (Mês global)
    df_current_rows = df_temp[df_temp["_period_score"] == periodo_recente_global].copy()
    
    # Garantir que TODOS os SKUs apareçam no "Atual", mesmo que com 0 venda/estoque no mês global
    df_sell_current = pd.merge(
        all_skus, 
        df_current_rows[["cliente", "produto", "venda", "estoque"]], 
        on=["cliente", "produto"], 
        how="left"
    )
    df_sell_current["venda"] = df_sell_current["venda"].fillna(0)
    df_sell_current["estoque"] = df_sell_current["estoque"].fillna(0)
    
    # Histórico (Tudo o que for estritamente anterior ao global recente)
    df_sell_history_extra = df_temp[df_temp["_period_score"] < periodo_recente_global].copy()
    df_hist_base = st.session_state.get("df_historico")
    if df_sell_history_extra.empty:
        df_hist_merged = df_hist_base
    else:
        hist_extra = df_sell_history_extra.copy()
        hist_extra["mes"] = hist_extra.apply(lambda r: f"{int(r['ano_venda'])}-{int(r['mes_venda']):02d}", axis=1)
        
        if df_hist_base is not None and not df_hist_base.empty:
            df_hist_merged = pd.concat([df_hist_base, hist_extra[["cliente", "produto", "mes", "venda"]]], ignore_index=True)
        else:
            df_hist_merged = hist_extra[["cliente", "produto", "mes", "venda"]]
    
    df_pedidos = st.session_state.get("df_pedidos")
    calendar = get_config("season_calendar", DEFAULT_SEASON_CALENDAR)
    seasonality = get_config("seasonality", DEFAULT_SEASONALITY)
    safety_days = get_config("days_safety", DEFAULT_DAYS_SAFETY)
    monthly_capacity = get_config("monthly_capacity", DEFAULT_MONTHLY_CAPACITY)
    regional = get_config("sazonalidade_regional_segmento", DEFAULT_REGIONAL_SEASONALITY_SEGMENT)
    analysis_regions = get_analysis_regions()
    lead_time = get_config("lead_time_days", DEFAULT_LEAD_TIME_DAYS)
    now = datetime.now()
    monthly_saz = get_config("monthly_seasonality", DEFAULT_MONTHLY_SEASONALITY)
    retail_events = get_config("retail_events", DEFAULT_RETAIL_EVENTS)

    df_fc = run_forecast_engine(
        df_sell_current, df_hist_merged, calendar, seasonality,
        current_month=ult_mes,
        regional_table=regional,
        analysis_regions=analysis_regions,
        lead_time_days=lead_time,
        reference_date=now,
        monthly_seasonality=monthly_saz,
    )

    # ─── GESTÃO DE ESTOQUE EM TRÂNSITO (Recebimento Programado) ───
    df_recebimento = st.session_state.get("df_recebimento_programado")
    df_transito_map = pd.DataFrame()
    
    if df_recebimento is not None and not df_recebimento.empty:
        df_rp = df_recebimento.copy()
        
        # Mapeamento Explícito de Chaves (Garante match se o ETL falhou)
        rename_map_rp = {
            "Cod. Referencia": "produto",
            "Produto - Codigo Referencia": "produto",
            "Referencia": "produto"
        }
        for old_col, new_col in rename_map_rp.items():
            if old_col in df_rp.columns and new_col not in df_rp.columns:
                df_rp = df_rp.rename(columns={old_col: new_col})

        df_rp["data_entrega"] = pd.to_datetime(df_rp["data_entrega"], errors="coerce")
        
        # Enriquecer com metadados (Segmento, Gênero, Público)
        # Drop columns if they already exist to avoid MergeError/suffixes on reruns
        cols_to_drop = [c for c in ["segmento", "genero", "publico"] if c in df_rp.columns]
        if cols_to_drop:
            df_rp = df_rp.drop(columns=cols_to_drop)

        # Garantir chaves rigorosas (String + Trim) para evitar falhas de Join
        df_rp["produto"] = df_rp["produto"].astype(str).str.strip()
        all_skus_clean = all_skus.copy()
        all_skus_clean["produto"] = all_skus_clean["produto"].astype(str).str.strip()

        df_rp = df_rp.merge(
            all_skus_clean[["cliente", "produto", "segmento", "genero", "publico"]].drop_duplicates(),
            on=["cliente", "produto"],
            how="left"
        )
        
        # NOVA REGRA: Se o Mês de Entrega >= Mês Atual -> Estoque em Trânsito
        # Consideramos o mês atual real ou o mês de referência visual
        limiar_mes = datetime(now.year, now.month, 1)
        
        df_rp["estoque_transito"] = np.where(
            (df_rp["data_entrega"] >= limiar_mes),
            pd.to_numeric(df_rp["quantidade"], errors="coerce").fillna(0),
            0
        )
        
        # Salvar enriquecido de volta no state para os motores
        st.session_state["df_recebimento_programado"] = df_rp
        
        # AGGREGAÇÃO: Somar trânsito e pegar a data do PRÓXIMO recebimento
        # Apenas para registros que são trânsito (estoque_transito > 0)
        df_rp_future = df_rp[df_rp["estoque_transito"] > 0].copy()
        
        if not df_rp_future.empty:
            df_transito_map = df_rp_future.groupby(["cliente", "produto"]).agg({
                "estoque_transito": "sum",
                "data_entrega": "min" # Data do próximo recebimento
            }).reset_index()
        else:
            df_transito_map = pd.DataFrame(columns=["cliente", "produto", "estoque_transito", "data_entrega"])

    # Filtrar Pedidos por Região (Passo 4.1)
    df_pedidos_raw = st.session_state.get("df_pedidos")
    df_pedidos = _filter_by_region(df_pedidos_raw)

    df_inv = calculate_inventory(
        df_fc, df_pedidos, 
        safety_days=safety_days,
        lead_time_days=lead_time,
        reference_date=now,
        retail_events=retail_events,
        monthly_capacity=monthly_capacity,
    )

    # Acoplar Estoque em Trânsito ao Resultado Final
    if not df_transito_map.empty:
        # Se o trânsito for 'Global' (vindo da matriz simplificada), ele deve casar com qualquer cliente
        # Caso contrário, casa por cliente e produto.
        if (df_transito_map["cliente"] == "Global").all():
            # Merge apenas por produto (ignora cliente 'Global' no mapa)
            df_transito_prod = df_transito_map.groupby("produto").agg({
                "estoque_transito": "sum",
                "data_entrega": "min"
            }).reset_index()
            df_inv = df_inv.merge(df_transito_prod, on="produto", how="left")
        else:
            # Merge específico por cliente e produto
            df_inv = df_inv.merge(df_transito_map, on=["cliente", "produto"], how="left")
    
    if "estoque_transito" not in df_inv.columns:
        df_inv["estoque_transito"] = 0
    else:
        df_inv["estoque_transito"] = df_inv["estoque_transito"].fillna(0).astype(int)

    # Ajuste na Sugestão de Compra (Subtrair Trânsito)
    # Sugestão = Necessidade - Trânsito
    df_inv["pedido_sugerido"] = (df_inv["pedido_sugerido"] - df_inv["estoque_transito"]).clip(lower=0).round(0)

    return df_inv, period_str


def run_all_engines():
    """Executa todos os motores (previsão, estoque, oportunidades, substituição, alertas)."""
    # 1. Preparar dados (Current vs History)
    df_sell_all = st.session_state.get("df_sell_out")
    if df_sell_all is None or df_sell_all.empty:
        return None, None, None, None, "Dados não carregados"

    # Re-utilizamos run_forecast_and_inventory que já faz o split
    df_inv, period_str = run_forecast_and_inventory()
    if df_inv is None:
        return None, None, None, None, period_str

    # Pegamos df_sell_current do período de referência para outros motores
    # Identificar Período Mais Recente GLOBAL
    df_temp = df_sell_all.copy()
    df_temp["_y"] = pd.to_numeric(df_temp["ano_venda"], errors="coerce").fillna(0).astype(int)
    df_temp["_m"] = pd.to_numeric(df_temp["mes_venda"], errors="coerce").fillna(0).astype(int)
    df_temp["_id"] = df_temp["_y"] * 100 + df_temp["_m"]
    periodo_recente_global = df_temp["_id"].max()
    
    # Sincronizar status_estrategico se houver (v5.0)
    # Se houver uma tabela de status no session_state, aplicamos aqui
    status_map = st.session_state.get("status_estrategico_map", {})
    if status_map:
        # O map é { (cliente, produto): status }
        def apply_status(row):
            key = (str(row["cliente"]), str(row["produto"]))
            return status_map.get(key, row.get("status_estrategico", "Indefinido"))
        
        df_temp["status_estrategico"] = df_temp.apply(apply_status, axis=1)

    # Current (apenas o mês global)
    df_sell_current = df_temp[df_temp["_id"] == periodo_recente_global].copy()

    df_campeoes = st.session_state.get("df_campeoes")
    df_recebimento = st.session_state.get("df_recebimento_programado")

    retail_events = get_config("retail_events", DEFAULT_RETAIL_EVENTS)
    days_thresh = get_config("days_threshold", DEFAULT_DAYS_WITHOUT_PURCHASE)
    lead_time = get_config("lead_time_days", DEFAULT_LEAD_TIME_DAYS)
    receipt_window = get_config("receipt_window_months", DEFAULT_RECEIPT_WINDOW_MONTHS)
    now = datetime.now()

    # Opportunities
    opps = run_opportunity_engine(
        df_sell_current, df_campeoes, df_recebimento, 
        df_inventory=df_inv, 
        retail_events=retail_events,
        days_threshold=days_thresh, 
        receipt_window_months=receipt_window,
        reference_date=now
    )

    # Substitutions - REMOVED per user request
    subs = None

    # Mix comparison for alerts
    ideal_mix = get_config("ideal_mix", DEFAULT_IDEAL_MIX)
    mix_comparisons = {}
    for dim in ["segmento", "genero", "publico"]:
        actual = calculate_mix(df_inv, dim)
        if not actual.empty and dim in ideal_mix:
            mix_comparisons[dim] = compare_with_ideal(actual, ideal_mix[dim], dim)

    # Alerts
    receipt_window = get_config("receipt_window_months", DEFAULT_RECEIPT_WINDOW_MONTHS)
    alerts = generate_alerts(
        df_inv, df_campeoes, df_recebimento, mix_comparisons,
        get_config("coverage_rupture", DEFAULT_COVERAGE_RUPTURE_THRESHOLD),
        get_config("coverage_excess", DEFAULT_COVERAGE_EXCESS_THRESHOLD),
        days_thresh, now,
        lead_time_days=lead_time,
        receipt_window_months=receipt_window,
    )

    return opps, subs, alerts, df_inv, period_str
