"""
Motor de Detecção de Oportunidades.
- Tipo 1: Produto campeão não vendido pelo cliente
- Tipo 2: Produto vendido abaixo da média do segmento
- Tipo 3: Produto sem compra recente (>N dias)
"""
import pandas as pd
from datetime import datetime, timedelta


def detect_champion_not_sold(
    df_sell: pd.DataFrame,
    df_campeoes: pd.DataFrame,
) -> pd.DataFrame:
    """
    TIPO 1: Produtos campeões que o cliente não vende.
    """
    if df_campeoes is None or df_campeoes.empty:
        return pd.DataFrame()

    champion_products = set(df_campeoes["produto"].unique())
    results = []

    for cliente in df_sell["cliente"].unique():
        client_products = set(
            df_sell[df_sell["cliente"] == cliente]["produto"].unique()
        )
        missing = champion_products - client_products

        for prod in missing:
            camp_row = df_campeoes[df_campeoes["produto"] == prod].iloc[0]
            results.append({
                "cliente": cliente,
                "produto": prod,
                "tipo_oportunidade": "Campeão não vendido",
                "segmento": camp_row.get("segmento", ""),
                "genero": camp_row.get("genero", ""),
                "publico": camp_row.get("publico", ""),
                "quantidade_vendida_nacional": camp_row.get("quantidade_vendida", 0),
            })

    return pd.DataFrame(results)


def detect_below_segment_avg(df_sell: pd.DataFrame) -> pd.DataFrame:
    """
    TIPO 2: Produtos vendidos abaixo da média do segmento.
    """
    seg_avg = df_sell.groupby("segmento")["venda"].mean().reset_index()
    seg_avg.rename(columns={"venda": "media_segmento"}, inplace=True)

    merged = df_sell.merge(seg_avg, on="segmento", how="left")
    below = merged[merged["venda"] < merged["media_segmento"]].copy()

    below["tipo_oportunidade"] = "Abaixo da média"
    below["gap_venda"] = (below["media_segmento"] - below["venda"]).round(0)

    return below[["cliente", "produto", "segmento", "venda", "media_segmento",
                   "gap_venda", "tipo_oportunidade"]].copy()


def detect_no_recent_delivery(
    df_recebimento: pd.DataFrame,
    df_inventory: pd.DataFrame,
    days_threshold: int = 120,
    receipt_window_months: int = 4,
    reference_date: datetime = None,
) -> pd.DataFrame:
    """
    TIPO 3: Produtos sem recebimento recente.
    Refatorado: Cruza com df_inventory para garantir que apenas o Mix Atual seja exibido
    e traz metadados (venda, estoque, segmento, etc).
    """
    if df_recebimento is None or df_recebimento.empty or df_inventory is None or df_inventory.empty:
        return pd.DataFrame()

    if reference_date is None:
        reference_date = datetime.now()
        
    # Converter janela de meses para dias (aproximado)
    actual_days_threshold = receipt_window_months * 30

    # 1. Preparar base de entregas passadas
    df_rp = df_recebimento.copy()
    
    # Mapeamento de chaves rigoroso
    rename_keys = {"Cod. Referencia": "produto", "Produto - Codigo Referencia": "produto", "Referencia": "produto"}
    for old, new in rename_keys.items():
        if old in df_rp.columns and new not in df_rp.columns:
            df_rp = df_rp.rename(columns={old: new})

    df_rp["data_entrega"] = pd.to_datetime(df_rp["data_entrega"], errors="coerce")
    df_past = df_rp[df_rp["data_entrega"] < reference_date].copy()
    
    # Calcular última data por cliente/produto
    df_last_receipt = df_past.groupby(["cliente", "produto"])["data_entrega"].max().reset_index()
    df_last_receipt["produto"] = df_last_receipt["produto"].astype(str).str.strip().str.upper()
    df_last_receipt = df_last_receipt.rename(columns={"data_entrega": "data_ultimo_recebimento"})
    
    # 2. Base Principal: Sell-out (df_inventory)
    # Regra Rigorosa: Apenas produtos com Venda > 0 OU Estoque > 0
    df_inv_clean = df_inventory[
        (df_inventory["venda"] > 0) | (df_inventory["estoque"] > 0)
    ].copy()
    df_inv_clean["produto"] = df_inv_clean["produto"].astype(str).str.strip().str.upper()
    
    # TRATAMENTO PARA CLIENTE 'Global'
    # Se houver registros 'Global', eles devem servir como fallback para todos os clientes
    if not df_last_receipt.empty and (df_last_receipt["cliente"] == "Global").any():
        df_global = df_last_receipt[df_last_receipt["cliente"] == "Global"].drop(columns=["cliente"])
        # Merge individual
        merged = df_inv_clean.merge(df_last_receipt, on=["cliente", "produto"], how="left")
        # Preencher NaNs com o Global
        merged = merged.merge(df_global, on="produto", how="left", suffixes=("", "_global"))
        merged["data_ultimo_recebimento"] = merged["data_ultimo_recebimento"].fillna(merged["data_ultimo_recebimento_global"])
        merged = merged.drop(columns=["data_ultimo_recebimento_global"])
    else:
        merged = df_inv_clean.merge(df_last_receipt, on=["cliente", "produto"], how="left")
    
    # 3. Filtro de Tempo e Inclusividade (NaN)
    # Itens com recebimento antigo OU sem nenhum registro de recebimento (são críticos)
    merged["dias_sem_receber"] = (reference_date - merged["data_ultimo_recebimento"]).dt.days
    
    # Regra: data_ultimo_recebimento < threshold OU data_ultimo_recebimento is NaN
    # NaN significa: Está no mix (sell-out), mas não temos registro de chegada (pode ser um item "esquecido" real)
    alerts = merged[
        (merged["data_ultimo_recebimento"].isna()) | 
        (merged["dias_sem_receber"] >= actual_days_threshold)
    ].copy()
    
    alerts["tipo_oportunidade"] = "Sem recebimento recente"

    # Retorno rico para a UI
    return alerts[[
        "cliente", "produto", "segmento", "genero", "publico", "venda", "estoque",
        "data_ultimo_recebimento", "dias_sem_receber", "tipo_oportunidade"
    ]].copy()


