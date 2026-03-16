"""
Módulo de carregamento e validação de dados.
Inclui gerador de dados de exemplo para demonstração.
"""
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
import random

# ───────── Esquemas esperados por aba ─────────
SCHEMAS = {
    "sell_out": {
        "columns": [
            "DESCR. REDE", "Ano", "Mes", "DATA", "Qtde Venda", "Qtde Estoque",
            "Produto - Codigo Referencia", "Produto - Descrição", "Produto - Modelo",
            "Produto - Segmento", "Produto - Publico", "Produto - Genero", "Produto - Linha"
        ],
        "mapping": {
            "DESCR. REDE": "cliente",
            "Ano": "ano_venda",
            "Mes": "mes_venda",
            "DATA": "data_venda",
            "Qtde Venda": "venda",
            "Qtde Estoque": "estoque",
            "Produto - Codigo Referencia": "produto",
            "Produto - Descrição": "descricao_produto",
            "Produto - Modelo": "modelo",
            "Produto - Segmento": "segmento",
            "Produto - Publico": "publico",
            "Produto - Genero": "genero",
            "Produto - Linha": "linha",
        },
        "mandatory": ["Produto - Codigo Referencia", "DESCR. REDE"],
        "optional": ["Ano", "Mes", "DATA", "status", "classificacao"],
        "numeric": ["Qtde Venda", "Qtde Estoque", "Ano", "Mes"],
    },
    "pedidos": {
        "columns": ["cliente", "produto", "quantidade", "segmento", "linha", "genero", "publico", "data_faturamento"],
        "numeric": ["quantidade"],
        "dates": ["data_faturamento"],
    },
    "campeoes": {
        "columns": ["referencia", "qt", "publico", "genero", "segmento", "linha"],
        "mapping": {
            "referencia": "produto",
            "qt": "quantidade_vendida",
            "publico": "publico",
            "genero": "genero",
            "segmento": "segmento",
            "linha": "linha",
        },
        "mandatory": ["referencia", "qt"],
        "numeric": ["qt"],
    },
    "recebimento_programado": {
        "columns": ["cliente", "produto", "data_entrega", "segmento", "genero", "publico"],
        "mapping": {
            "DESCR. REDE": "cliente",
            "Cliente": "cliente",
            "Produto - Codigo Referencia": "produto",
            "Produto": "produto",
            "Referencia": "produto",
            "Cod. Referencia": "produto",
            "Data Entrega": "data_entrega",
        },
        "optional": ["segmento", "genero", "publico", "quantidade", "data_entrega"],
        "mandatory": ["cliente", "produto"],
        "dates": ["data_entrega"],
    },
    "historico": {
        "columns": ["cliente", "produto", "mes", "venda"],
        "numeric": ["venda"],
    },
}


def _parse_month(val):
    if pd.isna(val) or val == "":
        return 0
    s = str(val).lower().strip()
    months_map = {
        "jan": 1, "janeiro": 1, "fev": 2, "fevereiro": 2, "mar": 3, "março": 3, "abr": 4, "abril": 4,
        "mai": 5, "maio": 5, "jun": 6, "junho": 6, "jul": 7, "julho": 7, "ago": 8, "agosto": 8,
        "set": 9, "setembro": 9, "out": 10, "outubro": 10, "nov": 11, "novembro": 11, "dez": 12, "dezembro": 12
    }
    if s in months_map:
        return months_map[s]
    try:
        # Tentar converter direto se for número em string "02"
        return int(float(s))
    except:
        return 0


def validate_dataframe(df: pd.DataFrame, schema_name: str) -> tuple[bool, list[str]]:
    """Valida um DataFrame contra o esquema esperado."""
    schema = SCHEMAS[schema_name]
    errors = []
    
    # Verificar colunas obrigatórias
    mapping = schema.get("mapping", {})
    optional = schema.get("optional", [])
    expected_cols = [c for c in (list(mapping.keys()) if mapping else schema["columns"]) if c not in optional]
    
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        errors.append(f"Colunas ausentes: {', '.join(missing)}")
        return False, errors

    # Validação de dados mandatórios (linhas vazias)
    for col in schema.get("mandatory", []):
        if df[col].isnull().any() or (df[col] == "").any():
            errors.append(f"A coluna '{col}' possui valores vazios.")

    return len(errors) == 0, errors


