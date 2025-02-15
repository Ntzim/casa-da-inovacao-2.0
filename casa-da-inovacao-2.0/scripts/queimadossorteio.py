import streamlit as st
import pandas as pd
import random
from io import BytesIO

# Inicializar lista global de sorteados na session_state
if 'sorteados_geral' not in st.session_state:
    st.session_state.sorteados_geral = pd.DataFrame(columns=['Name', 'ID', 'Cota', 'Curso'])

# Função para realizar sorteio garantindo 27 sorteados únicos
def realizar_sorteio_por_grupo(df, quantidade_por_grupo, curso):
    ganhadores_por_grupo = {}
    total_vagas = 27

    # Remover candidatos já sorteados
    df = df[~df['ID'].isin(st.session_state.sorteados_geral['ID']) & ~df['Name'].isin(st.session_state.sorteados_geral['Name'])]

    for grupo, quantidade in quantidade_por_grupo.items():
        df_grupo = df[df['Cota'] == grupo]

        if not df_grupo.empty:
            sorteados = df_grupo.sample(n=min(quantidade, len(df_grupo)), random_state=random.randint(0, 10000))
            ganhadores_por_grupo[grupo] = sorteados
            df = df.drop(sorteados.index)
        else:
            ganhadores_por_grupo[grupo] = pd.DataFrame(columns=df.columns)
            st.warning(f"Grupo '{grupo}' sem candidatos suficientes. Vagas serão preenchidas por outros grupos.")

    ganhadores_df = pd.concat(ganhadores_por_grupo.values(), ignore_index=True)
    vagas_faltantes = total_vagas - len(ganhadores_df)

    # Preencher vagas faltantes com ampla concorrência ou outras cotas, se necessário
    while vagas_faltantes > 0:
        if not df.empty:
            sorteados_extra = df.sample(n=min(vagas_faltantes, len(df)), random_state=random.randint(0, 10000))
            ganhadores_df = pd.concat([ganhadores_df, sorteados_extra], ignore_index=True)
            df = df.drop(sorteados_extra.index)
            vagas_faltantes = total_vagas - len(ganhadores_df)
        else:
            st.warning(f"Não há candidatos suficientes para completar as {total_vagas} vagas para o curso {curso}.")
            break

    ganhadores_df['Curso'] = curso

    # Garantir que não há duplicatas antes de atualizar a lista geral
    st.session_state.sorteados_geral = pd.concat([
        st.session_state.sorteados_geral, ganhadores_df[['Name', 'ID', 'Cota', 'Curso']]
    ], ignore_index=True).drop_duplicates(subset=['ID', 'Name'])

    return ganhadores_df.drop_duplicates(subset=['ID', 'Name'])

# Função para baixar o arquivo Excel
def baixar_excel(df, filename):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Ganhadores')
    processed_data = output.getvalue()
    return processed_data

st.title("Sorteio Edital | Casa da Inovação")
st.image('casa-da-inovacao-2.0/imagens/ID_CASA_INOVACAO -2.png')

uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    cursos_disponiveis = df['Curso'].unique()
    curso_selecionado = st.selectbox("Selecione o curso", cursos_disponiveis)

    df = df[df['Curso'] == curso_selecionado]
    df = df[~df['ID'].isin(st.session_state.sorteados_geral['ID']) & ~df['Name'].isin(st.session_state.sorteados_geral['Name'])]

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
            st.write(f"**{curso_selecionado}** - Lista de ganhadores:")
            st.dataframe(ganhadores)
            
            excel_data = baixar_excel(ganhadores, 'ganhadores.xlsx')
            st.download_button(
                label="Baixar lista de ganhadores",
                data=excel_data,
                file_name=f'{curso_selecionado.replace(" | ", "_").replace(" ", "_")}_ganhadores.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            st.warning("Nenhum ganhador foi selecionado. Verifique se há candidatos nos grupos especificados.")

    if st.button("Finalizar Sorteios e Baixar Lista Geral de Sorteados"):
        excel_data_geral = baixar_excel(st.session_state.sorteados_geral, 'sorteados_geral.xlsx')
        st.download_button(
            label="Baixar lista geral de sorteados",
            data=excel_data_geral,
            file_name='sorteados_geral.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