def detect_seasonal_opportunities(
    df_inventory: pd.DataFrame,
    retail_events: list[dict] = None,
    df_recebimento: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    TIPO 4: Oportunidades por Estação e Eventos.
    NOVO: Considera Estoque + Entregas ANTERIORES ao evento.
    """
    if df_inventory is None or df_inventory.empty:
        return pd.DataFrame()

    if retail_events is None:
        retail_events = []

    results = []
    
    # 1. Verificação de Estação (Lógica Cumulativa para Entrega no Inverno)
    # Reusar df_inventory que já tem demanda projetada
    
    # 2. Verificação de Eventos de Varejo
    for event in retail_events:
        mes_ev = event.get("mes")
        ano_ev = datetime.now().year if datetime.now().month <= mes_ev else datetime.now().year + 1
        data_evento = datetime(ano_ev, mes_ev, 1)
        
        nome_ev = event.get("evento", "")
        cat_foco = event.get("categoria_foco", "geral").lower()
        
        # Filtrar o que está programado para chegar ANTES do evento
        # (Somamos o que chegará até o mês anterior ou no próprio mês do evento?)
        # User diz: "anterior a essa data sazonal"
        
        for cliente in df_inventory["cliente"].unique():
            df_cli_inv = df_inventory[df_inventory["cliente"] == cliente]
            
            # Pegar entregas programadas desse cliente/produto
            if df_recebimento is not None and not df_recebimento.empty:
                df_cli_rp = df_recebimento[df_recebimento["cliente"] == cliente].copy()
                df_cli_rp["data_entrega"] = pd.to_datetime(df_cli_rp["data_entrega"])
            else:
                df_cli_rp = pd.DataFrame()

            # Analisar produtos da categoria foco
            if cat_foco != "geral":
                df_foco = df_cli_inv[df_cli_inv["genero"].str.lower().str.strip() == cat_foco]
                
                for _, row in df_foco.iterrows():
                    # Estoque atual + Entregas < data_evento
                    entregas_antes = 0
                    if not df_cli_rp.empty:
                        prod_rp = df_cli_rp[
                            (df_cli_rp["produto"] == row["produto"]) & 
                            (df_cli_rp["data_entrega"] < data_evento)
                        ]
                        entregas_antes = prod_rp["quantidade"].sum()
                    
                    estoque_disponivel = row["estoque"] + entregas_antes
                    
                    # Se cobertura (estoque / demanda) < 1.0 para o evento
                    if estoque_disponivel < row["venda"]: # venda aqui representa giro mensal
                        results.append({
                            "cliente": cliente,
                            "produto": row["produto"],
                            "tipo_oportunidade": f"Evento: {nome_ev}",
                            "detalhe": f"Estoque + Recebimentos ({estoque_disponivel:.0f}) não cobrem demanda p/ {nome_ev}.",
                            "segmento": row["segmento"],
                            "cobertura_meses": estoque_disponivel / row["venda"] if row["venda"] > 0 else 0
                        })

    return pd.DataFrame(results)


def run_opportunity_engine(
    df_sell: pd.DataFrame,
    df_campeoes: pd.DataFrame | None,
    df_recebimento: pd.DataFrame | None,
    df_inventory: pd.DataFrame | None = None,
    retail_events: list[dict] = None,
    days_threshold: int = 120,
    receipt_window_months: int = 4,
    reference_date: datetime = None,
) -> dict[str, pd.DataFrame]:
    """
    Executa todas as detecções de oportunidade.
    Retorna dict com DataFrames.
    """
    return {
        "campeoes_nao_vendidos": detect_champion_not_sold(df_sell, df_campeoes),
        "abaixo_media": detect_below_segment_avg(df_sell),
        "sem_recebimento_recente": detect_no_recent_delivery(
            df_recebimento, df_inventory, days_threshold, receipt_window_months, reference_date
        ),
        "sazonais": detect_seasonal_opportunities(df_inventory, retail_events, df_recebimento),
    }
