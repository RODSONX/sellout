"""
Página 6 — Configurações
Todos os parâmetros do sistema editáveis pelo usuário.
Inclui: sazonalidade regional, lead time, regiões de clientes.
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tema
from helpers import apply_professional_layout
from config import (
    DEFAULT_SEASON_CALENDAR, DEFAULT_SEASONALITY, DEFAULT_PRICE_RANGES,
    DEFAULT_IDEAL_MIX, DEFAULT_SAFETY_STOCK_PCT, DEFAULT_ALGORITHM_WEIGHTS,
    DEFAULT_DAYS_WITHOUT_PURCHASE, DEFAULT_COVERAGE_RUPTURE_THRESHOLD,
    DEFAULT_COVERAGE_EXCESS_THRESHOLD, DEFAULT_RECEIPT_WINDOW_MONTHS,
    DEFAULT_REGIONAL_SEASONALITY_SEGMENT, DEFAULT_CLIENT_REGIONS, DEFAULT_LEAD_TIME_DAYS,
    DEFAULT_MONTHLY_SEASONALITY, DEFAULT_RETAIL_EVENTS,
    DEFAULT_DAYS_SAFETY, DEFAULT_MONTHLY_CAPACITY,
    REGIONS,
)

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

SEASON_NAMES = ["verão", "outono", "inverno", "primavera"]
MONTH_NAMES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


def render():
    tema.aplicar_layout()
    st.header("⚙️ Configurações")
    st.markdown("Edite os parâmetros de cálculo. As alterações são aplicadas automaticamente em todos os dashboards.")

    tabs = st.tabs([
        "📅 Calendário",
        "📊 Sazonalidade",
        "🌍 Sazonalidade Regional por Segmento",
        "📈 Sazonalidade Mensal",
        "📍 Regiões dos Clientes",
        "💰 Faixas de Preço",
        "🔀 Mix Ideal",
        "🔧 Parâmetros",
        "⚖️ Pesos",
    ])

    # ─── Tab 1: Calendário de Estações ───
    with tabs[0]:
        st.subheader("📅 Calendário de Estações")
        st.caption("Defina a estação de cada mês do ano.")

        calendar = st.session_state.get("cfg_season_calendar", DEFAULT_SEASON_CALENDAR.copy())

        cols = st.columns(4)
        new_calendar = {}
        for i, (month_num, month_name) in enumerate(MONTH_NAMES.items()):
            with cols[i % 4]:
                current = calendar.get(month_num, "verão")
                idx = SEASON_NAMES.index(current) if current in SEASON_NAMES else 0
                new_calendar[month_num] = st.selectbox(
                    month_name, SEASON_NAMES, index=idx, key=f"cal_{month_num}"
                )

        if st.button("💾 Salvar Calendário", type="primary"):
            st.session_state["cfg_season_calendar"] = new_calendar
            st.success("✅ Calendário salvo!")

        if st.button("🔄 Restaurar Padrão", key="reset_cal"):
            st.session_state["cfg_season_calendar"] = DEFAULT_SEASON_CALENDAR.copy()
            st.rerun()

        st.divider()
        st.subheader("🛍️ Datas Importantes do Varejo")
        st.caption("Eventos que impactam categorias específicas ou o volume geral.")

        events = st.session_state.get("cfg_retail_events", DEFAULT_RETAIL_EVENTS.copy())
        df_events = pd.DataFrame(events)

        edited_events = st.data_editor(
            df_events,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "mes": st.column_config.NumberColumn("Mês", min_value=1, max_value=12, step=1),
                "categoria_foco": st.column_config.SelectboxColumn("Categoria Foco", options=["geral", "masculino", "feminino", "infantil"]),
                "fator_evento": st.column_config.NumberColumn("Fator Evento", min_value=1.0, max_value=2.0, step=0.05),
            },
            key="events_editor",
        )

        col_ev1, col_ev2 = st.columns(2)
        with col_ev1:
            if st.button("💾 Salvar Eventos", type="primary"):
                st.session_state["cfg_retail_events"] = edited_events.to_dict("records")
                st.success("✅ Eventos salvos!")
        with col_ev2:
            if st.button("🔄 Restaurar Padrão", key="reset_events"):
                st.session_state["cfg_retail_events"] = DEFAULT_RETAIL_EVENTS.copy()
                st.rerun()

    # ─── Tab 2: Sazonalidade por Segmento ───
    with tabs[1]:
        st.subheader("📊 Fatores de Sazonalidade por Segmento")
        st.caption("Valores acima de 1.0 indicam alta demanda na estação. Esta tabela é usada como fallback quando não existe fator regional.")

        seasonality = st.session_state.get("cfg_seasonality", DEFAULT_SEASONALITY.copy())

        saz_data = []
        for seg, factors in seasonality.items():
            row = {"segmento": seg}
            row.update(factors)
            saz_data.append(row)

        df_saz = pd.DataFrame(saz_data)
        edited_saz = st.data_editor(df_saz, use_container_width=True, num_rows="dynamic", key="saz_editor")

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("💾 Salvar Sazonalidade", type="primary"):
                new_saz = {}
                for _, row in edited_saz.iterrows():
                    seg = row["segmento"]
                    new_saz[seg] = {s: float(row.get(s, 1.0)) for s in SEASON_NAMES}
                st.session_state["cfg_seasonality"] = new_saz
                st.success("✅ Sazonalidade salva!")
        with col_s2:
            if st.button("🔄 Restaurar Padrão", key="reset_saz"):
                st.session_state["cfg_seasonality"] = DEFAULT_SEASONALITY.copy()
                st.rerun()

    with tabs[2]:
        st.subheader("🌍 Sazonalidade Regional por Segmento")
        st.caption("Fatores de venda por segmento x região x estação. Tabela: sazonalidade_regional_segmento")

        regional = st.session_state.get("cfg_sazonalidade_regional_segmento", DEFAULT_REGIONAL_SEASONALITY_SEGMENT.copy())

        # Converter para DataFrame
        reg_data = []
        for (seg, regiao), factors in regional.items():
            row = {"segmento": seg, "regiao": regiao}
            row.update(factors)
            reg_data.append(row)

        df_reg = pd.DataFrame(reg_data)
        df_reg = df_reg.sort_values(["segmento", "regiao"]).reset_index(drop=True)

        # Filtro para facilitar edição
        seg_filter = st.selectbox(
            "Filtrar por segmento",
            ["Todos"] + sorted(df_reg["segmento"].unique().tolist()),
            key="reg_seg_filter",
        )
        if seg_filter != "Todos":
            mask = df_reg["segmento"] == seg_filter
            df_filtered = df_reg[mask].copy()
        else:
            df_filtered = df_reg.copy()

        edited_reg = st.data_editor(
            df_filtered,
            use_container_width=True,
            num_rows="dynamic",
            key="reg_editor",
        )

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("💾 Salvar Sazonalidade Regional", type="primary", key="save_reg_seg"):
                new_reg = {}
                # Manter as entradas originais que não estão no filtro
                if seg_filter != "Todos":
                    for (seg, regiao), factors in regional.items():
                        if seg != seg_filter:
                            new_reg[(seg, regiao)] = factors
                # Adicionar as editadas
                for _, row in edited_reg.iterrows():
                    seg = row["segmento"]
                    regiao = row["regiao"]
                    new_reg[(seg, regiao)] = {s: float(row.get(s, 1.0)) for s in SEASON_NAMES}
                st.session_state["cfg_sazonalidade_regional_segmento"] = new_reg
                st.success("✅ Sazonalidade regional salva!")
        with col_r2:
            if st.button("🔄 Restaurar Padrão", key="reset_reg"):
                st.session_state["cfg_sazonalidade_regional_segmento"] = DEFAULT_REGIONAL_SEASONALITY_SEGMENT.copy()
                st.rerun()

    # ─── Tab 4: Sazonalidade Mensal ───
    with tabs[3]:
        st.subheader("📈 Sazonalidade Mensal")
        st.caption("Comportamento típico de vendas por mês e segmento.")

        monthly_saz = st.session_state.get("cfg_monthly_seasonality", DEFAULT_MONTHLY_SEASONALITY.copy())
        df_monthly = pd.DataFrame(monthly_saz)

        # Se houver lista de segmentos, usar para o selectbox
        segments_list = ["geral"] + sorted(DEFAULT_SEASONALITY.keys())

        edited_monthly = st.data_editor(
            df_monthly,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "mes": st.column_config.NumberColumn("Mês", min_value=1, max_value=12, step=1),
                "segmento": st.column_config.SelectboxColumn("Segmento", options=segments_list),
                "fator": st.column_config.NumberColumn("Fator", min_value=0.1, max_value=3.0, step=0.05),
            },
            key="monthly_editor",
        )

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            if st.button("💾 Salvar Sazonalidade Mensal", type="primary"):
                st.session_state["cfg_monthly_seasonality"] = edited_monthly.to_dict("records")
                st.success("✅ Sazonalidade mensal salva!")
        with col_m2:
            if st.button("🔄 Restaurar Padrão", key="reset_monthly"):
                st.session_state["cfg_monthly_seasonality"] = DEFAULT_MONTHLY_SEASONALITY.copy()
                st.rerun()

    # ─── Tab 5: Regiões dos Clientes ───
    with tabs[4]:
        st.subheader("📍 Regiões dos Clientes")
        st.caption("Defina a região geográfica de cada cliente. Usado na sazonalidade regional.")

        client_regions = st.session_state.get("cfg_client_regions", DEFAULT_CLIENT_REGIONS.copy())

        # Se há sell_out carregado, puxar clientes de lá
        df_sell = st.session_state.get("df_sell_out")
        if df_sell is not None and not df_sell.empty:
            all_clients = sorted(df_sell["cliente"].unique().tolist())
        else:
            all_clients = sorted(client_regions.keys())

        cr_data = [{"cliente": c, "regiao": client_regions.get(c, "Sudeste")} for c in all_clients]
        df_cr = pd.DataFrame(cr_data)

        edited_cr = st.data_editor(
            df_cr,
            use_container_width=True,
            column_config={
                "regiao": st.column_config.SelectboxColumn("Região", options=REGIONS),
            },
            key="cr_editor",
        )

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("💾 Salvar Regiões", type="primary"):
                new_cr = dict(zip(edited_cr["cliente"], edited_cr["regiao"]))
                st.session_state["cfg_client_regions"] = new_cr
                st.success("✅ Regiões salvas!")
        with col_c2:
            if st.button("🔄 Restaurar Padrão", key="reset_cr"):
                st.session_state["cfg_client_regions"] = DEFAULT_CLIENT_REGIONS.copy()
                st.rerun()

    # ─── Tab 6: Faixas de Preço ───
    with tabs[5]:
        st.subheader("💰 Faixas de Preço")

        price_ranges = st.session_state.get("cfg_price_ranges", DEFAULT_PRICE_RANGES.copy())
        pr_data = [{"faixa": name, "min": bounds["min"], "max": bounds["max"]} for name, bounds in price_ranges.items()]
        df_pr = pd.DataFrame(pr_data)
        edited_pr = st.data_editor(df_pr, use_container_width=True, num_rows="dynamic", key="pr_editor")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("💾 Salvar Faixas de Preço", type="primary"):
                new_pr = {}
                for _, row in edited_pr.iterrows():
                    new_pr[row["faixa"]] = {"min": float(row["min"]), "max": float(row["max"])}
                st.session_state["cfg_price_ranges"] = new_pr
                st.success("✅ Faixas de preço salvas!")
        with col_p2:
            if st.button("🔄 Restaurar Padrão", key="reset_pr"):
                st.session_state["cfg_price_ranges"] = DEFAULT_PRICE_RANGES.copy()
                st.rerun()

    # ─── Tab 7: Mix Ideal ───
    with tabs[6]:
        st.subheader("🔀 Mix Ideal da Marca")
        st.caption("Defina a participação ideal (em decimal, ex: 0.30 = 30%).")

        ideal_mix = st.session_state.get("cfg_ideal_mix", DEFAULT_IDEAL_MIX.copy())

        for dim_label, dim_key in [("Segmento", "segmento"), ("Gênero", "genero"), ("Público", "publico")]:
            st.markdown(f"**{dim_label}**")
            mix_data = [{"categoria": k, "participacao": v} for k, v in ideal_mix.get(dim_key, {}).items()]
            df_mix = pd.DataFrame(mix_data)
            
            # Restringir opções para Gênero e Público
            col_config = {}
            if dim_key == "genero":
                col_config = {"categoria": st.column_config.SelectboxColumn("Categoria", options=["masculino", "feminino"])}
            elif dim_key == "publico":
                col_config = {"categoria": st.column_config.SelectboxColumn("Categoria", options=["normal size", "small size", "plus size"])}
            elif dim_key == "segmento":
                segments_list = sorted(DEFAULT_SEASONALITY.keys())
                col_config = {"categoria": st.column_config.SelectboxColumn("Categoria", options=segments_list)}
            
            edited_mix = st.data_editor(
                df_mix, 
                use_container_width=True, 
                num_rows="dynamic", 
                column_config=col_config,
                key=f"mix_{dim_key}"
            )
            total = edited_mix["participacao"].sum()
            if abs(total - 1.0) > 0.01:
                st.warning(f"⚠️ A soma das participações é {total:.2f}. Deveria ser 1.00.")
            ideal_mix[dim_key] = dict(zip(edited_mix["categoria"], edited_mix["participacao"]))

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            if st.button("💾 Salvar Mix Ideal", type="primary"):
                st.session_state["cfg_ideal_mix"] = ideal_mix
                st.success("✅ Mix ideal salvo!")
        with col_m2:
            if st.button("🔄 Restaurar Padrão", key="reset_mix"):
                st.session_state["cfg_ideal_mix"] = DEFAULT_IDEAL_MIX.copy()
                st.rerun()

    # ─── Tab 8: Parâmetros de Cálculo ───
    with tabs[7]:
        st.subheader("🔧 Parâmetros de Cálculo")

        lead_time = st.number_input(
            "🚚 Lead Time Logístico (dias)",
            min_value=1, max_value=180,
            value=int(st.session_state.get("cfg_lead_time_days", DEFAULT_LEAD_TIME_DAYS)),
            step=5,
            help="Tempo entre produção, faturamento e entrega ao cliente. Usado para calcular estação futura e venda durante lead time.",
        )

        st.divider()

        safety_days = st.number_input(
            "🛡️ Estoque de Segurança (Dias)",
            min_value=0, max_value=90,
            value=int(st.session_state.get("cfg_days_safety", DEFAULT_DAYS_SAFETY)),
            step=5,
            help="Quantos dias de venda futura o estoque de segurança deve cobrir.",
        )

        monthly_capacity = st.number_input(
            "🏪 Capacidade de Venda Mensal (Limite)",
            min_value=1, max_value=50000,
            value=int(st.session_state.get("cfg_monthly_capacity", DEFAULT_MONTHLY_CAPACITY)),
            step=100,
            help="Limite máximo de peças sugeridas por mês para evitar pedidos fora da realidade da loja.",
        )

        days_thresh = st.number_input(
            "Dias sem compra para alerta (Frequência)",
            min_value=30, max_value=365,
            value=int(st.session_state.get("cfg_days_threshold", DEFAULT_DAYS_WITHOUT_PURCHASE)),
            step=10,
        )

        receipt_window = st.number_input(
            "Janela de Recebimentos Recentes (Meses)",
            min_value=1, max_value=12,
            value=int(st.session_state.get("cfg_receipt_window_months", DEFAULT_RECEIPT_WINDOW_MONTHS)),
            step=1,
            help="Define o corte para considerar um produto sem novos recebimentos. Ex: Se 4 meses, alerta produtos cujo último recebimento foi há mais de 4 meses."
        )

        cov_rupt = st.number_input(
            "Cobertura mínima (ruptura) em meses",
            min_value=0.1, max_value=3.0,
            value=float(st.session_state.get("cfg_coverage_rupture", DEFAULT_COVERAGE_RUPTURE_THRESHOLD)),
            step=0.1,
        )

        cov_excess = st.number_input(
            "Cobertura máxima (excesso) em meses",
            min_value=2.0, max_value=12.0,
            value=float(st.session_state.get("cfg_coverage_excess", DEFAULT_COVERAGE_EXCESS_THRESHOLD)),
            step=0.5,
        )


        if st.button("💾 Salvar Parâmetros", type="primary"):
            st.session_state["cfg_lead_time_days"] = lead_time
            st.session_state["cfg_days_safety"] = safety_days
            st.session_state["cfg_monthly_capacity"] = monthly_capacity
            st.session_state["cfg_days_threshold"] = days_thresh
            st.session_state["cfg_receipt_window_months"] = receipt_window
            st.session_state["cfg_coverage_rupture"] = cov_rupt
            st.session_state["cfg_coverage_excess"] = cov_excess
            st.session_state["cfg_coverage_excess"] = cov_excess
            st.success("✅ Parâmetros salvos!")

    # ─── Tab 9: Pesos dos Algoritmos ───
    with tabs[8]:
        st.subheader("⚖️ Pesos dos Algoritmos")
        st.caption("Ajuste os pesos do motor de previsão.")

        weights = st.session_state.get("cfg_weights", DEFAULT_ALGORITHM_WEIGHTS.copy())
        w_data = [{"fator": k, "peso": v} for k, v in weights.items()]
        df_w = pd.DataFrame(w_data)
        edited_w = st.data_editor(df_w, use_container_width=True, key="weights_editor")

        total_w = edited_w["peso"].sum()
        if abs(total_w - 1.0) > 0.01:
            st.warning(f"⚠️ A soma dos pesos é {total_w:.2f}. Recomenda-se que seja 1.00.")

        col_w1, col_w2 = st.columns(2)
        with col_w1:
            if st.button("💾 Salvar Pesos", type="primary"):
                new_w = dict(zip(edited_w["fator"], edited_w["peso"]))
                st.session_state["cfg_weights"] = new_w
                st.success("✅ Pesos salvos!")
        with col_w2:
            if st.button("🔄 Restaurar Padrão", key="reset_weights"):
                st.session_state["cfg_weights"] = DEFAULT_ALGORITHM_WEIGHTS.copy()
                st.rerun()


if __name__ == "__main__":
    render()
