import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA E ESTÉTICA DE TERMINAL ---
st.set_page_config(page_title="Painel de Controle - Operação e Margem", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; }
    h1, h2, h3, h4, p, label, .stMarkdown, .stTab { color: #E2E8F0 !important; }
    h1, h3 { color: #FFD700 !important; } 
    .stNumberInput > div > div > input { color: #FFD700 !important; background-color: #1E293B !important; border: 1px solid #FFD700 !important; }
    [data-testid="stMetricValue"] { color: #FFD700 !important; }
    .stDataFrame { background-color: #1E293B; }
    div[data-testid="stMetricDelta"] > div { font-size: 1.2rem !important; }
    .legenda-tatica { font-size: 0.85rem; color: #94a3b8; margin-top: -15px; display: block; line-height: 1.2; }
</style>
""", unsafe_allow_html=True)

st.title("Painel de Comando: Precificação Estratégica e Defesa de Caixa")
st.markdown("Insira os parâmetros operacionais. O motor financeiro recalcula a margem e a rentabilidade em tempo real.")

@st.cache_data
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSjH3b8-lsdDWGbw2xt5NYF-xZTmUBpeseXRaTyX4N-NTEsSreuwaP93GgQX8UV6A/pub?gid=272968961&single=true&output=csv"
    df_bruto = pd.read_csv(url)
    mask = df_bruto.apply(lambda row: row.astype(str).str.contains('Nome do produto', case=False, na=False).any(), axis=1)
    
    if mask.any():
        header_idx = mask.idxmax()
        df_bruto.columns = df_bruto.iloc[header_idx].astype(str).str.strip() 
        df_limpo = df_bruto.iloc[header_idx + 1:].reset_index(drop=True)
    else:
        df_limpo = df_bruto.copy()
        df_limpo.columns = df_limpo.columns.astype(str).str.strip()

    for col in df_limpo.columns:
        col_lower = col.lower()
        if 'produto' in col_lower and 'nome' in col_lower:
            df_limpo.rename(columns={col: 'Nome do produto'}, inplace=True)
        elif 'valor' in col_lower and 'produto' in col_lower:
            df_limpo.rename(columns={col: 'Valor do produto'}, inplace=True)
        elif 'fixo' in col_lower and 'unit' in col_lower:
            df_limpo.rename(columns={col: 'Custo Fixo Unitário'}, inplace=True)
            
    return df_limpo

try:
    df_base = carregar_dados()
except Exception as e:
    st.error(f"Falha de telemetria com a base de dados: {e}")
    st.stop()

def limpar_moeda(valor):
    if pd.isna(valor) or str(valor).strip().lower() in ['none', 'nan', '', '*']:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    v = str(valor).replace('R$', '').replace(' ', '')
    if '.' in v and ',' in v:
        v = v.replace('.', '').replace(',', '.')
    elif ',' in v:
        v = v.replace(',', '.')
    try:
        return float(v)
    except:
        return 0.0

# --- SINAIS VITAIS (ENTRADAS NUMÉRICAS REATIVAS) ---
st.markdown("### 🎛️ Calibração de Sinais Vitais")
col1, col2, col3 = st.columns(3)

with col1:
    carga_tributaria = st.number_input("Carga Tributária (%)", min_value=0.0, max_value=50.0, value=18.9, step=0.1, format="%.2f")
with col2:
    taxa_gateway = st.number_input("Taxa de Gateway / Cartão (%)", min_value=0.0, max_value=20.0, value=1.7, step=0.1, format="%.2f")
with col3:
    margem_liquida_alvo = st.number_input("Margem Líquida Alvo (%)", min_value=0.0, max_value=80.0, value=30.0, step=0.1, format="%.2f")

fator_deducao = (carga_tributaria + taxa_gateway + margem_liquida_alvo) / 100

tab1, tab2 = st.tabs(["🎯 Simulador de Cenários e Gráficos", "🗄️ Espelho da Planilha (Auditoria)"])

with tab1:
    if fator_deducao >= 1.0:
        st.error("⚠️ CÓDIGO AZUL: A soma de Impostos, Taxas e Margem atinge 100%. Sobrevivência matemática impossível.")
    else:
        df_simulacao = df_base.copy()
        
        if 'Valor do produto' in df_simulacao.columns:
            df_simulacao['Preço Praticado (Atual)'] = df_simulacao['Valor do produto'].apply(limpar_moeda)
        else:
            df_simulacao['Preço Praticado (Atual)'] = 0.0
            
        if 'Custo Fixo Unitário' in df_simulacao.columns:
            df_simulacao['Custo Base'] = df_simulacao['Custo Fixo Unitário'].apply(limpar_moeda)
        else:
            df_simulacao['Custo Base'] = 500.0 
            
        df_simulacao['Preço Ideal (Reativo)'] = df_simulacao['Custo Base'] / (1 - fator_deducao)
        df_simulacao['Custos Variáveis Atuais'] = df_simulacao['Preço Praticado (Atual)'] * ((carga_tributaria + taxa_gateway) / 100)
        df_simulacao['Margem de Contribuição (R$)'] = df_simulacao['Preço Praticado (Atual)'] - df_simulacao['Custos Variáveis Atuais']
        df_simulacao['Lucro Líquido Real (R$)'] = df_simulacao['Margem de Contribuição (R$)'] - df_simulacao['Custo Base']
        
        if 'Nome do produto' in df_simulacao.columns:
            df_valido = df_simulacao.dropna(subset=['Nome do produto']).copy()
            df_valido = df_valido[df_valido['Nome do produto'].str.strip() != ""]
            
            # --- HUD: PAINEL TÁTICO POR PRODUTO ---
            st.markdown("---")
            st.markdown("### 🛩️ HUD: Sinais Vitais por Produto")
            
            produto_selecionado = st.selectbox("Selecione o produto para auditar o raio-x financeiro:", df_valido['Nome do produto'].tolist())
            df_alvo = df_valido[df_valido['Nome do produto'] == produto_selecionado].iloc[0]
            
            hud_col1, hud_col2, hud_col3 = st.columns(3)
            
            with hud_col1:
                st.metric(
                    label="Preço Praticado / Alvo Ideal",
                    value=f"R$ {df_alvo['Preço Praticado (Atual)']:,.2f}",
                    delta=f"Alvo Ideal: R$ {df_alvo['Preço Ideal (Reativo)']:,.2f}",
                    delta_color="off"
                )
                st.markdown("<span class='legenda-tatica'>O valor menor é o praticado hoje. O Delta é o piso que garante a sobrevivência da operação.</span>", unsafe_allow_html=True)
            
            with hud_col2:
                st.metric(
                    label="TETO DO CAC (Custo de Aquisição Máximo)",
                    value=f"R$ {df_alvo['Margem de Contribuição (R$)']:,.2f}",
                    delta="Limite Máximo Seguro",
                    delta_color="normal"
                )
                st.markdown("<span class='legenda-tatica'>Se o tráfego gastar mais do que isso para converter, a escola queima caixa instantaneamente.</span>", unsafe_allow_html=True)
                
            with hud_col3:
                lucro_real = df_alvo['Lucro Líquido Real (R$)']
                st.metric(
                    label="Lucro Líquido Real (Por Matrícula)",
                    value=f"R$ {lucro_real:,.2f}",
                    delta="OPERAÇÃO SANGRA CAIXA" if lucro_real < 0 else "GERAÇÃO DE CAIXA POSITIVA",
                    delta_color="inverse" if lucro_real < 0 else "normal"
                )
                st.markdown("<span class='legenda-tatica'>Valores negativos indicam que o dono está pagando do próprio bolso para o aluno estudar.</span>", unsafe_allow_html=True)

            # --- GRÁFICOS VISUAIS ---
            df_plot = df_valido.head(10)
            
            st.markdown("---")
            st.markdown("### 📈 Diagnóstico de Preço: Praticado vs. Ideal (Sobrevivência)")
            
            fig1 = px.bar(
                df_plot, x='Nome do produto', y=['Preço Praticado (Atual)', 'Preço Ideal (Reativo)'],
                barmode='group', color_discrete_map={'Preço Praticado (Atual)': '#ef4444', 'Preço Ideal (Reativo)': '#3b82f6'}
            )
            
            fig1.update_traces(texttemplate='R$ %{y:,.2f}', textposition='outside', textfont=dict(color="#E2E8F0"))
            fig1.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#E2E8F0"),
                legend=dict(title="Cenário", font=dict(color="#FFD700"), bgcolor="rgba(0,0,0,0)"),
                xaxis_tickangle=-25, xaxis_title="", yaxis_title="Valor (R$)", height=500, margin=dict(t=30)
            )
            st.plotly_chart(fig1, use_container_width=True)

            st.markdown("---")
            st.markdown("### 🧬 Radiografia de Rentabilidade: Contribuição vs. Lucro Líquido Real")
            st.markdown("A barra amarela sustenta a operação. A barra ao lado (verde/vermelha) dita se a escola lucra ou paga para trabalhar.")
            
            fig2 = go.Figure()
            
            fig2.add_trace(go.Bar(
                x=df_plot['Nome do produto'],
                y=df_plot['Margem de Contribuição (R$)'],
                name='Margem de Contribuição (R$)',
                marker_color='#FFD700', 
                text=df_plot['Margem de Contribuição (R$)'],
                texttemplate='R$ %{text:,.2f}', textposition='outside', textfont=dict(color="#FFD700")
            ))
            
            fig2.add_trace(go.Bar(
                x=df_plot['Nome do produto'],
                y=df_plot['Lucro Líquido Real (R$)'],
                name='Lucro Líquido Real (R$)',
                marker_color=['#10b981' if val >= 0 else '#ef4444' for val in df_plot['Lucro Líquido Real (R$)']],
                text=df_plot['Lucro Líquido Real (R$)'],
                texttemplate='R$ %{text:,.2f}', textposition='outside', textfont=dict(color="#E2E8F0")
            ))
            
            fig2.update_layout(
                barmode='group', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#E2E8F0"),
                legend=dict(font=dict(color="#E2E8F0"), bgcolor="rgba(0,0,0,0)"),
                xaxis_tickangle=-25, xaxis_title="", yaxis_title="Rentabilidade (R$)", height=550, margin=dict(t=30)
            )
            st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.markdown("### 🗄️ Auditoria da Base de Dados")
    st.dataframe(df_base, use_container_width=True)