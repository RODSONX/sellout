"""
Motor de Alertas Automáticos.
- Ruptura de estoque
- Excesso de estoque
- Sem compra recente
- Campeão não vendido
- Mix abaixo do ideal
- Reposição atrasada (NEW: baseado em frequência + lead time)
"""
import pandas as pd
import numpy as np
from datetime import datetime


def generate_alerts(
    df_inventory: pd.DataFrame,
    df_campeoes: pd.DataFrame | None,
    df_recebimento: pd.DataFrame | None,
    mix_comparison: dict | None,
    coverage_rupture: float = 0.5,
    coverage_excess: float = 4.0,
    days_threshold: int = 120,
    reference_date: datetime | None = None,
    lead_time_days: int = 60,
    **kwargs
) -> pd.DataFrame:
    """
    Gera todos os alertas automáticos.
    Retorna DataFrame com colunas: tipo, severidade, cliente, produto, detalhe
    """
    if reference_date is None:
        reference_date = datetime.now()

    alerts = []

    # ─── 1. Ruptura de Estoque ───
    rupturas = df_inventory[
        (df_inventory["estoque"] <= 0) | (df_inventory["cobertura_meses"] < coverage_rupture)
    ]
    for _, r in rupturas.iterrows():
        alerts.append({
            "tipo": "🔴 Ruptura de Estoque",
            "severidade": "alta",
            "cliente": r["cliente"],
            "produto": r["produto"],
            "segmento": r.get("segmento", ""),
            "detalhe": f"Estoque: {r['estoque']:.0f} | Cobertura: {r['cobertura_meses']:.1f} meses",
        })

    # ─── 2. Excesso de Estoque ───
    excesso = df_inventory[df_inventory["cobertura_meses"] > coverage_excess]
    for _, r in excesso.iterrows():
        alerts.append({
            "tipo": "🟡 Excesso de Estoque",
            "severidade": "média",
            "cliente": r["cliente"],
            "produto": r["produto"],
            "segmento": r.get("segmento", ""),
            "detalhe": f"Estoque: {r['estoque']:.0f} | Cobertura: {r['cobertura_meses']:.1f} meses",
        })

    # ─── 3. Sem Recebimento Recente (Mix Atual + Janela Dinâmica) ───
    receipt_window_months = kwargs.get("receipt_window_months", 4)
    if df_recebimento is not None and not df_recebimento.empty:
        df_rp = df_recebimento.copy()
        df_rp["data_entrega"] = pd.to_datetime(df_rp["data_entrega"], errors="coerce")
        # Pegar apenas recebimentos passados (não futuros) para saber quando foi o ÚLTIMO
        df_past = df_rp[df_rp["data_entrega"] < reference_date].copy()
        
        # 1. Preparar chaves rigorosas (String + Trim)
        # Mapeamento implícito: 'Produto - Codigo Referencia' (Sell-out) e 'Cod. Referencia' (Recebimentos)
        # Ambos já foram normalizados para 'produto' no ETL.
        df_inv_clean = df_inventory.copy()
        df_inv_clean["produto"] = df_inv_clean["produto"].astype(str).str.strip()
        
        df_last_receipt = df_past.groupby(["cliente", "produto"])["data_entrega"].max().reset_index()
        df_last_receipt["produto"] = df_last_receipt["produto"].astype(str).str.strip()
        
        # 2. Base Principal (Left Join): Sell-out (df_inventory) como base principal
        # Traz a data do último recebimento apenas quando houver correspondência
        sem_receber_base = df_inv_clean[[
            "cliente", "produto", "estoque", "venda", "segmento", 
            "linha", "modelo", "genero", "publico", "descricao_produto"
        ]].merge(
            df_last_receipt, 
            on=["cliente", "produto"], 
            how="left"
        )
        
        # 3. Filtro Final de Tempo (Apenas itens com data de recebimento antiga)
        # Se data_entrega for NaN (sem match), o item não entra no alerta de 'atraso' cronológico
        threshold_date = reference_date - pd.DateOffset(months=receipt_window_months)
        sem_receber = sem_receber_base[
            (sem_receber_base["data_entrega"].notna()) & 
            (sem_receber_base["data_entrega"] < threshold_date)
        ]
        
        for _, r in sem_receber.iterrows():
            dias = (reference_date - r["data_entrega"]).days
            alerts.append({
                "tipo": "🟠 Sem Recebimento Recente",
                "severidade": "média",
                "cliente": r["cliente"],
                "produto": r["produto"],
                "produto_desc": f"{r['produto']} - {r.get('descricao_produto', '')}",
                "segmento": r.get("segmento", ""),
                "linha": r.get("linha", ""),
                "modelo": r.get("modelo", ""),
                "genero": r.get("genero", ""),
                "publico": r.get("publico", ""),
                "venda_recente": int(r["venda"]),
                "estoque_atual": int(r["estoque"]),
                "data_ultimo": r["data_entrega"].strftime("%y-%m-%d"),
                "data_ultimo_mes_ano": r["data_entrega"].strftime("%m/%Y"),
                "detalhe": f"Último em {r['data_entrega'].strftime('%d/%m/%Y')} ({dias} dias) | Estoque: {int(r['estoque'])}",
            })

    # ─── 4. Campeão Não Vendido ───
    if df_campeoes is not None and not df_campeoes.empty:
        champion_products = set(df_campeoes["produto"].unique())
        for cliente in df_inventory["cliente"].unique():
            client_products = set(
                df_inventory[df_inventory["cliente"] == cliente]["produto"].unique()
            )
            missing = champion_products - client_products
            for prod in missing:
                camp_row = df_campeoes[df_campeoes["produto"] == prod].iloc[0]
                alerts.append({
                    "tipo": "🔵 Campeão Não Vendido",
                    "severidade": "média",
                    "cliente": cliente,
                    "produto": prod,
                    "segmento": camp_row.get("segmento", ""),
                    "detalhe": f"Rank nacional: {camp_row.get('quantidade_vendida', 0):.0f} un.",
                })

    # ─── 5. Mix Abaixo do Ideal ───
    if mix_comparison:
        for dim, comp_df in mix_comparison.items():
            if comp_df is not None and not comp_df.empty:
                below = comp_df[comp_df["gap"] < -5]  # gap negativo > 5 pp
                for _, r in below.iterrows():
                    alerts.append({
                        "tipo": "🟣 Mix Abaixo do Ideal",
                        "severidade": "baixa",
                        "cliente": "Geral",
                        "produto": r[dim],
                        "segmento": dim,
                        "detalhe": f"Real: {r['pct_real']:.1f}% | Ideal: {r['pct_ideal']:.1f}% | Gap: {r['gap']:.1f}pp",
                    })

    # ─── 6. Reposição Atrasada (considerando frequência + lead time) ───
    if df_recebimento is not None and not df_recebimento.empty:
        df_rp2 = df_recebimento.copy()
        df_rp2["data_entrega"] = pd.to_datetime(df_rp2["data_entrega"], errors="coerce")

        # Calcular data_pedido_real = data_entrega - lead_time
        df_rp2["data_pedido_real"] = df_rp2["data_entrega"] - pd.Timedelta(days=lead_time_days)

        # Calcular frequência média de compra por cliente
        freq_by_client = (
            df_rp2.groupby("cliente")["data_pedido_real"]
            .apply(lambda x: x.sort_values().diff().dt.days.mean())
            .reset_index()
        )
        freq_by_client.columns = ["cliente", "freq_media_dias"]
        freq_by_client["freq_media_dias"] = freq_by_client["freq_media_dias"].fillna(90)

        # Ultimo recebimento mais recente por cliente
        last_receipt = (
            df_rp2[df_rp2["data_entrega"] <= reference_date].groupby("cliente")["data_entrega"]
            .max()
            .reset_index()
        )
        last_receipt.columns = ["cliente", "ultimo_recebimento_recente"]

        reposicao = freq_by_client.merge(last_receipt, on="cliente", how="left")
        reposicao["dias_desde_ultimo"] = (reference_date - reposicao["ultimo_recebimento_recente"]).dt.days
        reposicao["limiar_atraso"] = reposicao["freq_media_dias"] + lead_time_days

        atrasados = reposicao[reposicao["dias_desde_ultimo"] > reposicao["limiar_atraso"]]

        for _, r in atrasados.iterrows():
            alerts.append({
                "tipo": "⏰ Reposição Atrasada",
                "severidade": "alta",
                "cliente": r["cliente"],
                "produto": "—",
                "segmento": "—",
                "detalhe": (
                    f"{r['dias_desde_ultimo']:.0f} dias desde último pedido | "
                    f"Freq. média: {r['freq_media_dias']:.0f}d + Lead time: {lead_time_days}d = "
                    f"Limiar: {r['limiar_atraso']:.0f}d"
                ),
            })

    result = pd.DataFrame(alerts)
    if not result.empty:
        severity_order = {"alta": 0, "média": 1, "baixa": 2}
        result["_sev_order"] = result["severidade"].map(severity_order)
        result = result.sort_values("_sev_order").drop(columns="_sev_order")

    return result
