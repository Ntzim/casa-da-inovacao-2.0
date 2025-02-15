import streamlit as st
import pandas as pd
import random
from io import BytesIO

# Inicializar lista global de sorteados na session_state
if 'sorteados_geral' not in st.session_state:
    st.session_state.sorteados_geral = pd.DataFrame(columns=['Name', 'ID', 'Cota', 'Curso'])

# Função para realizar sorteio garantindo 27 sorteados únicos
def realizar_sorteio(df, curso):
    total_vagas = 27
    quantidade_por_grupo = {
        'Ampla concorrência': 15,
        'Negro ou Pardo': 3,
        'Pessoa com deficiência - PCD': 3,
        'Estudante de escola pública': 3,
        'Beneficiário Socioassistencial': 3
    }
    ganhadores = []

    # Remover candidatos já sorteados
    df = df[~df['ID'].isin(st.session_state.sorteados_geral['ID'])]
    df_ampla = df[df['Cota'] == 'Ampla concorrência']
    
    for grupo, qtd in quantidade_por_grupo.items():
        df_grupo = df[df['Cota'] == grupo]
        if not df_grupo.empty:
            sorteados = df_grupo.sample(n=min(qtd, len(df_grupo)), random_state=random.randint(0, 10000))
            ganhadores.append(sorteados)
            df = df.drop(sorteados.index)
        
    # Completar com ampla concorrência
    sorteados_df = pd.concat(ganhadores, ignore_index=True)
    vagas_faltantes = total_vagas - len(sorteados_df)
    if vagas_faltantes > 0 and not df_ampla.empty:
        extras = df_ampla.sample(n=min(vagas_faltantes, len(df_ampla)), random_state=random.randint(0, 10000))
        sorteados_df = pd.concat([sorteados_df, extras], ignore_index=True)

    # Atualizar lista global de sorteados
    sorteados_df['Curso'] = curso
    st.session_state.sorteados_geral = pd.concat([st.session_state.sorteados_geral, sorteados_df], ignore_index=True)
    return sorteados_df

# Função para baixar Excel
def baixar_excel(df, filename):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Ganhadores')
    return output.getvalue()

# Interface Streamlit
st.title("Sorteio Edital | Casa da Inovação")
st.image('../imagens/ID_CASA_INOVACAO 1.png')

curso_selecionado = st.selectbox("Selecione o curso", [
    "Programação de Aplicativos – Idade: 12 – 17 anos | Turno: Tarde",
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

uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    df = df[['Name', 'ID', 'Cota']]
    st.write("Primeiros registros do arquivo:")
    st.dataframe(df.head())
    
    if st.button(f"Realizar Sorteio para {curso_selecionado}"):
        ganhadores = realizar_sorteio(df, curso_selecionado)
        st.write(f"**{curso_selecionado}** - Lista de ganhadores:")
        st.dataframe(ganhadores)
        
        excel_data = baixar_excel(ganhadores, 'ganhadores.xlsx')
        st.download_button(
            label="Baixar lista de ganhadores",
            data=excel_data,
            file_name=f'{curso_selecionado.replace(" | ", "_").replace(" ", "_")}_ganhadores.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    if st.button("Finalizar Sorteios e Baixar Lista Geral de Sorteados"):
        excel_data_geral = baixar_excel(st.session_state.sorteados_geral, 'sorteados_geral.xlsx')
        st.download_button(
            label="Baixar lista geral de sorteados",
            data=excel_data_geral,
            file_name='sorteados_geral.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
