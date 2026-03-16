"""
Página 2 — Vitrine
Visualização de produtos organizada por preço com fotos dinâmicas.
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import sys, os

import tema
from helpers import run_forecast_and_inventory, apply_professional_layout

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

def card_produto(nome, referencia, vendas, estoque, selecionado, cor="#444"):
    url_img = f"https://www.pegada.com.br/uploadimagens/{referencia}.jpg"
    border_style = f"2px solid #2563eb" if selecionado else f"1.5px solid {cor}"
    opacity = "opacity: 0.4;" if selecionado else "opacity: 1;"
    check = f'<div style="position:absolute; top:3px; right:3px; background:#2563eb; color:white; border-radius:50%; width:14px; height:14px; font-size:9px; line-height:14px; z-index:100; text-align:center;">✓</div>' if selecionado else ""
    
    # Tag de cor (indicador visual de status)
    tag_cor = f'<div style="position:absolute; top:8px; left:8px; background:{cor}; width:10px; height:10px; border-radius:50%; border: 1px solid rgba(255,255,255,0.3); z-index:101;"></div>'

    html = f'''<div style="background:#111827; padding:4px; border-radius:6px; border: {border_style}; position: relative; margin: 0 auto 5px auto; max-width: 160px; box-shadow: 0 1px 3px rgba(0,0,0,0.3);">
{tag_cor}
{check}
<div style="background: white; border-radius: 3px; height: 85px; display: flex; align-items: center; justify-content: center; overflow: hidden; margin-bottom: 3px;">
<img src="{url_img}" style="max-width: 95%; max-height: 95%; object-fit: contain; {opacity}">
</div>
<h4 style="margin: 0; font-size: 13px; color: white; text-align: center; font-weight: 700; line-height: 1.1; width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{nome}</h4>
<div style="display: flex; justify-content: space-between; font-size: 11px; color: #9ca3af; border-top: 1px solid #1f2937; padding-top: 2px; margin-top: 2px;">
<span style="font-weight: 500;">↑ {vendas} u</span>
<span style="font-weight: 500;">📦 {estoque}</span>
</div>
</div>'''
    st.markdown(html, unsafe_allow_html=True)

def render():
    # --- Estética Global ---
    tema.aplicar_layout()
    
    # --- Controle de Estado ---
    if "sapatos_selecionados" not in st.session_state:
        st.session_state.sapatos_selecionados = []
    if "tags" not in st.session_state:
        st.session_state.tags = {}
    if "produtos_extras" not in st.session_state:
        st.session_state.produtos_extras = []
    if "produtos_removidos" not in st.session_state:
        st.session_state.produtos_removidos = []


    df_sell = st.session_state.get("df_sell_out")
    if df_sell is None or df_sell.empty:
        st.warning("⚠️ Importe os dados de Sell Out para começar.")
        return


    # Obter dados processados
    df_results = run_forecast_and_inventory()
    if df_results[0] is None:
        st.warning(f"⚠️ {df_results[1]}")
        return
        
    df_inv, period_str = df_results
    df_inv = df_inv.dropna(subset=["produto"])
    
    # Sincronizar dados entre DataFrame e Session State (Persistence)
    if not st.session_state.tags and "status_estrategico" in df_inv.columns:
        for _, row in df_inv.iterrows():
            if pd.notna(row["status_estrategico"]) and row["status_estrategico"] not in ["Indefinido", "Sem Classificação"]:
                st.session_state.tags[(str(row["cliente"]), str(row["produto"]))] = row["status_estrategico"]

    # --- Sidebar ---
    # --- Sidebar (Painel de Controle) ---
    with st.sidebar:
        st.subheader("🎨 Classificação")
        num_sel = len(st.session_state.sapatos_selecionados)
        st.info(f"Itens Selecionados: **{num_sel}**")
        
        status_config = [
            ("🟡 Novos", "Novos"), ("🟠 Verificar", "Verificar"), ("🔴 Fora de Linha", "Fora de Linha"),
            ("🟢 Segue no Mix", "Segue no Mix"), ("🟣 Retirar", "Retirar"), ("🔵 Bem Posicionado", "Bem Posicionado")
        ]
        
        for label, status in status_config:
            if st.button(label, key=f"side_btn_{status}", use_container_width=True):
                if st.session_state.sapatos_selecionados:
                    num_itens = len(st.session_state.sapatos_selecionados)
                    for ref in st.session_state.sapatos_selecionados:
                        st.session_state.tags[("Global", ref)] = status
                    
                    # Novo Comportamento: Limpar seleção automaticamente
                    st.session_state.sapatos_selecionados = []
                    
                    st.toast(f"Status '{status}' aplicado a {num_itens} itens!", icon="✨")
                    st.rerun()
                else:
                    st.warning("Selecione produtos no grid!")

        st.divider()

        # --- Painel de Ações Agrupado ---
        with st.sidebar.expander("🛠️ Painel de Ações", expanded=False):
            with st.container():
                # A. Sub-expander para Adição Manual
                with st.expander("➕ Novo Produto", expanded=False):
                    with st.form(key="form_add_manual_side"):
                        ref = st.text_input("Referência", placeholder="ex: 110507-01")
                        pdv = st.number_input("Preço PDV", min_value=0.0, format="%.2f")
                        lin = st.text_input("Linha")
                        seg = st.text_input("Segmento")
                        pub = st.text_input("Público")
                        gen = st.text_input("Gênero")
                        if st.form_submit_button("Adicionar", use_container_width=True):
                            if ref:
                                novo = {
                                    "produto": ref, "referencia": ref, "preco_pdv": pdv,
                                    "linha": lin.upper().strip(), "segmento": seg.upper().strip(),
                                    "publico": pub.upper().strip(), "genero": gen.upper().strip(),
                                    "venda": 0, "estoque": 0
                                }
                                st.session_state.produtos_extras.append(novo)
                                st.toast(f"PRODUTO {ref} ADICIONADO!", icon="✅")
                                st.rerun()
                            else:
                                st.error("Referência obrigatória.")

                st.markdown("---")

                # B. Remover Selecionados
                if st.button("🗑️ Remover Selecionados", use_container_width=True):
                    if st.session_state.sapatos_selecionados:
                        for sap in st.session_state.sapatos_selecionados:
                            if sap not in st.session_state.produtos_removidos:
                                st.session_state.produtos_removidos.append(sap)
                        st.session_state.sapatos_selecionados = []
                        st.toast("Produtos removidos!", icon="🗑️")
                        st.rerun()
                    else:
                        st.warning("Selecione produtos!")

                # C. Restaurar Removidos (Discreto)
                if st.session_state.produtos_removidos:
                    st.markdown("---")
                    st.caption("♻️ Restaurar Removido")
                    prod_r = st.selectbox("Selecione o SKU", st.session_state.produtos_removidos, key="sb_restaurar", label_visibility="collapsed")
                    if st.button("Confirmar Restauração", use_container_width=True):
                        st.session_state.produtos_removidos.remove(prod_r)
                        st.rerun()
                
                st.markdown("---")

                # D. Gerar Excel
                if st.button("📊 Gerar Planilha Excel", use_container_width=True, type="primary"):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                    filename = f"planejamento_{timestamp}.xlsx"
                    df_exp = df_inv.copy()
                    df_exp["status_estrategico"] = df_exp.apply(
                        lambda row: st.session_state.tags.get(("Global", str(row["produto"])), "Sem Classificação"), axis=1
                    )
                    z_mask = df_exp["status_estrategico"].isin(["Fora de Linha", "Retirar"])
                    df_exp.loc[z_mask, ["pedido_sugerido", "pedido_calculado"]] = 0
                    
                    output = pd.ExcelWriter(filename, engine='openpyxl')
                    df_exp.to_excel(output, index=False)
                    output.close()
                    with open(filename, "rb") as f:
                        st.download_button("📥 Baixar Planilha", f, file_name=filename, use_container_width=True)

        st.divider()
        st.subheader("🔍 Filtros")
        opcoes_status = ["Novos", "Verificar", "Fora de Linha", "Segue no Mix", "Retirar", "Bem Posicionado"]
        filter_status = st.multiselect("Classificação KAM:", opcoes_status)

    # Filtragem Global (Sempre todos os clientes para a Vitrine)
    df_filtered = df_inv.copy()
    
    # --- LOGICA DE FILTRO POR DATA (Mes/Ano mais recente) ---
    # Para garantir que a Vitrine não some o histórico, filtramos pelo período maximo
    if "ano_venda" in df_filtered.columns and "mes_venda" in df_filtered.columns:
        df_filtered["_period_score"] = pd.to_numeric(df_filtered["ano_venda"]) * 100 + pd.to_numeric(df_filtered["mes_venda"])
        max_p = df_filtered["_period_score"].max()
        df_filtered = df_filtered[df_filtered["_period_score"] == max_p].copy()

    # --- CSS PARA CONGELAR FILTROS E PREÇOS (STICKY) ---
    st.markdown("""
        <style>
            /* TARGET: The specific container with our anchor */
            div[data-testid="stVerticalBlock"] > div:has(div.sticky-anchor) {
                position: sticky;
                top: 2.875rem; /* Ajuste para não ficar sob a barra do Streamlit */
                z-index: 1001;
                background-color: #0e1117; 
                padding: 15px 0 10px 0; /* Aumentado o padding superior */
                border-bottom: 2px solid #1f2937;
            }
            
            /* Ensure the anchor itself doesn't take space */
            .sticky-anchor {
                display: none;
            }

            /* Redução do GAP entre colunas e paddings do grid do Streamlit */
            div[data-testid="column"] {
                padding: 0 !important;
                flex: none !important;      /* Desativa o crescimento automático */
                width: 160px !important;    /* Força largura fixa idêntica para todos */
            }
            div[data-testid="stHorizontalBlock"] {
                gap: 8px !important;        /* Espaçamento fixo entre as colunas */
                justify-content: flex-start !important; /* Empacota as colunas à esquerda */
            }

            /* Achatar botões de seleção (+) na vitrine e centralizar */
            div[data-testid="stButton"] {
                max-width: 160px !important;
                margin: 0 auto !important;
            }
            div[data-testid="stButton"] button {
                height: 24px !important;
                min-height: 24px !important;
                padding-top: 0px !important;
                padding-bottom: 0px !important;
                line-height: 24px !important;
                font-size: 14px !important;
                width: 100% !important;
            }

            /* Fix para botões da sidebar - Classificação */
            section[data-testid="stSidebar"] div[data-testid="stButton"] button {
                height: 38px !important;
                line-height: 1.2 !important;
                font-size: 13px !important;
                white-space: normal !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                padding: 2px 5px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # Contêiner Único para AREA STICKY (Filtros + Preços)
    with st.container():
        st.markdown('<div class="sticky-anchor"></div>', unsafe_allow_html=True)
        
        # 1. Barra de Filtros Superior
        f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)
        with f_col1:
            opts_seg = sorted(df_filtered["segmento"].dropna().unique()) if "segmento" in df_filtered.columns else []
            sel_seg = st.multiselect("Segmento", opts_seg)
        with f_col2:
            opts_lin = sorted(df_filtered["linha"].dropna().unique()) if "linha" in df_filtered.columns else []
            sel_lin = st.multiselect("Linha", opts_lin)
        with f_col3:
            sel_ref = st.text_input("🔍 Busca Referência", placeholder="ex: 110...").strip().upper()
        with f_col4:
            opts_gen = sorted(df_filtered["genero"].dropna().unique()) if "genero" in df_filtered.columns else []
            sel_gen = st.multiselect("Gênero", opts_gen)
        with f_col5:
            opts_pub = sorted(df_filtered["publico"].dropna().unique()) if "publico" in df_filtered.columns else []
            sel_pub = st.multiselect("Público", opts_pub)

        # 2. Aplicar Filtros e Processar Dados (Dentro do Container para manter o fluxo)
        if sel_seg: df_filtered = df_filtered[df_filtered["segmento"].isin(sel_seg)]
        if sel_lin: df_filtered = df_filtered[df_filtered["linha"].isin(sel_lin)]
        if sel_ref:
            col_ref = "referencia" if "referencia" in df_filtered.columns else "produto"
            df_filtered = df_filtered[df_filtered[col_ref].astype(str).str.contains(sel_ref, case=False, na=False)]
        if sel_gen: df_filtered = df_filtered[df_filtered["genero"].isin(sel_gen)]
        if sel_pub: df_filtered = df_filtered[df_filtered["publico"].isin(sel_pub)]

        agg_dict = {"venda": "sum", "estoque": "sum", "preco_pdv": "first"}
        for c in ["referencia", "modelo", "segmento", "linha", "genero", "publico"]:
            if c in df_filtered.columns: agg_dict[c] = "first"
        
        df_prod = df_filtered.groupby("produto").agg(agg_dict).reset_index()
        if "referencia" not in df_prod.columns: df_prod["referencia"] = df_prod["produto"]
        if "modelo" not in df_prod.columns: df_prod["modelo"] = df_prod["produto"]

        if st.session_state.produtos_extras:
            df_manual = pd.DataFrame(st.session_state.produtos_extras)
            df_prod = pd.concat([df_prod, df_manual], ignore_index=True)
        
        df_prod = df_prod[~df_prod["produto"].astype(str).isin(st.session_state.produtos_removidos)]

        # Preparação final da Matriz
        dados_vitrine = df_prod.copy()
        dados_vitrine = dados_vitrine.rename(columns={"modelo":"nome", "venda":"vendas", "preco_pdv":"pdv"})
        if filter_status:
            dados_vitrine = dados_vitrine[dados_vitrine.apply(lambda r: st.session_state.tags.get(("Global", str(r["nome"])), "Sem Classificação") in filter_status, axis=1)]
        dados_vitrine = dados_vitrine.sort_values("vendas", ascending=False)

        # 3. Cabeçalhos de Preço (PDV)
        if not dados_vitrine.empty:
            pdvs_unicos = sorted(dados_vitrine['pdv'].unique())
            cols_headers = st.columns(len(pdvs_unicos))
            for idx, preco in enumerate(pdvs_unicos):
                with cols_headers[idx]:
                    st.markdown(f"""
                        <div style='max-width: 160px; margin: 0 auto;'>
                            <h3 style='text-align:center; color:#60a5fa; border-bottom: 2px solid #2563eb; padding-bottom:5px; font-size: 14px; margin: 0;'>
                                R$ {preco:,.2f}
                            </h3>
                        </div>
                    """, unsafe_allow_html=True)

    # --- GRID DE PRODUTOS (CONFIG) ---
    COLOR_MAP = {
        "Novos": "#FFFF00", "Verificar": "#FF8C00", "Fora de Linha": "#FF0000",
        "Segue no Mix": "#008000", "Retirar": "#800080", "Bem Posicionado": "#0000FF",
        "Sem Classificação": "#444"
    }

    # --- ÁREA DE CONTEÚDO (FORA DO STICKY) ---
    if not dados_vitrine.empty:
        cols_content = st.columns(len(pdvs_unicos))
        for idx, preco in enumerate(pdvs_unicos):
            with cols_content[idx]:
                produtos_neste_preco = dados_vitrine[dados_vitrine['pdv'] == preco]
                for row_idx, row in enumerate(produtos_neste_preco.itertuples()):
                    is_sel = row.referencia in st.session_state.sapatos_selecionados
                    status = st.session_state.tags.get(("Global", str(row.referencia)), "Sem Classificação")
                    cor_status = COLOR_MAP.get(status, "#444")
                    
                    card_produto(
                        nome=row.referencia, referencia=row.referencia,
                        vendas=int(row.vendas), estoque=int(row.estoque),
                        selecionado=is_sel, cor=cor_status
                    )
                    
                    btn_label = "✓" if is_sel else "＋"
                    if st.button(btn_label, key=f"btn_{row.referencia}_{preco}_{row_idx}", use_container_width=True):
                        if is_sel:
                            st.session_state.sapatos_selecionados.remove(row.referencia)
                        else:
                            st.session_state.sapatos_selecionados.append(row.referencia)
                        st.rerun()
    else:
        st.info("Nenhum produto encontrado com os filtros atuais.")

if __name__ == "__main__":
    render()
