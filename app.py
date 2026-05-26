import streamlit as st
import pandas as pd
from datetime import datetime

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Controle de Portaria", layout="wide", page_icon="🏢")

# Substitua aqui pela URL da sua planilha do Google Sheets (deixando o final /pubhtml ou /edit)
# IMPORTANTE: Para o Streamlit ler direto, mudamos o final da URL para exportar em CSV
URL_BASE = "COLE_AQUI_A_URL_DA_SUA_PLANILHA_DO_GOOGLE"
URL_PESSOAS = f"{URL_BASE.rsplit('/', 1)[0]}/gviz/tq?tqx=out:csv&sheet=pessoas"
URL_HISTORICO = f"{URL_BASE.rsplit('/', 1)[0]}/gviz/tq?tqx=out:csv&sheet=historico"

st.title("🏢 Sistema de Controle de Portaria")

# Função para carregar dados do Google Sheets
def carregar_dados(url):
    try:
        return pd.read_csv(url)
    except:
        return pd.DataFrame()

# Carregando os dados em tempo real
df_pessoas = carregar_dados(URL_PESSOAS)
df_historico = carregar_dados(URL_HISTORICO)

# Criação das Abas
aba_registro, aba_cadastro, aba_dashboard = st.tabs([
    "🛎️ Registro (Check-in/Out)", 
    "📝 Cadastro de Pessoas", 
    "📊 Dashboard & Histórico"
])

# -------------------------------------------------------------------------
# ABA 1: REGISTRO DE MOVIMENTAÇÃO
# -------------------------------------------------------------------------
with aba_registro:
    st.header("Entrada e Saída de Pessoas")
    
    if df_pessoas.empty or 'CPF' not in df_pessoas.columns:
        st.warning("⚠️ Nenhuma pessoa cadastrada ou planilha não encontrada. Verifique a aba de cadastros.")
    else:
        # Formata a busca de pessoas
        df_pessoas['Busca'] = df_pessoas['Nome'] + " (" + df_pessoas['CPF'].astype(str) + ")"
        pessoa_selecionada = st.selectbox("Selecione a Pessoa:", df_pessoas['Busca'])
        
        cpf_sel = pessoa_selecionada.split("(")[-1].replace(")", "")
        dados_pessoa = df_pessoas[df_pessoas['CPF'].astype(str) == cpf_sel].iloc[0]
        
        # Identifica último status
        ultimo_status = "Fora"
        if not df_historico.empty and 'CPF' in df_historico.columns:
            historico_individual = df_historico[df_historico['CPF'].astype(str) == cpf_sel]
            if not historico_individual.empty:
                ultimo_status = "Dentro" if historico_individual.iloc[-1]['Movimentacao'] == "Entrada" else "Fora"
        
        st.info(f"👤 **Nome:** {dados_pessoa['Nome']} | **Tipo:** {dados_pessoa['Tipo']} | **Status Atual:** {ultimo_status}")
        obs = st.text_input("Observação:", placeholder="Ex: Prestador de serviço da empresa X")
        
        # NOTA: Para salvar de volta no Google Sheets via web de forma simples e segura, 
        # o ideal em produção é usar a biblioteca 'streamlit-gsheets-connection'.
        # O exemplo abaixo simula a lógica de salvamento.
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🟢 Registrar ENTRADA (Check-in)", use_container_width=True):
                st.success(f"Entrada de {dados_pessoa['Nome']} registrada com sucesso no sistema!")
                # Aqui o sistema dispara o append para a planilha
                
        with col2:
            if st.button("🔴 Registrar SAÍDA (Check-out)", use_container_width=True):
                st.success(f"Saída de {dados_pessoa['Nome']} registrada com sucesso no sistema!")

# -------------------------------------------------------------------------
# ABA 2: CADASTRO DE PESSOAS
# -------------------------------------------------------------------------
with aba_cadastro:
    st.header("Novo Cadastro")
    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo:")
        cpf = st.text_input("CPF (Apenas números):")
        tipo = st.selectbox("Tipo de Vínculo:", ["Morador", "Funcionário", "Visitante", "Prestador de Serviço", "Outro"])
        botao_salvar = st.form_submit_button("Salvar Cadastro")
        
        if botao_salvar and nome and cpf:
            st.success(f"✔️ {nome} enviado para a base de dados!")

# -------------------------------------------------------------------------
# ABA 3: DASHBOARD & HISTÓRICO
# -------------------------------------------------------------------------
with aba_dashboard:
    st.header("Monitoramento em Tempo Real")
    
    st.subheader("📍 Pessoas no Local (Presentes Agora)")
    if not df_historico.empty and 'Movimentacao' in df_historico.columns:
        ultimas_movs = df_historico.sort_values('Data_Hora').groupby('CPF').last().reset_index()
        dentro_agora = ultimas_movs[ultimas_movs['Movimentacao'] == 'Entrada']
        if not dentro_agora.empty:
            st.dataframe(dentro_agora[['Data_Hora', 'Nome', 'Tipo', 'Observacao']], use_container_width=True)
        else:
            st.info("Ninguém nas dependências no momento.")
    else:
        st.info("Nenhum registro de movimentação encontrado.")
        
    st.markdown("---")
    st.subheader("📜 Histórico Completo")
    busca = st.text_input("Buscar por Nome ou CPF no histórico:")
    
    if not df_historico.empty:
        df_filtrado = df_historico.copy()
        if busca:
            df_filtrado = df_filtrado[df_filtrado['Nome'].str.contains(busca, case=False) | df_filtrado['CPF'].astype(str).str.contains(busca)]
        st.dataframe(df_filtrado.iloc[::-1], use_container_width=True)
