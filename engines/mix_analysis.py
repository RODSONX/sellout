"""
Motor de Análise de Mix e Preço.
- Participação por segmento, gênero, público, linha
- Faixas de preço
- Ticket médio
- Comparação com mix ideal
"""
import pandas as pd
import numpy as np


def calculate_mix(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """
    Calcula participação de vendas por uma dimensão.
    Retorna DataFrame com colunas: [dimensão, venda, pct_venda].
    """
    if dimension not in df.columns:
        return pd.DataFrame()

    mix = df.groupby(dimension).agg(
        venda=("venda", "sum"),
        estoque=("estoque", "sum"),
        faturamento=("faturamento_estimado", "sum") if "faturamento_estimado" in df.columns else ("venda", "sum"),
    ).reset_index()

    total = mix["venda"].sum()
    mix["pct_venda"] = (mix["venda"] / total * 100).round(2) if total > 0 else 0

    return mix.sort_values("pct_venda", ascending=False)


def calculate_price_ranges(df: pd.DataFrame, price_ranges: dict) -> pd.DataFrame:
    """
    Classifica produtos em faixas de preço e calcula participação.
    """
    def classify(price):
        for name, bounds in price_ranges.items():
            if bounds["min"] <= price <= bounds["max"]:
                return name
        return "sem_faixa"

    result = df.copy()
    result["faixa_preco"] = result["preco_pdv"].apply(classify)

    mix = result.groupby("faixa_preco").agg(
        venda=("venda", "sum"),
        qtd_produtos=("produto", "nunique"),
    ).reset_index()

    total = mix["venda"].sum()
    mix["pct_venda"] = (mix["venda"] / total * 100).round(2) if total > 0 else 0

    return mix


def calculate_ticket_medio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula ticket médio por cliente.
    ticket_medio = faturamento_total / pares_vendidos
    """
    fat_col = "faturamento_estimado" if "faturamento_estimado" in df.columns else None
    if fat_col is None:
        df = df.copy()
        df["faturamento_estimado"] = df["venda"] * df["preco_pdv"]
        fat_col = "faturamento_estimado"

    ticket = df.groupby("cliente").agg(
        faturamento_total=(fat_col, "sum"),
        pares_vendidos=("venda", "sum"),
    ).reset_index()

    ticket["ticket_medio"] = np.where(
        ticket["pares_vendidos"] > 0,
        (ticket["faturamento_total"] / ticket["pares_vendidos"]).round(2),
        0
    )
    return ticket


def compare_with_ideal(actual_mix: pd.DataFrame, ideal_mix: dict, dimension: str) -> pd.DataFrame:
    """
    Compara mix real com mix ideal.
    Retorna DataFrame com colunas: [dimensão, pct_real, pct_ideal, gap].
    """
    comparison = []
    all_keys = set(list(ideal_mix.keys()) + list(actual_mix[dimension].values))

    actual_dict = dict(zip(actual_mix[dimension], actual_mix["pct_venda"]))

    for key in sorted(all_keys):
        pct_real = actual_dict.get(key, 0)
        pct_ideal = ideal_mix.get(key, 0) * 100
        comparison.append({
            dimension: key,
            "pct_real": round(pct_real, 2),
            "pct_ideal": round(pct_ideal, 2),
            "gap": round(pct_real - pct_ideal, 2),
        })

    return pd.DataFrame(comparison)
