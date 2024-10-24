import streamlit as st
import pandas as pd
import random
from io import BytesIO

# Inicializar lista global de sorteados na session_state
if 'sorteados_geral' not in st.session_state:
    st.session_state.sorteados_geral = pd.DataFrame(columns=['Name', 'ID','Cota'])

# Função para realizar sorteio por grupo
def realizar_sorteio_por_grupo(df, quantidade_por_grupo, curso):
    ganhadores_por_grupo = {}

    # Filtra para ampla concorrência
    df_ampla_concorrencia = df[df['Cota'] == 'Ampla Concorrência']

    for grupo in quantidade_por_grupo.keys():
        if grupo == 'Ampla Concorrência':
            continue  # Deixamos o sorteio de ampla concorrência por último
        
        df_grupo = df[df['Cota'] == grupo]
        total_grupo = len(df_grupo)
        
        if total_grupo > 0:
            quantidade_real = min(quantidade_por_grupo[grupo], total_grupo)
            ganhadores = df_grupo.sample(n=quantidade_real, random_state=random.randint(0, 10000))
            
            # Se sobrar vagas, preenche com ampla concorrência
            if quantidade_real < quantidade_por_grupo[grupo]:
                vagas_restantes = quantidade_por_grupo[grupo] - quantidade_real
                total_ampla_concorrencia = len(df_ampla_concorrencia)
                
                if vagas_restantes > total_ampla_concorrencia:
                    vagas_restantes = total_ampla_concorrencia
                
                if vagas_restantes > 0:
                    ganhadores_extra = df_ampla_concorrencia.sample(n=vagas_restantes, random_state=random.randint(0, 10000))
                    df_ampla_concorrencia = df_ampla_concorrencia.drop(ganhadores_extra.index)
                    ganhadores = pd.concat([ganhadores, ganhadores_extra])
            
            ganhadores_por_grupo[grupo] = ganhadores
        else:
            st.warning(f"Não há candidatos no grupo '{grupo}'. Todas as vagas serão preenchidas pela ampla concorrência.")
            vagas_restantes = quantidade_por_grupo[grupo]
            total_ampla_concorrencia = len(df_ampla_concorrencia)
            
            if vagas_restantes > total_ampla_concorrencia:
                vagas_restantes = total_ampla_concorrencia
            
            if vagas_restantes > 0:
                ganhadores_extra = df_ampla_concorrencia.sample(n=vagas_restantes, random_state=random.randint(0, 10000))
                df_ampla_concorrencia = df_ampla_concorrencia.drop(ganhadores_extra.index)
                ganhadores_por_grupo[grupo] = ganhadores_extra
    
    # Sorteio de ampla concorrência com as vagas restantes
    if len(df_ampla_concorrencia) > 0 and quantidade_por_grupo['Ampla Concorrência'] > 0:
        total_ampla_concorrencia = len(df_ampla_concorrencia)
        quantidade_real = min(quantidade_por_grupo['Ampla Concorrência'], total_ampla_concorrencia)
        ganhadores_ampla = df_ampla_concorrencia.sample(n=quantidade_real, random_state=random.randint(0, 10000))
        ganhadores_por_grupo['Ampla Concorrência'] = ganhadores_ampla
    
    # Se ainda existirem vagas em aberto, sorteia entre os restantes
    vagas_em_aberto = sum(quantidade_por_grupo.values()) - sum([len(g) for g in ganhadores_por_grupo.values()])
    if vagas_em_aberto > 0:
        candidatos_restantes = df.drop(pd.concat(ganhadores_por_grupo.values()).index)
        if not candidatos_restantes.empty:
            ganhadores_aleatorios = candidatos_restantes.sample(n=vagas_em_aberto, random_state=random.randint(0, 10000))
            ganhadores_por_grupo['Restantes'] = ganhadores_aleatorios
    
    ganhadores_df = pd.concat(ganhadores_por_grupo.values())

    # Adiciona os ganhadores à lista global de sorteados
    ganhadores_df = ganhadores_df[['Name', 'ID','Cota']]
    ganhadores_df['Curso'] = curso
    st.session_state.sorteados_geral = pd.concat([st.session_state.sorteados_geral, ganhadores_df[['Name', 'ID','Cota']]])
    
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
st.image('casa-da-inovacao-2.0/imagens/ID_CASA_INOVACAO -2.png')

# Seletores de curso
curso_selecionado = st.selectbox("Selecione o curso", [
    'Criação de Aplicativos | Manhã',
    'Programação de Games | Teens | Manhã',
    'Introdução à Robótica | Kids | Manhã',
    'Inclusão Digital | +50 anos | Manhã',
    'Criação de Aplicativos | Tarde',
    'Programação de Games | Teens | Tarde',
    'Programação de Games | Kids | Tarde',
    'Digital Influencer | Tarde',
    'Introdução à Robótica | Kids | Tarde',
    'Introdução à Robótica | Teens | Tarde',
    'Introdução ao Mundo Digital e Pacote Office | Noite',
    'Marketing Digital | Noite',
])

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Leitura do arquivo Excel
    df = pd.read_excel(uploaded_file)
    
    # Verifica se algum candidato já foi sorteado
    # Verifica se algum candidato já foi sorteado (somente por 'Name' e 'ID')
    candidatos_ja_sorteados = df.merge(st.session_state.sorteados_geral[['Name', 'ID']], on=['Name', 'ID'], how='inner')
    df = df[~df[['Name', 'ID']].isin(candidatos_ja_sorteados[['Name', 'ID']].to_dict('list')).all(axis=1)]

    
    # Exibe aviso se algum candidato foi removido
    if not candidatos_ja_sorteados.empty:
        st.warning(f"Os seguintes candidatos já foram sorteados anteriormente e foram removidos deste sorteio:\n{candidatos_ja_sorteados[['Name', 'ID','Cota']].to_string(index=False)}")
    
    # Mostrar os primeiros registros do arquivo carregado
    st.write(f"Primeiros registros do arquivo ({curso_selecionado}):")
    st.dataframe(df.head())

    # Definição das quantidades de vagas por grupo
    if curso_selecionado in ['Programação de Games | Teens | Tarde', 'Programação de Games | Teens | Manhã', 'Introdução à Robótica | Teens | Tarde',
                             'Introdução à Robótica | Kids | Tarde']:
        quantidade_por_grupo = {
            'Ampla Concorrência': 30,
            'Negro ou Pardo': 6,
            'Pessoa com deficiência - PCD': 6,
            'Estudante de escola pública': 6,
            'Beneficiário Socioassistencial': 6
        }
    else:
        quantidade_por_grupo = {
            'Ampla Concorrência': 15,
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

            # Adicionar botão para baixar o Excel
            excel_data = baixar_excel(ganhadores, 'ganhadores.xlsx')
            st.download_button(
                label="Baixar lista de ganhadores",
                data=excel_data,
                file_name=f'{curso_selecionado.replace(" | ", "_").replace(" ", "_")}_ganhadores.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            st.warning("Nenhum ganhador foi selecionado. Verifique se há candidatos nos grupos especificados.")
    
    # Adicionar botão para baixar a lista geral de sorteados
if curso_selecionado == 'Marketing Digital | Noite':
    if st.button("Finalizar Sorteios e Baixar Lista Geral de Sorteados"):
        excel_data = baixar_excel(st.session_state.sorteados_geral, 'sorteados_geral.xlsx')
        st.download_button(
            label="Baixar lista geral de sorteados",
            data=excel_data,
            file_name='sorteados_geral.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
