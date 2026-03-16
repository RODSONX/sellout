"""
Configurações padrão do sistema de Inteligência de Sell-Out.
Todos os parâmetros são editáveis via aba de Configurações.
"""

# ---------- Calendário de Estações ----------
DEFAULT_SEASON_CALENDAR = {
    1: "verão",
    2: "verão",
    3: "outono",
    4: "outono",
    5: "outono",
    6: "inverno",
    7: "inverno",
    8: "inverno",
    9: "primavera",
    10: "primavera",
    11: "primavera",
    12: "verão",
}

# ---------- Sazonalidade por Segmento ----------
DEFAULT_SEASONALITY = {
    "sandalia e chinelo": {"verão": 1.72, "outono": 1.28, "inverno": 0.88, "primavera": 1.48},
    "sandalia e chinelo pgd": {"verão": 1.62, "outono": 1.34, "inverno": 1.02, "primavera": 1.44},
    "sandalia e chinelo inj": {"verão": 1.82, "outono": 1.44, "inverno": 1.12, "primavera": 1.50},
    "sapatenis pegada": {"verão": 1.02, "outono": 1.1, "inverno": 1.04, "primavera": 1.04},
    "sapatenis pgd": {"verão": 1.04, "outono": 1.1, "inverno": 1.02, "primavera": 1.04},
    "bota": {"verão": 0.26, "outono": 0.52, "inverno": 1.08, "primavera": 0.56},
    "sapato": {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    "sapato social": {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    "drive": {"verão": 1.32, "outono": 1.12, "inverno": 0.92, "primavera": 1.24},
    "pantufa": {"verão": 0.18, "outono": 0.5, "inverno": 1.12, "primavera": 0.34},
    "trekking": {"verão": 0.96, "outono": 1.08, "inverno": 1.2, "primavera": 1.0},
    "tenis pegada": {"verão": 1.04, "outono": 1.1, "inverno": 0.98, "primavera": 1.04},
    "cintos": {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    "carteiras": {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
}

# ---------- Regiões ----------
REGIONS = ["Sul", "Sudeste", "Centro-Oeste", "Nordeste", "Norte"]

# ---------- Sazonalidade Regional por Segmento (segmento x região x estação) ----------
DEFAULT_REGIONAL_SEASONALITY_SEGMENT = {
    ("sandalia e chinelo", "Sul"): {"verão": 1.5, "outono": 1.2, "inverno": 0.7, "primavera": 1.3},
    ("sandalia e chinelo", "Sudeste"): {"verão": 1.6, "outono": 1.2, "inverno": 0.8, "primavera": 1.3},
    ("sandalia e chinelo", "Centro-Oeste"): {"verão": 1.7, "outono": 1.3, "inverno": 0.9, "primavera": 1.4},
    ("sandalia e chinelo", "Nordeste"): {"verão": 1.9, "outono": 1.5, "inverno": 1.2, "primavera": 1.7},
    ("sandalia e chinelo", "Norte"): {"verão": 1.9, "outono": 1.5, "inverno": 1.2, "primavera": 1.7},
    ("sandalia e chinelo pgd", "Sul"): {"verão": 1.4, "outono": 1.2, "inverno": 0.8, "primavera": 1.3},
    ("sandalia e chinelo pgd", "Sudeste"): {"verão": 1.5, "outono": 1.2, "inverno": 0.9, "primavera": 1.3},
    ("sandalia e chinelo pgd", "Centro-Oeste"): {"verão": 1.6, "outono": 1.3, "inverno": 1.0, "primavera": 1.4},
    ("sandalia e chinelo pgd", "Nordeste"): {"verão": 1.8, "outono": 1.5, "inverno": 1.2, "primavera": 1.6},
    ("sandalia e chinelo pgd", "Norte"): {"verão": 1.8, "outono": 1.5, "inverno": 1.2, "primavera": 1.6},
    ("sandalia e chinelo inj", "Sul"): {"verão": 1.6, "outono": 1.3, "inverno": 0.9, "primavera": 1.4},
    ("sandalia e chinelo inj", "Sudeste"): {"verão": 1.7, "outono": 1.3, "inverno": 1.0, "primavera": 1.4},
    ("sandalia e chinelo inj", "Centro-Oeste"): {"verão": 1.8, "outono": 1.4, "inverno": 1.1, "primavera": 1.5},
    ("sandalia e chinelo inj", "Nordeste"): {"verão": 2.0, "outono": 1.6, "inverno": 1.3, "primavera": 1.8},
    ("sandalia e chinelo inj", "Norte"): {"verão": 2.0, "outono": 1.6, "inverno": 1.3, "primavera": 1.8},
    ("sapatenis pegada", "Sul"): {"verão": 1.0, "outono": 1.1, "inverno": 1.2, "primavera": 1.0},
    ("sapatenis pegada", "Sudeste"): {"verão": 1.0, "outono": 1.1, "inverno": 1.1, "primavera": 1.0},
    ("sapatenis pegada", "Centro-Oeste"): {"verão": 1.0, "outono": 1.1, "inverno": 1.0, "primavera": 1.0},
    ("sapatenis pegada", "Nordeste"): {"verão": 1.1, "outono": 1.1, "inverno": 0.9, "primavera": 1.1},
    ("sapatenis pegada", "Norte"): {"verão": 1.1, "outono": 1.1, "inverno": 0.9, "primavera": 1.1},
    ("sapatenis pgd", "Sul"): {"verão": 1.0, "outono": 1.1, "inverno": 1.2, "primavera": 1.0},
    ("sapatenis pgd", "Sudeste"): {"verão": 1.0, "outono": 1.1, "inverno": 1.1, "primavera": 1.0},
    ("sapatenis pgd", "Centro-Oeste"): {"verão": 1.0, "outono": 1.1, "inverno": 1.0, "primavera": 1.0},
    ("sapatenis pgd", "Nordeste"): {"verão": 1.1, "outono": 1.1, "inverno": 0.9, "primavera": 1.1},
    ("sapatenis pgd", "Norte"): {"verão": 1.1, "outono": 1.1, "inverno": 0.9, "primavera": 1.1},
    ("bota", "Sul"): {"verão": 0.3, "outono": 0.8, "inverno": 1.9, "primavera": 0.7},
    ("bota", "Sudeste"): {"verão": 0.4, "outono": 0.8, "inverno": 1.6, "primavera": 0.8},
    ("bota", "Centro-Oeste"): {"verão": 0.4, "outono": 0.8, "inverno": 1.3, "primavera": 0.9},
    ("bota", "Nordeste"): {"verão": 0.1, "outono": 0.2, "inverno": 0.3, "primavera": 0.2},
    ("bota", "Norte"): {"verão": 0.1, "outono": 0.2, "inverno": 0.3, "primavera": 0.2},
    ("sapato", "Sul"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("sapato", "Sudeste"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("sapato", "Centro-Oeste"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("sapato", "Nordeste"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("sapato", "Norte"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("sapato social", "Sul"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("sapato social", "Sudeste"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("sapato social", "Centro-Oeste"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("sapato social", "Nordeste"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("sapato social", "Norte"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("drive", "Sul"): {"verão": 1.2, "outono": 1.1, "inverno": 0.9, "primavera": 1.2},
    ("drive", "Sudeste"): {"verão": 1.3, "outono": 1.1, "inverno": 0.9, "primavera": 1.2},
    ("drive", "Centro-Oeste"): {"verão": 1.3, "outono": 1.1, "inverno": 0.9, "primavera": 1.2},
    ("drive", "Nordeste"): {"verão": 1.4, "outono": 1.2, "inverno": 1.0, "primavera": 1.3},
    ("drive", "Norte"): {"verão": 1.4, "outono": 1.2, "inverno": 1.0, "primavera": 1.3},
    ("pantufa", "Sul"): {"verão": 0.2, "outono": 0.7, "inverno": 2.0, "primavera": 0.4},
    ("pantufa", "Sudeste"): {"verão": 0.2, "outono": 0.7, "inverno": 1.7, "primavera": 0.4},
    ("pantufa", "Centro-Oeste"): {"verão": 0.3, "outono": 0.7, "inverno": 1.3, "primavera": 0.5},
    ("pantufa", "Nordeste"): {"verão": 0.1, "outono": 0.2, "inverno": 0.3, "primavera": 0.2},
    ("pantufa", "Norte"): {"verão": 0.1, "outono": 0.2, "inverno": 0.3, "primavera": 0.2},
    ("trekking", "Sul"): {"verão": 0.9, "outono": 1.1, "inverno": 1.5, "primavera": 1.0},
    ("trekking", "Sudeste"): {"verão": 0.9, "outono": 1.1, "inverno": 1.3, "primavera": 1.0},
    ("trekking", "Centro-Oeste"): {"verão": 1.0, "outono": 1.1, "inverno": 1.2, "primavera": 1.0},
    ("trekking", "Nordeste"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("trekking", "Norte"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("tenis pegada", "Sul"): {"verão": 1.0, "outono": 1.1, "inverno": 1.1, "primavera": 1.0},
    ("tenis pegada", "Sudeste"): {"verão": 1.0, "outono": 1.1, "inverno": 1.0, "primavera": 1.0},
    ("tenis pegada", "Centro-Oeste"): {"verão": 1.0, "outono": 1.1, "inverno": 1.0, "primavera": 1.0},
    ("tenis pegada", "Nordeste"): {"verão": 1.1, "outono": 1.1, "inverno": 0.9, "primavera": 1.1},
    ("tenis pegada", "Norte"): {"verão": 1.1, "outono": 1.1, "inverno": 0.9, "primavera": 1.1},
    ("cintos", "Sul"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("cintos", "Sudeste"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("cintos", "Centro-Oeste"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("cintos", "Nordeste"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("cintos", "Norte"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("carteiras", "Sul"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("carteiras", "Sudeste"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("carteiras", "Centro-Oeste"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("carteiras", "Nordeste"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
    ("carteiras", "Norte"): {"verão": 1.0, "outono": 1.0, "inverno": 1.0, "primavera": 1.0},
}

# ---------- Mapeamento Padrão Cliente→Região ----------
DEFAULT_CLIENT_REGIONS = {
    "Loja Estrela": "Sul",
    "Calçados Silva": "Sudeste",
    "Rede Conforto": "Sudeste",
    "Magazine Passos": "Nordeste",
    "Sapataria Central": "Centro-Oeste",
    "Top Shoes": "Sul",
    "Pé Feliz": "Norte",
    "Mundo dos Pés": "Nordeste",
}

# ---------- Faixas de Preço ----------
DEFAULT_PRICE_RANGES = {
    "baixo":   {"min": 0,   "max": 99.99},
    "medio":   {"min": 100, "max": 199.99},
    "alto":    {"min": 200, "max": 349.99},
    "premium": {"min": 350, "max": 99999},
}

# ---------- Mix Ideal da Marca ----------
DEFAULT_IDEAL_MIX = {
    "segmento": {
        "sandalia e chinelo": 0.10,
        "sandalia e chinelo pgd": 0.10,
        "sandalia e chinelo inj": 0.10,
        "sapatenis pegada": 0.10,
        "sapatenis pgd": 0.10,
        "bota": 0.10,
        "sapato": 0.10,
        "sapato social": 0.05,
        "drive": 0.05,
        "pantufa": 0.05,
        "trekking": 0.05,
        "tenis pegada": 0.05,
        "cintos": 0.02,
        "carteiras": 0.03,
    },
    "genero": {
        "masculino": 0.50,
        "feminino": 0.50,
    },
    "publico": {
        "normal size": 0.40,
        "small size": 0.30,
        "plus size": 0.30,
    },
}

# ---------- Parâmetros de Cálculo ----------
DEFAULT_SAFETY_STOCK_PCT = 0.30          # 30% de estoque de segurança
DEFAULT_DAYS_WITHOUT_PURCHASE = 120       # dias sem compra para alerta
DEFAULT_COVERAGE_RUPTURE_THRESHOLD = 0.5  # cobertura abaixo de 0.5 = ruptura
DEFAULT_COVERAGE_EXCESS_THRESHOLD = 4.0   # cobertura acima de 4 = excesso
DEFAULT_DAYS_SAFETY = 15                  # estoque de segurança em dias
DEFAULT_MONTHLY_CAPACITY = 1000           # limite de pedidos por mês (capacidade loja)
DEFAULT_LEAD_TIME_DAYS = 60               # lead time logístico em dias
DEFAULT_RECEIPT_WINDOW_MONTHS = 4         # janela para alerta de recebimento recente

# ---------- Pesos dos Algoritmos ----------
DEFAULT_ALGORITHM_WEIGHTS = {
    "media_movel": 0.5,
    "tendencia": 0.3,
    "sazonalidade": 0.2,
}

# ---------- Sazonalidade Mensal (estimativa varejo calçadista) ----------
DEFAULT_MONTHLY_SEASONALITY = [
    {"mes": 1,  "segmento": "geral", "fator": 0.85},
    {"mes": 2,  "segmento": "geral", "fator": 0.90},
    {"mes": 3,  "segmento": "geral", "fator": 1.00},
    {"mes": 4,  "segmento": "geral", "fator": 1.10},
    {"mes": 5,  "segmento": "geral", "fator": 1.20},
    {"mes": 6,  "segmento": "geral", "fator": 1.15},
    {"mes": 7,  "segmento": "geral", "fator": 1.05},
    {"mes": 8,  "segmento": "geral", "fator": 1.10},
    {"mes": 9,  "segmento": "geral", "fator": 1.00},
    {"mes": 10, "segmento": "geral", "fator": 1.10},
    {"mes": 11, "segmento": "geral", "fator": 1.25},
    {"mes": 12, "segmento": "geral", "fator": 1.45},
]

# ---------- Calendário de Eventos do Varejo ----------
DEFAULT_RETAIL_EVENTS = [
    {"mes": 5,  "evento": "Dia das Mães", "categoria_foco": "feminino", "fator_evento": 1.25},
    {"mes": 6,  "evento": "Dia dos Namorados", "categoria_foco": "geral", "fator_evento": 1.15},
    {"mes": 8,  "evento": "Dia dos Pais", "categoria_foco": "masculino", "fator_evento": 1.20},
    {"mes": 10, "evento": "Dia das Crianças", "categoria_foco": "infantil", "fator_evento": 1.20},
    {"mes": 11, "evento": "Black Friday", "categoria_foco": "geral", "fator_evento": 1.30},
    {"mes": 12, "evento": "Natal", "categoria_foco": "geral", "fator_evento": 1.35},
]
