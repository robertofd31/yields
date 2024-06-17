import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Función para obtener y procesar datos
def get_data():
    url = 'https://yields.llama.fi/pools'
    headers = {'accept': '*/*'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["data"])
        stable_df = df[df['stablecoin'] == True]
        stable_df_filtered = stable_df[['project', 'chain', 'symbol', 'apy', 'tvlUsd', 'apyMean30d', 'pool']]
        return stable_df_filtered
    else:
        st.error('Error fetching data')
        return pd.DataFrame()

# Obtener los datos
if 'data' not in st.session_state:
    st.session_state.data = get_data()

# Sidebar filters
st.sidebar.header('Filtros')

# Resto del código para filtrar y mostrar datos...


# Filtro por proyecto
projects = st.sidebar.selectbox('Proyecto', options=["Todos"] + list(data['project'].unique()))

# Filtro por cadena (chain)
chains = st.sidebar.selectbox('Chain', options=["Todos"] + list(data['chain'].unique()))

# Filtro por símbolo (contiene palabra)
symbol_filter = st.sidebar.text_input('Símbolo contiene', '')

# Filtro por APY (enteros, incremento de 1)
apy_min = st.sidebar.number_input('APY mínimo', min_value=int(data['apy'].min()), max_value=int(data['apy'].max()), value=int(data['apy'].min()), step=1)
apy_max = st.sidebar.number_input('APY máximo', min_value=int(data['apy'].min()), max_value=int(data['apy'].max()), value=int(data['apy'].max()), step=1)

# Filtro por TVL (USD) (enteros, incremento de 5000)
tvl_min = st.sidebar.number_input('TVL mínimo (USD)', min_value=int(data['tvlUsd'].min()), max_value=int(data['tvlUsd'].max()), value=int(data['tvlUsd'].min()), step=5000)
tvl_max = st.sidebar.number_input('TVL máximo (USD)', min_value=int(data['tvlUsd'].min()), max_value=int(data['tvlUsd'].max()), value=int(data['tvlUsd'].max()), step=5000)

# Aplicar filtros
filtered_data = data[
    ((data['project'] == projects) if projects != "Todos" else True) &
    ((data['chain'] == chains) if chains != "Todos" else True) &
    (data['symbol'].str.contains(symbol_filter, case=False)) &
    (data['apy'] >= apy_min) &
    (data['apy'] <= apy_max) &
    (data['tvlUsd'] >= tvl_min) &
    (data['tvlUsd'] <= tvl_max)
]

# Mostrar datos filtrados
st.write('### Tabla de datos filtrados')
st.dataframe(filtered_data)

# Input para el ID de la pool
pool_id = st.text_input('Ingresa el ID de la pool', '')

# Función para manejar la selección de filas en la tabla
def show_pool_data(pool_id):
    pool_data = get_pool_data(pool_id)
    if not pool_data.empty:
        pool_data['timestamp'] = pd.to_datetime(pool_data['timestamp'])
        pool_data.set_index('timestamp', inplace=True)

        fig, ax1 = plt.subplots()

        color = 'tab:blue'
        ax1.set_xlabel('Fecha')
        ax1.set_ylabel('APY', color=color)
        ax1.plot(pool_data.index, pool_data['apy'], color=color)
        ax1.tick_params(axis='y', labelcolor=color)

        ax2 = ax1.twinx()
        color = 'tab:red'
        ax2.set_ylabel('TVL (USD)', color=color)
        ax2.plot(pool_data.index, pool_data['tvlUsd'], color=color)
        ax2.tick_params(axis='y', labelcolor=color)

        fig.tight_layout()
        st.pyplot(fig)

# Mostrar datos de la pool si se ingresa un ID
if pool_id:
    st.write(f"Datos de la pool: {pool_id}")
    show_pool_data(pool_id)
