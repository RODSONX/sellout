"""
Motor de Substituição de Produtos.
Quando produto em ruptura (estoque=0 ou cobertura<0.5),
sugere substitutos com critérios de: segmento, linha, público, gênero, faixa de preço.
"""
import pandas as pd


def find_substitutes(
    product_row: pd.Series,
    df_sell: pd.DataFrame,
    df_campeoes: pd.DataFrame | None,
    price_min_pct: float = 0.80,
    price_max_pct: float = 1.20,
    top_n: int = 3,
) -> pd.DataFrame:
    """
    Busca até top_n substitutos para um produto em ruptura.
    """
    preco = product_row.get("preco_pdv", 0)
    segmento = product_row.get("segmento", "")
    linha = product_row.get("linha", "")
    publico = product_row.get("publico", "")
    genero = product_row.get("genero", "")
    produto = product_row.get("produto", "")

    preco_min = preco * price_min_pct
    preco_max = preco * price_max_pct

    # Buscar no sell-out geral (todos os clientes)
    candidates = df_sell[
        (df_sell["produto"] != produto)
        & (df_sell["segmento"] == segmento)
        & (df_sell["linha"] == linha)
        & (df_sell["publico"] == publico)
        & (df_sell["genero"] == genero)
        & (df_sell["preco_pdv"] >= preco_min)
        & (df_sell["preco_pdv"] <= preco_max)
        & (df_sell["estoque"] > 0)
    ].copy()

    if candidates.empty:
        # Relaxar: remover filtro de linha
        candidates = df_sell[
            (df_sell["produto"] != produto)
            & (df_sell["segmento"] == segmento)
            & (df_sell["publico"] == publico)
            & (df_sell["genero"] == genero)
            & (df_sell["preco_pdv"] >= preco_min)
            & (df_sell["preco_pdv"] <= preco_max)
            & (df_sell["estoque"] > 0)
        ].copy()

    if candidates.empty:
        return pd.DataFrame()

    # Remover duplicatas de produto
    candidates = candidates.drop_duplicates(subset=["produto"])

    # Ordenar por ranking de campeões se disponível
    if df_campeoes is not None and not df_campeoes.empty:
        camp_dict = dict(zip(df_campeoes["produto"], df_campeoes["quantidade_vendida"]))
        candidates["rank_campeao"] = candidates["produto"].map(camp_dict).fillna(0)
        candidates = candidates.sort_values("rank_campeao", ascending=False)
    else:
        candidates = candidates.sort_values("venda", ascending=False)

    top = candidates.head(top_n)

    return top[["produto", "segmento", "linha", "genero", "publico",
                "preco_pdv", "venda", "estoque"]].copy()


def run_substitution_engine(
    df_inventory: pd.DataFrame,
    df_sell: pd.DataFrame,
    df_campeoes: pd.DataFrame | None,
    coverage_threshold: float = 0.5,
    price_min_pct: float = 0.80,
    price_max_pct: float = 1.20,
    top_n: int = 3,
) -> pd.DataFrame:
    """
    Identifica produtos em ruptura e sugere substitutos.

    Retorna DataFrame com:
      produto_original, cliente, motivo, substituto_1, substituto_2, substituto_3
    """
    # Filtrar rupturas
    rupturas = df_inventory[
        (df_inventory["estoque"] <= 0) | (df_inventory["cobertura_meses"] < coverage_threshold)
    ].copy()

    if rupturas.empty:
        return pd.DataFrame()

    results = []
    for _, row in rupturas.iterrows():
        motivo = "Estoque zero" if row["estoque"] <= 0 else f"Cobertura baixa ({row['cobertura_meses']:.1f} meses)"

        subs = find_substitutes(
            row, df_sell, df_campeoes, price_min_pct, price_max_pct, top_n
        )

        entry = {
            "cliente": row["cliente"],
            "produto_original": row["produto"],
            "segmento": row["segmento"],
            "preco_original": row["preco_pdv"],
            "estoque": row["estoque"],
            "cobertura": row.get("cobertura_meses", 0),
            "motivo": motivo,
        }

        for i in range(top_n):
            if i < len(subs):
                s = subs.iloc[i]
                entry[f"substituto_{i+1}"] = s["produto"]
                entry[f"preco_sub_{i+1}"] = s["preco_pdv"]
            else:
                entry[f"substituto_{i+1}"] = ""
                entry[f"preco_sub_{i+1}"] = 0

        results.append(entry)

    return pd.DataFrame(results)