def parse_upload(uploaded_file, schema_name: str) -> tuple[pd.DataFrame | None, list[str]]:
    """Lê arquivo CSV ou Excel e valida contra o esquema."""
    try:
        name = uploaded_file.name.lower()
        if name.endswith(".csv"):
            df_raw = pd.read_csv(uploaded_file, sep=None, engine="python", header=None)
        elif name.endswith((".xlsx", ".xls")):
            df_raw = pd.read_excel(uploaded_file, header=None)
        else:
            return None, ["Formato não suportado. Use CSV ou Excel."]

        # ─── DETECÇÃO DE MATRIZ PERSONALIZADA (PERIODO DE ENTREGA) ───
        # Se A1 (0,0) contiver "Periodo Entrega" (ou variações)
        primeira_celula = str(df_raw.iloc[0, 0]).strip().upper() if len(df_raw) > 0 and len(df_raw.columns) > 0 else ""
        
        if schema_name == "recebimento_programado" and ("PERIODO ENTREGA" in primeira_celula or "PERÍODO ENTREGA" in primeira_celula):
            # Lógica de Matriz Estrita:
            # Linha 1 (index 0): Datas YYYY.MM a partir da Coluna B (index 1)
            # Linha 2 (index 1): Ignorar (Cod. Referencia)
            # Linha 3+ (index 2+): Produto na Coluna A (index 0), Quantidades nas Colunas B+
            
            headers_raw = df_raw.iloc[0, 1:]
            date_col_map = {} # {col_index: date_object}
            
            for i, val in enumerate(headers_raw):
                val_str = str(val).strip()
                # Tentar converter YYYY.MM -> 01/MM/YYYY
                try:
                    if "." in val_str:
                        y_str, m_str = val_str.split(".")
                        y, m = int(y_str), int(m_str)
                        dt = datetime(y, m, 1)
                        date_col_map[i+1] = dt
                except:
                    # Tentar conversão genérica se não for YYYY.MM
                    parsed = pd.to_datetime(val, errors="coerce", dayfirst=True)
                    if pd.notna(parsed):
                        date_col_map[i+1] = parsed
            
            if not date_col_map:
                return None, ["Formato de data 'YYYY.MM' não detectado na primeira linha."]
            
            # Dados de produtos (Linha 3 em diante -> index 2+)
            df_data = df_raw.iloc[2:].copy()
            rows_uc = []
            
            # Ordenar colunas da direita para a esquerda (mais recente primeiro)
            sorted_col_indices = sorted(date_col_map.keys(), key=lambda k: date_col_map[k], reverse=True)
            
            for _, row in df_data.iterrows():
                produto = str(row[0]).strip()
                if not produto or produto.lower() in ["nan", "cod. referencia"]:
                    continue
                
                for col_idx in sorted_col_indices:
                    qty = pd.to_numeric(row[col_idx], errors="coerce")
                    if pd.notna(qty) and qty > 0:
                        rows_uc.append({
                            "cliente": "Global",
                            "produto": produto,
                            "data_entrega": date_col_map[col_idx],
                            "quantidade": qty
                        })
            
            df_final = pd.DataFrame(rows_uc)
            if df_final.empty:
                return None, ["Nenhuma quantidade > 0 encontrada para os produtos."]
            return df_final, []

        # Se não for a matriz customizada, tratamos como planilha comum
        df = df_raw.copy()
        df.columns = [str(c).strip() for c in df.iloc[0]] # Usa a primeira linha como header
        df = df.iloc[1:].reset_index(drop=True)
        df.columns = [c.strip() for c in df.columns]

        # Conserto específico para meses em string no sell_out ANTES da validação numérica
        if schema_name == "sell_out" and "Mes" in df.columns:
            df["Mes"] = df["Mes"].apply(_parse_month)

        schema = SCHEMAS[schema_name]
        valid, errors = validate_dataframe(df, schema_name)
        if not valid:
            return None, errors

        # Conversão numérica com validação
        for col in schema.get("numeric", []):
            df[col] = pd.to_numeric(df[col], errors="coerce")
            if df[col].isnull().any():
                errors.append(f"A coluna '{col}' possui valores não numéricos.")
                df[col] = df[col].fillna(0)

        # Mapeamento de colunas se houver
        if "mapping" in schema:
            df = df.rename(columns=schema["mapping"])

        # Consolidação específica para Sell-Out
        if schema_name == "sell_out":
            group_cols = ["cliente", "produto", "ano_venda", "mes_venda"]
            for c in group_cols:
                if c not in df.columns:
                    df[c] = ""
            
            other_cols = [c for c in df.columns if c not in group_cols + ["venda", "estoque"]]
            agg_dict = {"venda": "sum", "estoque": "sum"}
            for c in other_cols:
                agg_dict[c] = "first"
                
            df = df.groupby(group_cols, as_index=False).agg(agg_dict)

        # Filtro Top 15 para Campeões de Venda
        if schema_name == "campeoes":
            if "segmento" in df.columns and "quantidade_vendida" in df.columns:
                df = df.sort_values("quantidade_vendida", ascending=False)
                df = df.groupby("segmento").head(15).reset_index(drop=True)

        # Conversão de datas padrão
        for col in schema.get("dates", []):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

        # ─── Lógica Especial: Matriz Cross-Tab para Última Compra ───
        if schema_name == "recebimento_programado":
            # 1. Identificar colunas que parecem datas (Ex: jan/26, 01/26, 2026-01)
            # Vamos considerar colunas que não são as fixas do schema
            fixed_cols = ["cliente", "produto", "segmento", "genero", "publico", "data_entrega"]
            potential_date_cols = [c for c in df.columns if c.lower() not in fixed_cols]
            
            # Tentar converter essas colunas para data. Se falhar na maioria, talvez não seja matriz.
            date_map = {}
            for col in potential_date_cols:
                parsed_date = pd.to_datetime(col, errors="coerce", dayfirst=True)
                if pd.notna(parsed_date):
                    date_map[col] = parsed_date
            
            if date_map:
                # É uma matriz! Vamos dar um "melt"
                id_vars = [c for c in df.columns if c not in date_map.keys()]
                df_melted = df.melt(id_vars=id_vars, value_vars=list(date_map.keys()), 
                                    var_name="_col_data", value_name="quantidade")
                
                # Converter a coluna de data var_name para datetime real
                df_melted["data_faturamento"] = df_melted["_col_data"].map(date_map)
                
                # Filtrar apenas onde quantidade > 0
                df_melted["quantidade"] = pd.to_numeric(df_melted["quantidade"], errors="coerce").fillna(0)
                df_valid = df_melted[df_melted["quantidade"] > 0].copy()
                
                if not df_valid.empty:
                    # Ajustar colunas para o padrão do sistema
                    df_final = df_valid.rename(columns={"data_faturamento": "data_entrega"})
                    return df_final, errors
                else:
                    return pd.DataFrame(columns=schema["columns"]), ["Nenhuma quantidade encontrada nas colunas de data."]

        return df, errors
    except Exception as e:
        return None, [f"Erro ao ler arquivo: {str(e)}"]


