import streamlit as st
import pandas as pd
import random
from io import BytesIO

# Inicializar lista global de sorteados na session_state
if 'sorteados_geral' not in st.session_state:
    st.session_state.sorteados_geral = pd.DataFrame(columns=['Name', 'ID', 'Cota', 'Curso'])

# Função para realizar sorteio por grupo com verificação rigorosa de duplicados
def realizar_sorteio_por_grupo(df, quantidade_por_grupo, curso):
    ganhadores_por_grupo = {}
    total_vagas = sum(quantidade_por_grupo.values())

    # Remover candidatos já sorteados (verificando por 'Name' e 'ID')
    df = df[~df[['Name', 'ID']].apply(tuple, axis=1).isin(
        st.session_state.sorteados_geral[['Name', 'ID']].apply(tuple, axis=1)
    )]

    # Separar ampla concorrência para uso posterior
    df_ampla_concorrencia = df[df['Cota'] == 'Ampla concorrência']

    # Sorteio inicial para cada grupo
    for grupo, quantidade in quantidade_por_grupo.items():
        df_grupo = df[df['Cota'] == grupo]
        
        if not df_grupo.empty:
            quantidade_real = min(quantidade, len(df_grupo))
            sorteados = df_grupo.sample(n=quantidade_real, random_state=random.randint(0, 10000))
            ganhadores_por_grupo[grupo] = sorteados
            # Remover os sorteados do pool geral
            df = df.drop(sorteados.index)
        else:
            ganhadores_por_grupo[grupo] = pd.DataFrame(columns=df.columns)
            st.warning(f"Grupo '{grupo}' sem candidatos suficientes. Vagas serão preenchidas pela ampla concorrência.")

    # Garantir o preenchimento das vagas não ocupadas com ampla concorrência
    for grupo, quantidade in quantidade_por_grupo.items():
        sorteados_no_grupo = ganhadores_por_grupo[grupo]
        vagas_restantes = quantidade - len(sorteados_no_grupo)

        if vagas_restantes > 0 and not df_ampla_concorrencia.empty:
            sorteados_extra = df_ampla_concorrencia.sample(n=min(vagas_restantes, len(df_ampla_concorrencia)), random_state=random.randint(0, 10000))
            df_ampla_concorrencia = df_ampla_concorrencia.drop(sorteados_extra.index)
            ganhadores_por_grupo[grupo] = pd.concat([sorteados_no_grupo, sorteados_extra])

    # Unir os sorteados de todos os grupos
    ganhadores_df = pd.concat(ganhadores_por_grupo.values(), ignore_index=True)

    # Garantir o preenchimento até atingir o total de vagas
    vagas_faltantes = total_vagas - len(ganhadores_df)
    if vagas_faltantes > 0 and not df_ampla_concorrencia.empty:
        sorteados_extra = df_ampla_concorrencia.sample(n=min(vagas_faltantes, len(df_ampla_concorrencia)), random_state=random.randint(0, 10000))
        ganhadores_df = pd.concat([ganhadores_df, sorteados_extra], ignore_index=True)

    # Adicionar informações do curso e atualizar a lista global de sorteados
    ganhadores_df['Curso'] = curso
    st.session_state.sorteados_geral = pd.concat(
        [st.session_state.sorteados_geral, ganhadores_df[['Name', 'ID', 'Cota', 'Curso']]], 
        ignore_index=True
    ).drop_duplicates(subset=['Name', 'ID'])  # Verifica duplicados por 'Name' e 'ID'

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
    'Programação de Aplicativos Teens – Idade: 12 – 17 anos | Turno: Tarde',
    'Programação de Aplicativos – Idade: 18+ | Turno: Tarde',
    'Criação de Games kids – Idade: 8 -14 anos| Turno: Manhã',
    'Criação de Games kids – Idade: 8 -14 anos | Turno: Tarde',
    'Criação de Games teens – Idade: 15 - 29 anos| Turno: Tarde',
    'Inclusão Digital – Idade: 50+ | Turno: Manhã',
    'Introdução à Robótica kids – Idade: kids 8 -14 | Turno: Manhã',
    'Introdução à Robótica kids – Idade: 8 -14 | Turno: Tarde',
    'Introdução à Robótica teens – Idade: 15 – 29 anos | Turno: Manhã',
    'Introdução ao Mundo Digital e Pacote Office – Idade: 18 + | Turno: Noite',
    'Marketing Digital – Idade: 18+ | Turno: Noite',
    'Digital Influencer– Idade: 15 – 29 anos | Turno: Tarde',
])

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Leitura do arquivo Excel
    df = pd.read_excel(uploaded_file)
    
    # Verifica se algum candidato já foi sorteado (apenas pelo 'Name' e 'ID')
    candidatos_ja_sorteados = df[df[['Name', 'ID']].apply(tuple, axis=1).isin(
        st.session_state.sorteados_geral[['Name', 'ID']].apply(tuple, axis=1)
    )]

    # Remove os candidatos já sorteados do DataFrame original
    df = df[~df[['Name', 'ID']].apply(tuple, axis=1).isin(
        candidatos_ja_sorteados[['Name', 'ID']].apply(tuple, axis=1)
    )]

    # Exibe aviso se algum candidato foi removido
    if not candidatos_ja_sorteados.empty:
        lista_candidatos = "\n".join([f"ID: {row['ID']}, Nome: {row['Name']}" for _, row in candidatos_ja_sorteados.iterrows()])
        st.warning(f"Os seguintes candidatos já foram sorteados e foram removidos: \n{lista_candidatos}")

    # Mostrar os primeiros registros do arquivo carregado
    st.write(f"Primeiros registros do arquivo ({curso_selecionado}):")
    st.dataframe(df.head())

    # Definição das quantidades de vagas por grupo
    quantidade_por_grupo = {
        'Ampla concorrência': 15,
        'Negro ou Pardo': 3,
        'Pessoa com deficiência - PCD': 3,
        'Estudante de escola pública': 3,
        'Beneficiário Socioassistencial': 3
    }
    
    # Botão para realizar o sorteio
    if st.button(f"Realizar Sorteio para {curso_selecionado}"):
        ganhadores = realizar_sorteio_por_grupo(df, quantidade_por_grupo, curso_selecionado)
        
        if not ganhadores.empty:
            st.write(f"**{curso_selecionado}** - Lista de ganhadores:")
            st.dataframe(ganhadores)

            # Adicionar botão para baixar o Excel dos ganhadores do curso atual
            excel_data = baixar_excel(ganhadores, 'ganhadores.xlsx')
            st.download_button(
                label="Baixar lista de ganhadores",
                data=excel_data,
                file_name=f'{curso_selecionado.replace(" | ", "_").replace(" ", "_")}_ganhadores.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            st.warning("Nenhum ganhador foi selecionado. Verifique se há candidatos nos grupos especificados.")
    
    # Botão para baixar a lista geral de sorteados
    if st.button("Finalizar Sorteios e Baixar Lista Geral de Sorteados"):
        excel_data_geral = baixar_excel(st.session_state.sorteados_geral, 'sorteados_geral.xlsx')
        st.download_button(
            label="Baixar lista geral de sorteados",
            data=excel_data_geral,
            file_name='sorteados_geral.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
