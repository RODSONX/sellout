"""
🧠 Sistema de Inteligência de Sell-Out & Planejamento de Vendas
Aplicação principal — Streamlit multi-page
"""
import streamlit as st

# ─── Page Config ───
st.set_page_config(layout='wide', page_title='KAMPEG')

import tema # <-- Importa o arquivo tema

# Aplica o layout premium
tema.aplicar_layout()

# ─── Custom CSS Complementar ───
st.markdown("""
<style>
    /* Center the Hero Section (Stitch Style) */
    .hero-section {
        padding: 60px 20px;
        text-align: center;
        background: radial-gradient(circle at center, rgba(17, 51, 116, 0.1) 0%, transparent 70%);
        border-radius: 20px;
        border: 1px solid rgba(30, 41, 59, 0.5);
        margin-bottom: 40px;
    }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar ───
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 15px 0;">
        <h1 style="color: #ffffff; font-size: 1.8rem; margin: 0;">👟</h1>
        <h2 style="color: #f8fafc; font-size: 1rem; margin: 4px 0; font-weight: 600;">Pegada Analytics</h2>
        <p style="color: #cbd5e0; font-size: 0.75rem;">Intelligence & Planning</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Status dos dados
    st.markdown("### 📋 Status dos Dados")
    data_keys = {
        "sell_out": "🛒 Sell Out",
        "pedidos": "📋 Pedidos",
        "campeoes": "🏆 Campeões",
        "recebimento_programado": "🚚 Recebimentos",
        "historico": "📈 Histórico",
    }

    for key, label in data_keys.items():
        df = st.session_state.get(f"df_{key}")
        if df is not None and not df.empty:
            st.markdown(f"<span style='color: #22c55e; font-weight:600;'>●</span> {label} <span style='color: #94a3b8; font-size:0.75rem;'>({len(df)})</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color: #334155;'>○</span> {label}", unsafe_allow_html=True)

    st.divider()
    st.caption("v1.0 — Indústria de Calçados")


# ─── Main Page Hero ───
st.markdown("""
<div class="hero-section">
    <h1 style="color: #f8fafc; font-size: 2.2rem; margin-bottom: 12px;">
        Sua Central de Inteligência Pegada
    </h1>
    <p style="color: #cbd5e0; font-size: 1.05rem; max-width: 800px; margin: 0 auto; line-height: 1.6;">
        Transforme dados brutos de sell-out em decisões estratégicas. 
        Otimize seu mix, reduza rupturas e maximize o faturamento com nossa análise assistida.
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ─── Cards de funcionalidades ───
features = [
    ("📈", "Previsão de Vendas", "Média móvel, tendência e sazonalidade para projetar demanda futura."),
    ("📦", "Planejamento de Estoque", "Cobertura, estoque de segurança e sugestão automática de reposição."),
    ("🔀", "Análise de Mix", "Participação por segmento, gênero, público e faixa de preço."),
    ("🎯", "Oportunidades", "Produtos campeões não vendidos, vendas abaixo da média e substituições."),
    ("🚨", "Alertas Automáticos", "Ruptura, excesso, mix fora do ideal e produtos sem recebimento recente."),
    ("⚙️", "Configurável", "Todos os parâmetros editáveis: sazonalidade, faixas de preço, mix ideal e mais."),
]

cols = st.columns(3)
for i, (icon, title, desc) in enumerate(features):
    with cols[i % 3]:
        st.markdown(f"""
        <div class="v-card" style="min-height: 200px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 2rem;">
            <div style="font-size: 2.2rem; margin-bottom: 12px; background: rgba(17, 51, 116, 0.1); width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; border-radius: 12px; color: #0ea5e9;">{icon}</div>
            <h3 style="margin: 0 0 8px 0; font-size: 1.1rem; color: #ffffff;">{title}</h3>
            <p style="color: #94a3b8; font-size: 0.85rem; margin: 0; line-height: 1.5;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Quick Start ───
st.markdown("""
<div style="text-align: center; padding: 20px;">
    <p style="color: #ccd6f6; font-size: 1rem;">
        👈 Use o menu lateral para navegar. Comece importando seus dados em <strong>📊 Importar Dados</strong>.
    </p>
</div>
""", unsafe_allow_html=True)
