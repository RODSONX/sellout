"""
Motor de Planejamento de Estoque.
- Estoque futuro (com data_chegada via lead time)
- Cobertura
- Estoque de segurança
- Venda durante lead time
- Estoque ideal (inclui venda durante lead time)
- Sugestão de reposição
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def calculate_inventory(
    df_forecast: pd.DataFrame,
    df_pedidos: pd.DataFrame | None,
    safety_days: int = 15,
    lead_time_days: int = 60,
    reference_date: datetime = None,
    retail_events: list[dict] = None,
    monthly_capacity: int = 1000,
) -> pd.DataFrame:
    """
    Recebe DataFrame com previsão e calcula métricas de estoque seguindo o modelo v1.12.
    """
    if reference_date is None:
        reference_date = datetime.now()

    if retail_events is None:
        retail_events = []

    df = df_forecast.copy()

    # Pedidos em carteira por cliente x produto
    if df_pedidos is not None and not df_pedidos.empty:
        ped = df_pedidos.copy()
        ped["data_faturamento"] = pd.to_datetime(ped["data_faturamento"], errors="coerce")
        ped["data_chegada"] = ped["data_faturamento"] + timedelta(days=lead_time_days)

        cart = ped.groupby(["cliente", "produto"]).agg(
            pedidos_carteira=("quantidade", "sum"),
        ).reset_index()

        df = df.merge(cart, on=["cliente", "produto"], how="left")
    else:
        df["pedidos_carteira"] = 0

    df["pedidos_carteira"] = df["pedidos_carteira"].fillna(0)

    # Passo 4: Ajuste de Evento (FE)
    df["fator_evento"] = 1.0
    df["evento_nome"] = ""
    
    for event in retail_events:
        mes_ev = event.get("mes")
        fator_ev = event.get("fator_evento", 1.0)
        cat_foco = event.get("categoria_foco", "geral").lower()
        nome_ev = event.get("evento", "")
        
        mask_month = df["mes_projecao"] == mes_ev
        if cat_foco == "geral":
            mask_cat = pd.Series([True] * len(df), index=df.index)
        else:
            mask_cat = df["genero"].str.lower().str.strip() == cat_foco
            
        combined_mask = mask_month & mask_cat
        if combined_mask.any():
            df.loc[combined_mask, "fator_evento"] = fator_ev
            df.loc[combined_mask, "evento_nome"] = nome_ev

    # Passo 5: Demanda Projetada (Integral - 30 Dias)
    # Sempre exibe o valor da venda mensal cheia (30 dias)
    demanda_full = df["demanda_prevista"] * df["fator_evento"]
    
    # Fim do Arredondamento para Zero (v1.13)
    df["demanda_projetada"] = np.where(
        (demanda_full > 0) & (demanda_full < 1),
        demanda_full.round(1),
        demanda_full.round(2)
    )

    # Passo 6/7/8: Demanda Durante o Lead Time + Estoque de Segurança
    df["venda_durante_leadtime"] = ( (df["demanda_projetada"] / 30.0) * (lead_time_days + safety_days) ).round(0)

    # Passo 9: Cálculo do Pedido Sugerido
    df["pedido_calculado"] = (
        df["venda_durante_leadtime"] - df["estoque"] - df["pedidos_carteira"]
    ).clip(lower=0).round(0)

    # Passo 10: Limitar por Capacidade da Loja
    df["pedido_sugerido"] = df["pedido_calculado"].clip(upper=monthly_capacity)

    # REGRAS ESTRATÉGICAS (v5.0)
    # Se status_estrategico for 'Fora de Linha' (Vermelho) ou 'Retirar' (Roxo), zerar pedido
    if "status_estrategico" in df.columns:
        # Mapeamento para garantir consistência
        zera_mask = df["status_estrategico"].isin(["Fora de Linha", "Retirar"])
        df.loc[zera_mask, "pedido_sugerido"] = 0
        df.loc[zera_mask, "pedido_calculado"] = 0

    # Métricas Adicionais
    df["estoque_seguranca"] = ( (df["demanda_projetada"] / 30.0) * safety_days ).round(0)
    df["estoque_ideal"] = df["venda_durante_leadtime"]
    
    # Garantir tipos numéricos para faturamento (evita TypeError no round)
    venda_num = pd.to_numeric(df["venda"], errors="coerce").fillna(0)
    preco_num = pd.to_numeric(df["preco_pdv"], errors="coerce").fillna(0)
    df["faturamento_estimado"] = (venda_num * preco_num).round(2)
    
    df["lead_time_dias"] = lead_time_days

    # Cobertura de Estoque Atual (Tratamento de Cobertura Infinita v1.13)
    # Se demanda == 0 e estoque > 0 -> exibe 12.0 (Sem Giro)
    df["cobertura_meses"] = np.where(
        df["demanda_projetada"] > 0,
        (df["estoque"] / df["demanda_projetada"]).round(2),
        np.where(df["estoque"] > 0, 12.0, 0.0)
    )

    return df