# ─────────────────────────────────────────────
# Gerador de Dados de Exemplo
# ─────────────────────────────────────────────
_CLIENTES = [
    "Loja Estrela", "Calçados Silva", "Rede Conforto",
    "Magazine Passos", "Sapataria Central", "Top Shoes",
    "Pé Feliz", "Mundo dos Pés",
]

_CLIENT_REGIONS = {
    "Loja Estrela": "Sul",
    "Calçados Silva": "Sudeste",
    "Rede Conforto": "Sudeste",
    "Magazine Passos": "Nordeste",
    "Sapataria Central": "Centro-Oeste",
    "Top Shoes": "Sul",
    "Pé Feliz": "Norte",
    "Mundo dos Pés": "Nordeste",
}

_PRODUTOS_BASE = {
    "bota": {
        "linha": ["adventure", "urban", "classic"],
        "modelos": ["BT-1001", "BT-1002", "BT-1003", "BT-1004", "BT-1005"],
        "preco_range": (189.90, 349.90),
    },
    "sandalia": {
        "linha": ["casual", "sport", "elegance"],
        "modelos": ["SD-2001", "SD-2002", "SD-2003", "SD-2004", "SD-2005"],
        "preco_range": (59.90, 149.90),
    },
    "sapato": {
        "linha": ["social", "casual", "confort"],
        "modelos": ["SP-3001", "SP-3002", "SP-3003", "SP-3004", "SP-3005"],
        "preco_range": (149.90, 299.90),
    },
    "sapatenis": {
        "linha": ["casual", "sport", "urban"],
        "modelos": ["ST-4001", "ST-4002", "ST-4003", "ST-4004"],
        "preco_range": (129.90, 249.90),
    },
    "chinelo": {
        "linha": ["basico", "confort", "sport"],
        "modelos": ["CH-5001", "CH-5002", "CH-5003"],
        "preco_range": (29.90, 79.90),
    },
}

_GENEROS = ["masculino", "feminino"]
_PUBLICOS = ["adulto", "infantil", "juvenil"]


