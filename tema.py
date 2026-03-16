# Arquivo: tema.py
import streamlit as st

def aplicar_layout():
    st.markdown("""
<style>
/* FUNDO GERAL */
.stApp { background: linear-gradient(180deg,#0b1220,#0f172a); }

/* CONTAINER WIDE */
.block-container { padding-top: 1.5rem !important; max-width: 100% !important; }

/* SIDEBAR PREMIUM E COMPACTA */
section[data-testid="stSidebar"] { background-color:#0f172a; border-right:1px solid #1f2937; }
[data-testid="stSidebar"] .stButton > button {
    height: 1.8rem !important; min-height: 1.8rem !important;
    font-size: 0.8rem !important; justify-content: flex-start !important;
    margin-bottom: -0.6rem !important; border-radius: 6px !important;
}

/* CARDS E INTERATIVIDADE */
.card, [data-testid="stMetric"] { background:#111827; padding:18px; border-radius:14px; box-shadow:0 8px 25px rgba(0,0,0,0.35); }
.prod-card { transition: 0.25s; border-radius: 14px; }
.prod-card:hover { transform: translateY(-5px); box-shadow: 0 12px 30px rgba(0,0,0,0.5); }

/* BOTÕES GERAIS (FORA DA SIDEBAR) */
.stButton button:not([data-testid="stSidebar"] button) {
    border-radius:10px; padding:8px 18px; background:#1f2937; border:1px solid #1f2937; transition:0.2s;
}
.stButton button:hover { background:#2563eb !important; border-color:#2563eb !important; }

/* COMPONENTES */
h1,h2,h3 { font-weight:600; letter-spacing:0.3px; color: #ffffff; }
.stSelectbox div, img { border-radius:10px !important; }
</style>
    """, unsafe_allow_html=True)
