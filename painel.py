import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================================
# 1. CONFIGURAÇÃO DA PÁGINA (DEVE SER A PRIMEIRA LINHA)
# ==========================================================
st.set_page_config(page_title="Painel de Comando - Operação e Margem", layout="wide", initial_sidebar_state="expanded")

# ==========================================================
# 2. SISTEMA DE AUTENTICAÇÃO BLINDADO (BARREIRA LINEAR)
# ==========================================================
VALID_USERS = {
    "pedro": "An@140919",
    "consultora": "Amand@2026"
}

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #0f172a;'>🔒 Acesso Restrito - Diretoria</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #334155;'>Painel Estratégico de Margem e Precificação</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuário").strip().lower()
            password = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar no Painel", use_container_width=True)
            
            if submit:
                if username in VALID_USERS and password == VALID_USERS[username]:
                    st.session_state["autenticado"] = True
                    st.rerun() 
                else:
                    st.error("Usuário ou senha incorretos. Acesso negado.")
    
    st.stop()

# ==========================================================
# 3. CORPO DO PAINEL (SÓ RODA SE A BARREIRA FOR VENCIDA)
# ==========================================================

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; }
    [data-testid="stHeader"] { background-color: #0b0f19 !important; }
    [data-testid="stSidebar"] { background-color: #111827 !important; }
    h1, h2, h3, h4, p, label, .stMarkdown, .stTab, span { color: #E2E8F0 !important; }
    h1, h3 { color: #FFD700 !important; } 
    
    .stNumberInput > div > div > input { 
        color: #FFD700 !important; 
        background-color: #1E293B !important; 
        border: 1px solid #1E293B !important; 
        transition: all 0.4s ease-in-out;
    }
    .stNumberInput > div > div > input:focus {
        border: 1px solid #FFD700 !important; 
        box-shadow: 0 0 8px rgba(255, 215, 0, 0.2) !important;
    }
    
    [data-testid="stMetricValue"] { color: #FFD700 !important; }
    div[data-testid="stMetricDelta"] > div { font-size: 1.2rem !important; }
    
    .stDataFrame { background-color: #1E293B; }
    
    .stButton > button { 
        background-color: #1E293B !important; 
        color: #FFD700 !important; 
        border: 1px solid #FFD700 !important; 
        font-weight: bold;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stButton > button:hover { 
        background-color: #FFD700 !important; 
        color: #0b0f19 !important; 
        border: 1px solid #FFD700 !important;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🛡️ Painel do Mentor")
    st.write("Conectado como: **Diretoria**")
    st.markdown("---")
    
    if st.button("🔒 Encerrar Sessão (Logout)", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()
        
    st.markdown("---")
    st.markdown("### 🎛️ Calibração de Sinais Vitais")
    carga_tributaria = st.number_input("Carga Tributária (%)", min_value=0.0, max_value=50.0, value=18.9, step=0.1, format="%.2f")
    taxa_gateway = st.number_input("Taxa de Gateway / Cartão (%)", min_value=0.0, max_value=20.0, value=1.7, step=0.1, format="%.2f")
    desconto_aplicado = st.number_input("Desconto Aplicado (%)", min_value=0.0, max_value=99.0, value=0.0, step=0.1, format="%.2f", help="Qualquer desconto dado corrói a base de cálculo. O motor vai recalcular o impacto.")
    margem_liquida_alvo = st.number_input("Margem Líquida Alvo (%)", min_value=0.0, max_value=80.0, value=30.0, step=0.1, format="%.2f")

st.title("Painel de Comando: Precificação Estratégica e Defesa de Caixa")
st.markdown("Insira os parâmetros operacionais na barra lateral. O motor financeiro recalcula a margem e a rentabilidade em tempo real sobre a base da planilha.")

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

# ==========================================================
# 4. MOTOR FINANCEIRO (CÁLCULOS DINÂMICOS)
# ==========================================================

fator_deducao_ideal = (carga_tributaria + taxa_gateway + margem_liquida_alvo + desconto_aplicado) / 100

tab1, tab2 = st.tabs(["🎯 Simulador de Cenários e Gráficos", "🗄️ Espelho da Planilha (Auditoria)"])

with tab1:
    if fator_deducao_ideal >= 1.0:
        st.error("⚠️ CÓDIGO AZUL: A soma de Impostos, Taxas, Margem e Desconto ultrapassa 100%. O Preço Ideal tende ao infinito (Falência Matemática).")
    else:
        df_simulacao = df_base.copy()
        
        # Resgatando a Base Real da Planilha
        if 'Valor do produto' in df_simulacao.columns:
            df_simulacao['Valor do Produto'] = df_simulacao['Valor do produto'].apply(limpar_moeda)
        else:
            df_simulacao['Valor do Produto'] = 0.0
            
        if 'Custo Fixo Unitário' in df_simulacao.columns:
            df_simulacao['Custo Base'] = df_simulacao['Custo Fixo Unitário'].apply(limpar_moeda)
        else:
            df_simulacao['Custo Base'] = 500.0 
            
        # O impacto direto das variáveis no cenário projetado
        df_simulacao['Preço Ideal'] = df_simulacao['Custo Base'] / (1 - fator_deducao_ideal)
        
        # O impacto real e atual: Aplicando o Desconto no Valor do Produto que eles já cobram hoje
        df_simulacao['Receita Efetiva (Atual)'] = df_simulacao['Valor do Produto'] * (1 - (desconto_aplicado / 100))
        df_simulacao['Custos Variáveis Atuais'] = df_simulacao['Receita Efetiva (Atual)'] * ((carga_tributaria + taxa_gateway) / 100)
        
        # Métricas vitais impactadas
        df_simulacao['Margem de Contribuição (R$)'] = df_simulacao['Receita Efetiva (Atual)'] - df_simulacao['Custos Variáveis Atuais']
        df_simulacao['Lucro Líquido Real (R$)'] = df_simulacao['Margem de Contribuição (R$)'] - df_simulacao['Custo Base']
        
        if 'Nome do produto' in df_simulacao.columns:
            df_valido = df_simulacao.dropna(subset=['Nome do produto']).copy()
            df_valido = df_valido[df_valido['Nome do produto'].str.strip() != ""]
            
            st.markdown("---")
            st.markdown("### 🛩️ HUD: Sinais Vitais por Produto")
            
            produto_selecionado = st.selectbox("Selecione o produto para auditar o raio-x financeiro:", df_valido['Nome do produto'].tolist())
            df_alvo = df_valido[df_valido['Nome do produto'] == produto_selecionado].iloc[0]
            
            hud_col1, hud_col2, hud_col3 = st.columns(3)
            
            with hud_col1:
                st.metric(
                    label="Valor do Produto / Preço Ideal",
                    value=f"R$ {df_alvo['Valor do Produto']:,.2f}",
                    delta=f"Preço Ideal: R$ {df_alvo['Preço Ideal']:,.2f}",
                    delta_color="off"
                )
            
            with hud_col2:
                st.metric(
                    label="TETO DO CAC (Margem de Contribuição)",
                    value=f"R$ {df_alvo['Margem de Contribuição (R$)']:,.2f}",
                    delta="Limite Máximo Seguro p/ Aquisição",
                    delta_color="normal"
                )
                
            with hud_col3:
                lucro_real = df_alvo['Lucro Líquido Real (R$)']
                st.metric(
                    label="Lucro Líquido Real (Por Matrícula)",
                    value=f"R$ {lucro_real:,.2f}",
                    delta="OPERAÇÃO SANGRA CAIXA" if lucro_real < 0 else "GERAÇÃO DE CAIXA POSITIVA",
                    delta_color="inverse" if lucro_real < 0 else "normal"
                )

            df_plot = df_valido.head(10)
            
            st.markdown("---")
            st.markdown("### 📈 Diagnóstico de Precificação (Impacto das Variáveis no Preço Ideal)")
            
            fig1 = px.bar(
                df_plot, x='Nome do produto', y=['Valor do Produto', 'Preço Ideal'],
                barmode='group', color_discrete_map={'Valor do Produto': '#ef4444', 'Preço Ideal': '#3b82f6'}
            )
            
            fig1.update_traces(texttemplate='R$ %{y:,.2f}', textposition='outside', textfont=dict(color="#E2E8F0"))
            fig1.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#E2E8F0"),
                legend=dict(title="Cenário", font=dict(color="#FFD700"), bgcolor="rgba(0,0,0,0)"),
                xaxis_tickangle=-25, xaxis_title="", yaxis_title="Valor (R$)", height=500, margin=dict(t=30),
                uirevision='constant', 
                transition=dict(duration=500, easing="sin-in-out") 
            )
            st.plotly_chart(fig1, use_container_width=True)

            st.markdown("---")
            st.markdown("### 🧬 Radiografia de Rentabilidade (Impacto em Tempo Real)")
            
            fig2 = go.Figure()
            
            fig2.add_trace(go.Bar(
                x=df_plot['Nome do produto'],
                y=df_plot['Margem de Contribuição (R$)'],
                name='Teto do CAC (Margem Contrib.)',
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
                xaxis_tickangle=-25, xaxis_title="", yaxis_title="Rentabilidade (R$)", height=550, margin=dict(t=30),
                uirevision='constant', 
                transition=dict(duration=500, easing="sin-in-out") 
            )
            st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.markdown("### 🗄️ Auditoria da Base de Dados")
    st.dataframe(df_base, use_container_width=True)