# Sorteio Edital | Casa da Inovação
Este é um aplicativo em Python desenvolvido com o Streamlit para realizar sorteios de candidatos para cursos variados, seguindo regras específicas de cotas, além de possibilitar a exclusão de candidatos previamente sorteados em outros cursos.

## Funcionalidades
1 - Upload de Arquivo: Permite carregar um arquivo Excel com a lista de candidatos.


2 - Sorteio com Cotas: Realiza sorteios divididos em grupos de cotas (Ampla Concorrência, Negro ou Pardo, PCD, Escola Pública, Beneficiário Socioassistencial).


3 - Controle de Duplicidade: Candidatos sorteados em qualquer curso anterior são automaticamente excluídos do sorteio para outro curso.


4 - Download de Resultados: Possibilita o download da lista de ganhadores por curso e a lista geral de sorteados.


# Estrutura de Uso
1 - Selecionar o Curso: Escolha o curso para o sorteio.


2 - Carregar Lista de Candidatos: Faça o upload do arquivo Excel com os candidatos.


3 - Realizar o Sorteio: Clique no botão para sortear os ganhadores do curso selecionado, respeitando as quantidades de vagas por cota.


4 -Baixar Listas: Ao final do sorteio, faça o download da lista de ganhadores do curso e/ou da lista geral de sorteados.
# Requisitos
Python 3.8+
Bibliotecas: Streamlit, Pandas, openpyxl, XlsxWriter
Para rodar o aplicativo localmente:

bash
Copiar código
pip install streamlit pandas openpyxl xlsxwriter
streamlit run script.py
# Observações
Os candidatos excluídos por já terem sido sorteados em outros cursos são exibidos como aviso.
O script garante 27 sorteados por curso, preenchendo vagas faltantes com ampla concorrência, se necessário.
