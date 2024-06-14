import streamlit as st
import requests
import pandas as pd

# Función para obtener y procesar datos
@st.cache
def get_data():
    url = 'https://yields.llama.fi/pools'
    headers = {
        'accept': '*/*'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["data"])
        stable_df = df[df['stablecoin'] == True]
        stable_df_filtered = stable_df[['project', 'chain', 'symbol', 'apy', 'tvlUsd', 'apyMean30d', 'apyBase7d']]
        return stable_df_filtered
    else:
        st.error('Error fetching data')
        return pd.DataFrame()

# Obtener los datos
data = get_data()

# Sidebar filters
st.sidebar.header('Filtros')

# Filtro por proyecto
projects = st.sidebar.multiselect('Proyecto', options=data['project'].unique(), default=data['project'].unique())

# Filtro por cadena (chain)
chains = st.sidebar.multiselect('Chain', options=data['chain'].unique(), default=data['chain'].unique())

# Filtro por símbolo (contiene palabra)
symbol_filter = st.sidebar.text_input('Símbolo contiene', '')

# Filtro por APY
apy_min = st.sidebar.number_input('APY mínimo', min_value=float(data['apy'].min()), max_value=float(data['apy'].max()), value=float(data['apy'].min()))
apy_max = st.sidebar.number_input('APY máximo', min_value=float(data['apy'].min()), max_value=float(data['apy'].max()), value=float(data['apy'].max()))

# Filtro por TVL (USD)
tvl_min = st.sidebar.number_input('TVL mínimo (USD)', min_value=float(data['tvlUsd'].min()), max_value=float(data['tvlUsd'].max()), value=float(data['tvlUsd'].min()))
tvl_max = st.sidebar.number_input('TVL máximo (USD)', min_value=float(data['tvlUsd'].min()), max_value=float(data['tvlUsd'].max()), value=float(data['tvlUsd'].max()))

# Aplicar filtros
filtered_data = data[
    (data['project'].isin(projects)) &
    (data['chain'].isin(chains)) &
    (data['symbol'].str.contains(symbol_filter, case=False)) &
    (data['apy'] >= apy_min) &
    (data['apy'] <= apy_max) &
    (data['tvlUsd'] >= tvl_min) &
    (data['tvlUsd'] <= tvl_max)
]

# Mostrar datos filtrados
st.write('### Tabla de datos filtrados')
st.dataframe(filtered_data)

if __name__ == '__main__':
    st.write(filtered_data)
