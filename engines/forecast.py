"""
Motor de Previsão de Vendas.
- Média móvel (3 ou 6 meses)
- Tendência
- Sazonalidade (regional + estação futura via lead time)
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_season(month: int, calendar: dict) -> str:
    """Retorna a estação do mês com base no calendário."""
    return calendar.get(month, "verão")


def get_future_season(calendar: dict, lead_time_days: int = 60, reference_date: datetime = None) -> tuple[str, int]:
    """
    Calcula a estação futura considerando o lead time logístico.
    Retorna (estação_futura, mês_projeção).
    """
    if reference_date is None:
        reference_date = datetime.now()
    projection_date = reference_date + timedelta(days=lead_time_days)
    future_month = projection_date.month
    return get_season(future_month, calendar), future_month


def get_seasonality_factor(segment: str, season: str, seasonality_table: dict) -> float:
    """Retorna o fator de sazonalidade para segmento + estação (fallback sem região)."""
    seg = segment.lower().strip()
    return seasonality_table.get(seg, {}).get(season, 1.0)


def get_regional_seasonality_factor(
    segment: str, region: str, season: str,
    regional_table: dict, fallback_table: dict,
) -> float:
    """
    Retorna o fator de sazonalidade regional.
    Busca primeiro na tabela regional (segmento, região).
    Se não encontrar, usa a tabela de segmento como fallback.
    """
    seg = segment.lower().strip()
    key = (seg, region)
    if key in regional_table:
        return regional_table[key].get(season, 1.0)
    # Fallback: usar tabela por segmento
    return fallback_table.get(seg, {}).get(season, 1.0)


def forecast_with_history(
    history: pd.DataFrame,
    segment: str,
    season: str,
    seasonality_factor: float,
    long_history_threshold: int = 6,
    short_months: int = 3,
    long_months: int = 6,
) -> dict:
    """
    Calcula previsão de vendas com base no histórico.

    Retorna dict com:
      - media_vendas
      - tendencia
      - fator_sazonalidade
      - demanda_prevista
    """
    if history is None or history.empty:
        return _empty_forecast()

    # Ordenar por mês
    h = history.sort_values("mes", ascending=True).copy()
    vendas = h["venda"].values

    n_months = len(vendas)

    # Determinar janela de média
    if n_months >= long_history_threshold:
        window = long_months
    else:
        window = min(short_months, n_months)

    media_vendas = float(np.mean(vendas[-window:])) if window > 0 else 0

    # Tendência
    media_3 = float(np.mean(vendas[-min(3, n_months):])) if n_months > 0 else 0
    venda_ultimo = float(vendas[-1]) if n_months > 0 else 0
    tendencia = venda_ultimo / media_3 if media_3 > 0 else 1.0

    # Sazonalidade
    fator = seasonality_factor

    demanda = media_vendas * tendencia * fator

    return {
        "media_vendas": round(media_vendas, 2),
        "tendencia": round(tendencia, 4),
        "fator_sazonalidade": fator,
        "demanda_prevista": round(max(0, demanda), 2),
    }


def forecast_from_sellout(
    venda_atual: float,
    seasonality_factor: float,
) -> dict:
    """
    Previsão simplificada quando só existe o sell-out atual (sem histórico).
    Usa a venda atual como média e aplica sazonalidade.
    """
    demanda = venda_atual * seasonality_factor

    return {
        "media_vendas": round(venda_atual, 2),
        "tendencia": 1.0,
        "fator_sazonalidade": seasonality_factor,
        "demanda_prevista": round(max(0, demanda), 2),
    }


def forecast_from_segment_avg(
    segment_avg: float,
    seasonality_factor: float,
) -> dict:
    """
    Previsão usando média do segmento (para clientes sem histórico do produto).
    """
    demanda = segment_avg * seasonality_factor

    return {
        "media_vendas": round(segment_avg, 2),
        "tendencia": 1.0,
        "fator_sazonalidade": seasonality_factor,
        "demanda_prevista": round(max(0, demanda), 2),
    }


def calculate_smart_trend(vendas: np.ndarray) -> float:
    """
    Calcula a tendência inteligente com base no histórico.
    vendas: array de vendas mensais ordenadas.
    """
    n = len(vendas)
    if n < 1:
        return 1.0
    if n == 1:
        return 1.0
    
    venda_ultimo = float(vendas[-1])
    # Tentar pegar penultimo
    venda_penultimo = float(vendas[-2]) if n >= 2 else venda_ultimo
    
    # Tendência Curto Prazo (Último vs Penúltimo)
    if venda_penultimo > 0:
        cp = venda_ultimo / venda_penultimo
    else:
        cp = 1.0 if venda_ultimo == 0 else 1.5
        
    if n >= 3:
        # Tendência Média (vs 3 meses)
        media_3 = float(np.mean(vendas[-3:]))
        med = venda_ultimo / media_3 if media_3 > 0 else 1.0
        
        # Estabilidade (1 - CV)
        # Quanto menor o desvio padrão em relação à média, maior a estabilidade
        media_all = float(np.mean(vendas))
        std_all = float(np.std(vendas))
        stability = 1 - (std_all / media_all) if media_all > 0 else 0
    else:
        # Fallback para histórico curto
        med = cp
        stability = 0.5
        
    # Clipping de segurança
    cp = np.clip(cp, 0.6, 1.5)
    med = np.clip(med, 0.6, 1.5)
    stability = np.clip(stability, 0, 1)
        
    final = (0.5 * cp) + (0.3 * med) + (0.2 * stability)
    return float(np.clip(final, 0.6, 1.5))


def _empty_forecast() -> dict:
    return {
        "media_vendas": 0,
        "tendencia": 1.0,
        "fator_sazonalidade": 1.0,
        "demanda_prevista": 0,
    }


def get_monthly_seasonality_factor(month: int, segment: str, monthly_table: list[dict]) -> float:
    """
    Retorna o fator de sazonalidade mensal para um mês e segmento.
    Busca primeiro por segmento. Se não encontrar, busca por 'geral'.
    """
    seg = segment.lower().strip()
    factor_seg = 1.0
    factor_gen = 1.0
    
    if monthly_table is None:
        monthly_table = []
        
    found_seg = False
    for item in monthly_table:
        if item.get("mes") == month:
            if item.get("segmento") == seg:
                factor_seg = item.get("fator", 1.0)
                found_seg = True
            elif item.get("segmento") == "geral":
                factor_gen = item.get("fator", 1.0)
    
    factor = factor_seg if found_seg else factor_gen
    
    # Auditoria de Segmento: Garante fator mínimo de 0.1 para 'SAPATO' (Passo 3.1)
    if seg == "sapato" and factor < 0.1:
        factor = 0.1
        
    return factor


def run_forecast_engine(
    df_sell: pd.DataFrame,
    df_hist: pd.DataFrame | None,
    calendar: dict,
    seasonality_table: dict,
    current_month: int = None,
    long_history_threshold: int = 6,
    regional_table: dict = None,
    analysis_regions: list[str] = None,
    lead_time_days: int = 60,
    reference_date: datetime = None,
    monthly_seasonality: list[dict] = None,
) -> pd.DataFrame:
    """
    Executa o motor de previsão para todas as combinações cliente x produto.

    Suporta:
      - Sazonalidade regional (média das regiões selecionadas)
      - Sazonalidade mensal (calendário brasileiro)
      - Estação futura baseada em lead time
    """
    if reference_date is None:
        reference_date = datetime.now()

    # Identificar Período de Destino
    future_season, future_month = get_future_season(calendar, lead_time_days, reference_date)

    # Identificar Mês Atual (Origem)
    current_month_num = current_month if current_month else reference_date.month

    # Cache de fatores mensais por segmento (Ponderado por Região)
    saz_ratio_cache = {} 
    
    segments = df_sell["segmento"].unique()
    for seg in segments:
        # Se regiões forem selecionadas, calculamos a média dos fatores para essas regiões
        if analysis_regions:
            factors_origem = []
            factors_destino = []
            for reg in analysis_regions:
                # Regra: Se a região não existir na tabela regional, usamos a tabela genérica de segmento
                f_o = get_regional_seasonality_factor(seg, reg, get_season(current_month_num, calendar), regional_table, seasonality_table)
                f_d = get_regional_seasonality_factor(seg, reg, future_season, regional_table, seasonality_table)
                factors_origem.append(f_o)
                factors_destino.append(f_d)
            
            avg_origem = np.mean(factors_origem) if factors_origem else 1.0
            avg_destino = np.mean(factors_destino) if factors_destino else 1.0
        else:
            # Fallback global (sem filtro de região)
            avg_origem = get_monthly_seasonality_factor(current_month_num, seg, monthly_seasonality)
            avg_destino = get_monthly_seasonality_factor(future_month, seg, monthly_seasonality)
        
        # AjusteEstacao
        ajuste_estacao = avg_destino / avg_origem if avg_origem > 0 else 1.0
        saz_ratio_cache[seg] = ajuste_estacao

    results = []
    for _, row in df_sell.iterrows():
        cliente = row["cliente"]
        produto = row["produto"]
        segmento = row.get("segmento", "")
        venda_atual = row.get("venda", 0)

        # Passo 1: Definir Venda Base
        venda_base = venda_atual 
        
        if df_hist is not None and not df_hist.empty:
            hist_cp = df_hist[
                (df_hist["cliente"] == cliente) & (df_hist["produto"] == produto)
            ]
            if len(hist_cp) > 0:
                h = hist_cp.sort_values("mes").copy()
                vendas_hist = h["venda"].values
                n_hist = len(vendas_hist)
                window = min(3, n_hist)
                if window > 0:
                    venda_base = float(np.mean(vendas_hist[-window:]))
                else:
                    venda_base = venda_atual

        # Passo 3: Ajuste de Estação (Ponderado Regionalmente)
        ajuste_estacao = saz_ratio_cache.get(segmento, 1.0)

        # Passo 5: Demanda Projetada
        demanda_base = venda_base * ajuste_estacao
        
        if 0 < demanda_base < 1:
            demanda_val = round(demanda_base, 1)
        else:
            demanda_val = round(demanda_base, 2)

        results.append({
            "media_vendas": round(venda_base, 2),
            "tendencia": round(ajuste_estacao, 4), 
            "fator_sazonalidade": ajuste_estacao,
            "demanda_prevista": max(0, demanda_val),
        })

    fc_df = pd.DataFrame(results)
    result = pd.concat([df_sell.reset_index(drop=True), fc_df], axis=1)

    # Adicionar colunas de contexto
    result["regiao_analisada"] = ", ".join(analysis_regions) if analysis_regions else "Brasil"
    result["estacao_futura"] = future_season
    result["mes_projecao"] = future_month

    return result
