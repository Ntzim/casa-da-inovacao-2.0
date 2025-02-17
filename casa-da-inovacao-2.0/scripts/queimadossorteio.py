import streamlit as st
import pandas as pd
import random
from io import BytesIO

# Inicializar lista global de sorteados na session_state
if 'sorteados_geral' not in st.session_state:
    st.session_state.sorteados_geral = pd.DataFrame(columns=['Name', 'ID', 'Cota', 'Curso'])

# Função para realizar sorteio por grupo garantindo 27 ganhadores
def realizar_sorteio_por_grupo(df, quantidade_por_grupo, curso):
    total_vagas = 27  # Total fixo de vagas
    ganhadores_por_grupo = {}

    # Remover candidatos já sorteados
    df = df[~df[['Name', 'ID']].apply(tuple, axis=1).isin(
        st.session_state.sorteados_geral[['Name', 'ID']].apply(tuple, axis=1)
    )]

    # Separar ampla concorrência para uso posterior
    df_ampla_concorrencia = df[df['Cota'] == 'Ampla concorrência']

    # Sorteio inicial para cada grupo (exceto ampla concorrência)
    for grupo, quantidade in quantidade_por_grupo.items():
        if grupo == 'Ampla concorrência':
            continue  # Sortearemos ampla concorrência por último

        df_grupo = df[df['Cota'] == grupo]
        if not df_grupo.empty:
            sorteados = df_grupo.sample(n=min(quantidade, len(df_grupo)), random_state=random.randint(0, 10000))
            df = df.drop(sorteados.index)
            ganhadores_por_grupo[grupo] = sorteados

    # Garantir que vagas não preenchidas sejam ocupadas por ampla concorrência
    vagas_ocupadas = sum(len(ganhadores_por_grupo[g]) for g in ganhadores_por_grupo)
    vagas_restantes = total_vagas - vagas_ocupadas

    if vagas_restantes > 0 and not df_ampla_concorrencia.empty:
        sorteados_extra = df_ampla_concorrencia.sample(n=min(vagas_restantes, len(df_ampla_concorrencia)), random_state=random.randint(0, 10000))
        df_ampla_concorrencia = df_ampla_concorrencia.drop(sorteados_extra.index)
        ganhadores_por_grupo['Ampla concorrência'] = pd.concat([ganhadores_por_grupo.get('Ampla concorrência', pd.DataFrame()), sorteados_extra], ignore_index=True)

    # Unir os sorteados de todos os grupos
    ganhadores_df = pd.concat(ganhadores_por_grupo.values(), ignore_index=True)

    # Garantir exatamente 27 sorteados
    if len(ganhadores_df) < total_vagas and not df_ampla_concorrencia.empty:
        sorteados_extra = df_ampla_concorrencia.sample(n=total_vagas - len(ganhadores_df), random_state=random.randint(0, 10000))
        ganhadores_df = pd.concat([ganhadores_df, sorteados_extra], ignore_index=True)

    # Adicionar informações do curso e atualizar lista global de sorteados
    ganhadores_df['Curso'] = curso
    st.session_state.sorteados_geral = pd.concat([
        st.session_state.sorteados_geral, ganhadores_df[['Name', 'ID', 'Cota', 'Curso']]
    ], ignore_index=True).drop_duplicates(subset=['Name', 'ID'])

    return ganhadores_df

# Função para baixar o arquivo Excel
def baixar_excel(df, filename):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Ganhadores')
    processed_data = output.getvalue()
    return processed_data

# Configuração da aplicação
st.title("Sorteio Edital | Casa da Inovação")
st.image('casa-da-inovacao-2.0/imagens/ID_CASA_INOVACAO 1.png')

# Seletores de curso
curso_selecionado = st.selectbox("Selecione o curso", [
    "Programação de Aplicativos Teens – Idade: 12 – 17 anos | Turno: Tarde",
    "Criação de Games Kids – Idade: 8 - 14 anos | Turno: Manhã",
    "Criação de Games Kids – Idade: 8 - 14 anos | Turno: Tarde",
    "Criação de Games Teens – Idade: 15 - 29 anos | Turno: Tarde",
    "Inclusão Digital – Idade: 50+ | Turno: Manhã",
    "Inclusão Digital – Idade: 50+ | Turno: Tarde",
    "Introdução à Robótica Kids – Idade: 8 - 14 anos | Turno: Manhã",
    "Introdução à Robótica Kids – Idade: 8 - 14 anos | Turno: Tarde",
    "Introdução à Robótica Teens – Idade: 15 – 29 anos | Turno: Manhã",
    "Introdução ao Mundo Digital e Pacote Office – Idade: 18+ | Turno: Noite",
    "Marketing Digital – Idade: 18+ | Turno: Noite",
    "Digital Influencer – Idade: 15 – 29 anos | Turno: Tarde"
])

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    candidatos_ja_sorteados = df[df[['Name', 'ID']].apply(tuple, axis=1).isin(
        st.session_state.sorteados_geral[['Name', 'ID']].apply(tuple, axis=1)
    )]

    df = df[~df[['Name', 'ID']].apply(tuple, axis=1).isin(
        candidatos_ja_sorteados[['Name', 'ID']].apply(tuple, axis=1)
    )]

    if not candidatos_ja_sorteados.empty:
        lista_candidatos = "\n".join([f"ID: {row['ID']}, Nome: {row['Name']}" for index, row in candidatos_ja_sorteados.iterrows()])
        st.warning(f"Os seguintes candidatos já foram sorteados anteriormente e foram removidos:\n{lista_candidatos}")

    st.write(f"Primeiros registros do arquivo ({curso_selecionado}):")
    st.dataframe(df.head())

    quantidade_por_grupo = {
        'Ampla concorrência': 15,
        'Negro ou Pardo': 3,
        'Pessoa com deficiência - PCD': 3,
        'Estudante de escola pública': 3,
        'Beneficiário Socioassistencial': 3
    }

    if st.button(f"Realizar Sorteio para {curso_selecionado}"):
        ganhadores = realizar_sorteio_por_grupo(df, quantidade_por_grupo, curso_selecionado)
        if not ganhadores.empty:
            st.dataframe(ganhadores)
            excel_data = baixar_excel(ganhadores, 'ganhadores.xlsx')
            st.download_button("Baixar lista de ganhadores", data=excel_data, file_name=f'{curso_selecionado}_ganhadores.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    if st.button("Finalizar Sorteios e Baixar Lista Geral de Sorteados"):
        excel_data_geral = baixar_excel(st.session_state.sorteados_geral, 'sorteados_geral.xlsx')
        st.download_button("Baixar lista geral de sorteados", data=excel_data_geral, file_name='sorteados_geral.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        st.success("Lista geral de sorteados baixada com sucesso!")
