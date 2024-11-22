import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path


st.set_page_config(
    page_title='Tesouro Direto - Dashboard',
    page_icon=':moneybag:',
    layout='wide',
)


@st.cache_data
def get_tesouro_csv():

    DATA_FILENAME = Path(__file__).parent / 'data/PrecoTaxaTesouroDireto.csv'
    df = pd.read_csv(DATA_FILENAME, sep=';')
    df['Data Vencimento'] = pd.to_datetime(df['Data Vencimento'], dayfirst=True)
    df['Data Base'] = pd.to_datetime(df['Data Base'], dayfirst=True)
    df['Taxa Compra Manha'] = df['Taxa Compra Manha'].str.replace('.', '')
    df['Taxa Compra Manha'] = df['Taxa Compra Manha'].str.replace(',', '.')
    df['Taxa Compra Manha'] = df['Taxa Compra Manha'].astype(float)
    df['PU Compra Manha'] = df['PU Compra Manha'].str.replace('.', '')
    df['PU Compra Manha'] = df['PU Compra Manha'].str.replace(',', '.')
    df['PU Compra Manha'] = df['PU Compra Manha'].astype(float)
    df.drop(labels='Taxa Venda Manha', axis=1, inplace=True)
    df.drop(labels='PU Venda Manha', axis=1, inplace=True)
    df.drop(labels='PU Base Manha', axis=1, inplace=True)
    df['Ano'] = df['Data Vencimento'].apply(lambda x: str(x.year))
    df['Tipo Titulo'] = df['Tipo Titulo'] + ' ' + df['Ano']
    df['Ano'] = df['Ano'].astype(str)
    df = df.rename(columns={'Taxa Compra Manha': 'Taxa', 'PU Compra Manha': 'Valor'})
    return df


def main():
    df_tesouro = get_tesouro_csv()
    '''
    # :moneybag: Histórico de Preços do Tesouro
    Consulte o histórico dos preços e taxas dos títulos públicos selecionando o nome do título e o período desejado.
    Base atualizada até o dia 19/11/2024.
    '''

    df_tesouro = df_tesouro.sort_values(by=['Tipo Titulo', 'Ano'], ascending=False)
    lista_titulos = df_tesouro['Tipo Titulo'].unique()

    f_titulos_selecionados = st.sidebar.multiselect(
        'Quais os títulos você gostaria de visualizar?',
        lista_titulos,
        placeholder='Selecione o Título',
        default=lista_titulos[0])

    df_titulo_selecionado = df_tesouro.loc[df_tesouro['Tipo Titulo'].isin(f_titulos_selecionados)]
    df_titulo_selecionado = df_titulo_selecionado.sort_values(by=['Tipo Titulo', 'Data Base'])

    min_value = df_titulo_selecionado['Data Base'].min()
    max_value = df_titulo_selecionado['Data Base'].max()

    if f_titulos_selecionados:

        f_data_selecionada = st.sidebar.date_input(
            'Selecioe o período de desejado?',
            min_value=min_value,
            max_value=max_value,
            value=[min_value, max_value],
            format='DD/MM/YYYY')
        try:
            data_inicial = f_data_selecionada[0].strftime('%Y-%m-%d')
            data_final = f_data_selecionada[1].strftime('%Y-%m-%d')
        except Exception:
            data_final = max_value

        f_preco_taxa = st.sidebar.selectbox('Selecione Preço ou Taxa', ['Valor (PU)', 'Taxa'])

        filtro_tesouro = df_titulo_selecionado.loc[
            (df_titulo_selecionado['Data Base'] >= data_inicial) & (df_titulo_selecionado['Data Base'] <= data_final)]
        ''
        ''
        st.header('Tesouro ao longo do tempo', divider='gray')
        ''
        fig_tesouro = px.line(filtro_tesouro,
                              x='Data Base',
                              y='Valor' if f_preco_taxa == 'Valor (PU)' else 'Taxa',
                              title='Tesouro ao longo do tempo',
                              color='Tipo Titulo',
                              markers=True,
                              hover_data={'Data Base': '|%d/%m/%Y'})

        st.plotly_chart(fig_tesouro, use_container_width=True)

        st.dataframe(filtro_tesouro, hide_index=True, use_container_width=True,
                        column_config={
                            "Valor": st.column_config.NumberColumn(
                                help="Valor P.U diário do Título",
                                format="R$ %.2f"),
                            "Taxa": st.column_config.NumberColumn(
                                help="Taxa diária do título",
                                format="%.2f",
                            ),
                            "Data Vencimento": st.column_config.DateColumn(
                                help="Data Vencimento",
                                format="DD/MM/YYYY",
                            ),
                            "Data Base": st.column_config.DateColumn(
                                help="Data Base",
                                format="DD/MM/YYYY",
                            )
                        }
                    )
    else:
        st.warning("Selecione pelo menos um título")


if __name__ == '__main__':
    main()
