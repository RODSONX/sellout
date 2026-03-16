"""
Página 8 — Manual do Sistema
Documentação técnica e guia de uso detalhado.
"""
import streamlit as st
import tema
from helpers import apply_professional_layout

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

def render():
    tema.aplicar_layout()
    st.header("📖 Manual do Sistema - Sell Out Intelligence")

    st.markdown("""
    Bem-vindo ao guia oficial do **Sell Out Intelligence**. Este documento foi projetado para fornecer transparência total sobre como o sistema processa dados, 
    calcula oportunidades e ajuda na gestão estratégica do seu mix de produtos.
    """)

    tabs = st.tabs([
        "📊 Dados & ETL", 
        "🖼️ Vitrine Estratégica",
        "👤 Gestão de Clientes",
        "🎯 Inteligência (Insights)",
        "📐 Fórmulas & Regras"
    ])

    # ──────────────────────────────────────────────
    # TAB 1 — DADOS & ETL
    # ──────────────────────────────────────────────
    with tabs[0]:
        st.subheader("📊 Fluxo de Dados e Processamento (ETL)")
        st.markdown("""
        O sistema opera através de um motor de ETL (Extract, Transform, Load) que unifica dados de diferentes fontes em um modelo de dados coerente.

        ### 1. Importação e Detecção
        - **Identificação do Período**: O sistema analisa as datas de venda e identifica o mês mais recente disponível. Este mês é definido como o "Mês de Referência".
        - **Separação de Blocos**: 
            - **Bloco Atual**: Dados do mês de referência (usados para o estoque atual).
            - **Bloco Histórico**: Dados dos meses anteriores (usados para calcular médias de giro e sazonalidade).

        ### 2. Tratamento de Arquivos
        Ao importar arquivos de Sell Out ou Inventário, o sistema limpa duplicatas, formata códigos de produtos para padrão universal (Pegada) e agrupa dados por cliente e referência.
        """)

    # ──────────────────────────────────────────────
    # TAB 2 — VITRINE ESTRATÉGICA
    # ──────────────────────────────────────────────
    with tabs[1]:
        st.subheader("🖼️ Vitrine de Coleção e Filtros")
        st.markdown("""
        A Vitrine é sua ferramenta visual de curadoria de mix. Ela organiza os produtos por **preço sugerido (PDV)** e performance.

        ### Funções de Busca e Filtro
        - **🔍 Busca Manual de Referência**: O campo central permite digitar partes do código do produto (ex: "110"). O grid filtra instantaneamente, facilitando encontrar modelos específicos sem navegar por listas longas.
        - **Filtros Laterais**: Você pode filtrar por Segmento, Linha, Gênero e Público.

        ### Sistema de Cores e Status
        Cada produto no grid possui um indicador visual no canto superior esquerdo:
        - 🟢 **Segue no Mix**: Itens com boa performance que devem ser mantidos.
        - 🟡 **Novos**: Lançamentos que estão entrando na coleção.
        - 🔵 **Bem Posicionado**: Itens que estão com o mix ideal naquela faixa de preço.
        - 🟠 **Verificar**: Itens com performance instável que exigem análise.
        - 🔴 **Fora de Linha / Retirar**: Itens que devem ser descontinuados ou removidos da vitrine.

        > [!TIP]
        > Clique no botão **＋** de cada card para selecionar produtos e aplicar status em massa usando os botões na barra lateral.
        """)

    # ──────────────────────────────────────────────
    # TAB 3 — GESTÃO DE CLIENTES
    # ──────────────────────────────────────────────
    with tabs[2]:
        st.subheader("👤 Visão Cliente e Dashboards")
        st.markdown("""
        Esta tela oferece um diagnóstico 360º de cada parceiro comercial.

        ### Gráficos Dinâmicos
        O sistema ajusta a visualização baseado no histórico do cliente:
        - **Gráfico de Linhas (Histórico > 1 mês)**: Mostra a evolução das Vendas vs Estoque ao longo dos meses. Ideal para ver se o estoque está crescendo rápido demais em relação à venda.
        - **Gráfico de Barras (Novo Cliente)**: Se o cliente tem apenas um mês de dados, o sistema mostra os totais absolutos de estoque e venda em barras simples.

        ### Grade de Performance por Segmento
        Exibe a variação percentual (MoM - Month over Month) das vendas e do estoque. 
        - **Cuidado**: Se a venda caiu (⬇️) e o estoque subiu (⬆️) no mesmo segmento, é um alerta de sobrestoque.

        ### Pedido Sugerido (Replenishment)
        Gera uma lista detalhada SKU por SKU com a sugestão de compra baseada no Forecast de demanda e no estoque atual.
        """)

    # ──────────────────────────────────────────────
    # TAB 4 — INTELIGÊNCIA (INSIGHTS)
    # ──────────────────────────────────────────────
    with tabs[3]:
        st.subheader("🎯 Insights Inteligentes (O Portfólio de 6 Módulos)")
        st.markdown("""
        O painel de Inteligência na tela de Oportunidades é o "cérebro" consultivo do sistema. Ele usa 6 modelos matemáticos para diagnosticar riscos.

        1. **🚩 Ruptura de Categorias**: Identifica onde o cliente tinha vendas históricas, mas hoje está com o estoque físico + trânsito zerado (vendas perdidas).
        2. **⚖️ Alerta de Mix Pobre**: Detecta categorias onde o cliente tem pouca variedade (1 ou 2 modelos), o que afasta o consumidor final.
        3. **🔥 Campeões com Risco**: Monitora os produtos que mais vendem. Se o estoque físico + recebimentos programados não cobrirem a demanda, ele sugere reposição.
        4. **🚚 Sazonalidade & Eventos**: Analisa o que o cliente já tem em estoque somado ao que está **programado para chegar antes** de datas sazonais (ex: Dia das Mães).
        5. **🕒 Histórico YoY (Year-over-Year)**: Compara o estoque (+ trânsito) atual com o que o cliente vendeu no mesmo mês do ano anterior.
        6. **🏆 Regra de Ouro Pareto (80/20)**: Lista os itens críticos que representam 80% do faturamento e estão com baixo estoque somado ao trânsito.
        """)

    # ──────────────────────────────────────────────
    # TAB 5 — FÓRMULAS E REGRAS
    # ──────────────────────────────────────────────
    with tabs[4]:
        st.subheader("📐 Fórmulas e Regras de Cálculo")
        st.markdown(r"""
        Para garantir a precisão, usamos as seguintes fórmulas matemáticas em todo o sistema:

        ### 1. Previsão de Demanda (Forecast)
        A demanda projetada para o próximo ciclo considera a média móvel ajustada por fatores sazonais:
        $$Demanda = \text{Média(3 meses)} \times \text{Fator Sazonal}$$

        ### 2. Venda Durante o Lead Time ($V_{LT}$)
        Calculamos quantos pares o cliente deve vender até que o novo pedido chegue à loja:
        $$V_{LT} = \left( \frac{Demanda}{30} \right) \times (LeadTimeDays + DiasSegurança)$$

        ### 3. Sugestão de Compra (Incluso Recebimento Programado)
        O pedido sugerido agora considera o equilíbrio entre a demanda e o que já está na loja ou previsto para entrar:
        $$Pedido = Demanda - (\text{Estoque Atual} + \text{Estoque em Trânsito})$$
        - **Estoque em Trânsito**: Volume identificado na planilha de entregas cujo mês seja igual ou superior ao mês atual.
        - **Cálculo Sazonal**: Para alertas de eventos, somamos apenas as entregas cujo mês seja **anterior** à data do evento.

        ### 4. Cobertura de Estoque
        Indica para quantos meses o estoque atual é suficiente:
        $$Cobertura = \frac{\text{Estoque Atual}}{Demanda}$$
        - **Meta Ideal**: Entre 1.5 e 2.5 meses de cobertura.
        """)
        
        st.info("💡 Todas as configurações de Lead Time, Sazonalidade e Mix Ideal podem ser ajustadas na aba de Configurações.")

if __name__ == "__main__":
    render()
