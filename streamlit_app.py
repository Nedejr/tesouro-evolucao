import streamlit as st
import pandas as pd
import math
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

import os

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Evolução Carteira do Tesouro Dashboard',
    page_icon=':earth_americas:', # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def lista_tesouro_totais():
    load_dotenv()
    cliente = MongoClient(f"mongodb+srv://{os.getenv('MONGO_DATABASE')}:{os.getenv('MONGO_PASSW')}@clustercontroleweb.dfrs4.mongodb.net/?retryWrites=true&w=majority&appName=ClusterControleWeb")
    database = cliente['db_controleweb']
    collection = database['Tesouro']
    
    df = pd.DataFrame(list(collection.find()))
    df = df.sort_values(by='Data')
    df_agrupado_dia = df.groupby('Data')['Posição Atual'].sum().reset_index()
    df_agrupado_dia['Lucro'] = df_agrupado_dia['Posição Atual'].diff().round(2).astype(str)
    df_agrupado_dia['Data'] = pd.to_datetime(df_agrupado_dia['Data'])
    df_agrupado_dia['Data'] = df_agrupado_dia['Data'].dt.strftime('%d/%m/%Y')


    lista = df['Titulo'].unique().tolist()
    df_total = pd.DataFrame()

    for ativo in lista:

        df1 = df.loc[df['Titulo']==ativo]
        df1.loc[:,['Lucro']] = df1['Posição Atual'].diff()
        #df1.loc[:,['Dif']] = df1['Unit'].diff()
        #df1.loc[:,['Rent%']] = df1['Unit'].pct_change() * 100
        #fig_tesouro = px.line(df1, x='Data', y='Lucro', color= 'Titulo',title='Tesouro no Período ' + ativo)
        #fig_tesouro.show()
        df_total = pd.concat([df_total, df1], axis=0)
        df1 = df1.loc[:,['Titulo','Lucro']].style.hide()
        #display(df1)
        
    return df_total
    
def get_gdp_data():
    """Grab GDP data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
    print(DATA_FILENAME)
    df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 1960
    MAX_YEAR = 2022

    # The data above has columns like:
    #_id
    #Titulo
    #Qtd
    #Posição Atual
    #Data


    # So let's pivot all those year-columns into two: Year and GDP
    gdp_df = df.melt(
        ['Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'GDP',
    )
    print(df)
    print(gdp_df)

    # Convert years from string to integers
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])

    return gdp_df

gdp_df = get_gdp_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :earth_americas: Evolução Tesouro Diário
Evolução diária da carteira Tesouro direto desde o dia 03/10/2024 até hoje.
'''

# Add some spacing
''
''

df_tesouro = lista_tesouro_totais()
print(df_tesouro['Data'].min())
print(df_tesouro['Data'].max())

min_value = gdp_df['Year'].min()
max_value = gdp_df['Year'].max()

# min_value = df_tesouro['Data'].min()
# max_value = df_tesouro['Data'].max()

from_year, to_year = st.slider(
    'Qual o período você tem interesse?',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value])

countries = gdp_df['Country Code'].unique()

if not len(countries):
    st.warning("Select at least one country")

selected_countries = st.multiselect(
    'Which countries would you like to view?',
    countries,
    ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'])

''
''
''

# Filter the data
filtered_gdp_df = gdp_df[
    (gdp_df['Country Code'].isin(selected_countries))
    & (gdp_df['Year'] <= to_year)
    & (from_year <= gdp_df['Year'])
]

st.header('GDP over time', divider='gray')

''

st.line_chart(
    filtered_gdp_df,
    x='Year',
    y='GDP',
    color='Country Code',
)

''
''


first_year = gdp_df[gdp_df['Year'] == from_year]
last_year = gdp_df[gdp_df['Year'] == to_year]

st.header(f'GDP in {to_year}', divider='gray')

''

cols = st.columns(4)

for i, country in enumerate(selected_countries):
    col = cols[i % len(cols)]

    with col:
        first_gdp = first_year[first_year['Country Code'] == country]['GDP'].iat[0] / 1000000000
        last_gdp = last_year[last_year['Country Code'] == country]['GDP'].iat[0] / 1000000000

        if math.isnan(first_gdp):
            growth = 'n/a'
            delta_color = 'off'
        else:
            growth = f'{last_gdp / first_gdp:,.2f}x'
            delta_color = 'normal'

        st.metric(
            label=f'{country} GDP',
            value=f'{last_gdp:,.0f}B',
            delta=growth,
            delta_color=delta_color
        )

