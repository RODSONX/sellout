"""
Página 1 — Importar Dados
Upload e visualização dos dados de entrada.
"""
import streamlit as st
import pandas as pd
import tema
from data_loader import parse_upload, generate_sample_data, SCHEMAS
from helpers import apply_professional_layout

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

def render():
    tema.aplicar_layout()
    st.header("📊 Importar Dados")
    st.markdown("Carregue seus arquivos CSV ou Excel para cada aba de dados, ou use dados de exemplo para demonstração.")

    # ─── Botão de dados de exemplo ───
    st.divider()
    col_demo1, col_demo2 = st.columns([3, 1])
    with col_demo1:
        st.markdown("**🎲 Demonstração rápida** — Carregar dados de exemplo automaticamente")
    with col_demo2:
        if st.button("📥 Carregar Exemplo", type="primary", use_container_width=True):
            sample = generate_sample_data()
            for key, df in sample.items():
                st.session_state[f"df_{key}"] = df
            st.success("✅ Dados de exemplo carregados com sucesso!")
            st.rerun()

    with st.sidebar:
        st.divider()
        st.markdown("**🌍 Escopo Geográfico**")
        st.caption("Selecione as regiões onde a rede atua para ajustar a sazonalidade.")
        from config import REGIONS
        
        # Initialize session state if not present
        if "cfg_analysis_regions" not in st.session_state:
            st.session_state["cfg_analysis_regions"] = []
            
        selected_regions = st.multiselect(
            "REGIÃO DA REDE",
            options=REGIONS,
            default=st.session_state["cfg_analysis_regions"],
            help="Deixe em branco para considerar o Brasil inteiro.",
            key="temp_analysis_regions", 
        )
        st.session_state["cfg_analysis_regions"] = selected_regions

    st.divider()

    # ─── Upload Tabs ───
    tabs = st.tabs([
        "🛒 Sell Out",
        "📋 Pedidos em Carteira",
        "🏆 Campeões de Venda",
        "🚚 Recebimento Programado",
        "📈 Histórico (Opcional)",
    ])

    upload_configs = [
        {"tab_idx": 0, "key": "sell_out", "label": "Sell Out",
         "help": "Campos: cliente, produto, venda, estoque, segmento, linha, modelo, genero, publico, preco_pdv"},
        {"tab_idx": 1, "key": "pedidos", "label": "Pedidos em Carteira",
         "help": "Campos: cliente, produto, quantidade, segmento, linha, genero, publico, data_faturamento"},
        {"tab_idx": 2, "key": "campeoes", "label": "Campeões de Venda",
         "help": "Campos: produto, quantidade_vendida, segmento, genero, publico"},
        {"tab_idx": 3, "key": "recebimento_programado", "label": "Recebimento Programado",
         "help": "Aceita Matriz (Jan/26, Fev/26...) ou Tabela simples (cliente, produto, data_entrega)"},
        {"tab_idx": 4, "key": "historico", "label": "Histórico de Sell Out",
         "help": "Campos: cliente, produto, mes, venda"},
    ]

    for cfg in upload_configs:
        with tabs[cfg["tab_idx"]]:
            st.markdown(f"**{cfg['label']}**")
            st.caption(cfg["help"])

            uploaded = st.file_uploader(
                f"Upload {cfg['label']}",
                type=["csv", "xlsx", "xls"],
                key=f"upload_{cfg['key']}",
                label_visibility="collapsed",
            )

            if uploaded is not None:
                df, errors = parse_upload(uploaded, cfg["key"])
                if errors:
                    for e in errors:
                        st.error(f"❌ {e}")
                else:
                    st.session_state[f"df_{cfg['key']}"] = df
                    st.success(f"✅ {len(df)} registros carregados")

            # Mostrar preview se dados já carregados
            session_key = f"df_{cfg['key']}"
            if session_key in st.session_state and st.session_state[session_key] is not None:
                df_loaded = st.session_state[session_key].copy()
                
                # Regra especial para Recebimento: ocultar cliente
                if cfg["key"] == "recebimento_programado":
                    cols_to_show = [c for c in df_loaded.columns if str(c).lower() != "cliente"]
                    df_loaded = df_loaded[cols_to_show]

                st.markdown(f"**{len(df_loaded)} registros carregados**")
                st.dataframe(df_loaded.head(20), use_container_width=True, height=300)

    # ─── Status Geral ───
    st.divider()
    st.subheader("📋 Status dos Dados")

    status_cols = st.columns(5)
    icons = ["🛒", "📋", "🏆", "🚚", "📈"]
    keys = ["sell_out", "pedidos", "campeoes", "recebimento_programado", "historico"]
    labels = ["Sell Out", "Pedidos", "Campeões", "Recebimentos", "Histórico"]

    for i, (icon, key, label) in enumerate(zip(icons, keys, labels)):
        with status_cols[i]:
            df = st.session_state.get(f"df_{key}")
            if df is not None and not df.empty:
                st.metric(f"{icon} {label}", f"{len(df)} reg.", delta="OK", delta_color="normal")
            else:
                st.metric(f"{icon} {label}", "—", delta="Pendente", delta_color="off")


if __name__ == "__main__":
    render()