def _build_product_catalog() -> list[dict]:
    catalog = []
    for seg, info in _PRODUTOS_BASE.items():
        for modelo in info["modelos"]:
            gen = random.choice(_GENEROS)
            pub = random.choice(_PUBLICOS)
            linha = random.choice(info["linha"])
            preco = round(random.uniform(*info["preco_range"]), 2)
            
            # Layer de Inteligência Visual (v4.0)
            status_options = ["Novos", "Verificar Produto", "Fora de Linha", "Segue no Mix", "Avaliar Retirada", "Bem Posicionado"]
            catalog.append({
                "produto": modelo,
                "segmento": seg,
                "linha": linha,
                "modelo": modelo,
                "genero": gen,
                "publico": pub,
                "preco_pdv": preco,
                "status": random.choice(status_options),
                "classificacao": random.choice(["A", "B", "C"])
            })
    return catalog


def generate_sample_data() -> dict[str, pd.DataFrame]:
    random.seed(42)
    np.random.seed(42)
    catalog = _build_product_catalog()
    today = datetime(2026, 3, 1)

    # ─── Sell Out ───
    sell_rows = []
    for cliente in _CLIENTES:
        n_products = random.randint(8, len(catalog))
        selected = random.sample(catalog, min(n_products, len(catalog)))
        for prod in selected:
            venda = max(0, int(np.random.normal(40, 20)))
            estoque = max(0, int(np.random.normal(25, 15)))
            sell_rows.append({
                "cliente": cliente,
                "produto": prod["produto"],
                "venda": venda,
                "estoque": estoque,
                "segmento": prod["segmento"],
                "linha": prod["linha"],
                "modelo": prod["modelo"],
                "genero": prod["genero"],
                "publico": prod["publico"],
                "preco_pdv": prod["preco_pdv"],
                "regiao": _CLIENT_REGIONS.get(cliente, "Sudeste"),
                "ano_venda": 2026,
                "mes_venda": 2
            })
    df_sell = pd.DataFrame(sell_rows)

    # ─── Pedidos em Carteira ───
    pedido_rows = []
    for cliente in _CLIENTES[:5]:
        n_pedidos = random.randint(2, 6)
        prods = random.sample(catalog, n_pedidos)
        for prod in prods:
            pedido_rows.append({
                "cliente": cliente,
                "produto": prod["produto"],
                "quantidade": random.randint(5, 30),
                "segmento": prod["segmento"],
                "linha": prod["linha"],
                "genero": prod["genero"],
                "publico": prod["publico"],
                "data_faturamento": today + timedelta(days=random.randint(5, 30)),
            })
    df_pedidos = pd.DataFrame(pedido_rows)

    # ─── Campeões de Venda ───
    camp_rows = []
    top_products = random.sample(catalog, min(15, len(catalog)))
    for i, prod in enumerate(top_products):
        camp_rows.append({
            "produto": prod["produto"],
            "quantidade_vendida": max(50, 500 - i * 30 + random.randint(-20, 20)),
            "segmento": prod["segmento"],
            "genero": prod["genero"],
            "publico": prod["publico"],
        })
    df_campeoes = pd.DataFrame(camp_rows)

    # ─── Última Compra ───
    uc_rows = []
    for cliente in _CLIENTES:
        n = random.randint(5, 12)
        prods = random.sample(catalog, min(n, len(catalog)))
        for prod in prods:
            dias_atras = random.randint(10, 200)
            uc_rows.append({
                "cliente": cliente,
                "produto": prod["produto"],
                "data_ultima_compra": today - timedelta(days=dias_atras),
                "segmento": prod["segmento"],
                "genero": prod["genero"],
                "publico": prod["publico"],
            })
    df_ultima = pd.DataFrame(uc_rows)

    # ─── Histórico de Sell Out ───
    hist_rows = []
    for cliente in _CLIENTES[:4]:
        sel = random.sample(catalog, min(6, len(catalog)))
        for prod in sel:
            for m in range(8):
                mes_dt = today - timedelta(days=30 * (m + 1))
                mes_str = mes_dt.strftime("%Y-%m")
                venda = max(0, int(np.random.normal(35, 15)))
                hist_rows.append({
                    "cliente": cliente,
                    "produto": prod["produto"],
                    "mes": mes_str,
                    "venda": venda,
                })
    df_historico = pd.DataFrame(hist_rows)

    return {
        "sell_out": df_sell,
        "pedidos": df_pedidos,
        "campeoes": df_campeoes,
        "ultima_compra": df_ultima,
        "historico": df_historico,
    }
