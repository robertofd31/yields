import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import re
from bs4 import BeautifulSoup

# Configuración inicial de la aplicación
st.set_page_config(page_title="Streamlit App", layout="wide")

# Define páginas
def main_page():
    st.title("Página Principal")

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

    # Función para obtener datos de la pool
    def get_pool_data(pool_id):
        url = f'https://yields.llama.fi/chart/{pool_id}'
        headers = {'accept': '*/*'}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data['data'])
        else:
            st.error('Error fetching pool data')
            return pd.DataFrame()

    # Obtener los datos
    if 'data' not in st.session_state:
        st.session_state.data = get_data()

    # Sidebar filters
    st.sidebar.header('Filtros')

    # Filtro por proyecto
    projects = st.sidebar.selectbox('Proyecto', options=["Todos"] + list(st.session_state.data['project'].unique()))

    # Filtro por cadena (chain)
    chains = st.sidebar.selectbox('Chain', options=["Todos"] + list(st.session_state.data['chain'].unique()))

    # Filtro por símbolo (contiene palabra)
    symbol_filter = st.sidebar.text_input('Símbolo contiene', '')

    # Filtro por APY (enteros, incremento de 1)
    apy_min = st.sidebar.number_input('APY mínimo', min_value=int(st.session_state.data['apy'].min()), max_value=int(st.session_state.data['apy'].max()), value=int(st.session_state.data['apy'].min()), step=1)
    apy_max = st.sidebar.number_input('APY máximo', min_value=int(st.session_state.data['apy'].min()), max_value=int(st.session_state.data['apy'].max()), value=int(st.session_state.data['apy'].max()), step=1)

    # Filtro por TVL (USD) (enteros, incremento de 5000)
    tvl_min = st.sidebar.number_input('TVL mínimo (USD)', min_value=int(st.session_state.data['tvlUsd'].min()), max_value=int(st.session_state.data['tvlUsd'].max()), value=int(st.session_state.data['tvlUsd'].min()), step=5000)
    tvl_max = st.sidebar.number_input('TVL máximo (USD)', min_value=int(st.session_state.data['tvlUsd'].min()), max_value=int(st.session_state.data['tvlUsd'].max()), value=int(st.session_state.data['tvlUsd'].max()), step=5000)

    # Aplicar filtros
    filtered_data = st.session_state.data[
        ((st.session_state.data['project'] == projects) if projects != "Todos" else True) &
        ((st.session_state.data['chain'] == chains) if chains != "Todos" else True) &
        (st.session_state.data['symbol'].str.contains(symbol_filter, case=False)) &
        (st.session_state.data['apy'] >= apy_min) &
        (st.session_state.data['apy'] <= apy_max) &
        (st.session_state.data['tvlUsd'] >= tvl_min) &
        (st.session_state.data['tvlUsd'] <= tvl_max)
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

def second_page():
    st.title("Segunda Página - Scraping de Datos")

    # Lista de términos a buscar
    lista = ["USDC USDT", "USDC", "USDT", "DAI", "FRAX", "USDe", "MAI"]

    # Configuración del proxy (ajusta según sea necesario)
    proxies = {
        "https": "scraperapi.render=true:427b3db93cce1266f1a94aef300f1c5c@proxy-server.scraperapi.com:8001"
    }

    def process_elements(p_elements):
        data = []
        for element in p_elements:
            text = element.text.strip()
            # Usamos una expresión regular mejorada para extraer la información
            match = re.match(r'(.+?)Live([\d.]+[k]?)%\s+\$([\d.]+[km]?)\$([\d.]+[km]?)', text)
            if match:
                name = match.group(1).strip()
                percentage = match.group(2)
                value1 = match.group(3)
                value2 = match.group(4)

                # Convertimos k y m a números reales
                percentage = float(percentage.replace('k', '')) * 1000 if 'k' in percentage else float(percentage)
                value1 = float(value1.replace('k', '').replace('m', '')) * (1000 if 'k' in value1 else 1000000 if 'm' in value1 else 1)
                value2 = float(value2.replace('k', '').replace('m', '')) * (1000 if 'k' in value2 else 1000000 if 'm' in value2 else 1)

                # Separamos el nombre y el tipo (si existe)
                name_parts = name.split('Provide liquidity')
                if len(name_parts) > 1:
                    name = name_parts[0].strip()
                    tipo = 'Provide liquidity'
                else:
                    name_parts = name.split('Hold token')
                    if len(name_parts) > 1:
                        name = name_parts[0].strip()
                        tipo = 'Hold token'
                    else:
                        name_parts = name.split('Lend')
                        if len(name_parts) > 1:
                            name = name_parts[0].strip()
                            tipo = 'Lend'
                        else:
                            tipo = ''

                variables = name.split(" ", 2)  # Dividir en tres partes máximo
                variable1 = variables[0]  # StrykePCS
                variable2 = variables[1]  # ARB-USDC
                try:
                    variable3 = variables[2]
                except:
                    variable3 = ""

                data.append({
                    'DEX': variable1,
                    'Pair': variable2,
                    'Tier': variable3,
                    'Name': name,
                    'Type': tipo,
                    'APR': percentage,
                    'TVL': value1,
                    'Rewards': value2
                })

        return pd.DataFrame(data)

    # Crear un DataFrame vacío para combinar los resultados
    combined_df = pd.DataFrame()

    for term in lista:
        # Realizar la solicitud para cada término en la lista
        url = f'https://merkl.angle.money/?search={term}'
        r = requests.get(url, proxies=proxies, verify=False)
        a = r.text

        # Parsear el contenido HTML
        soup = BeautifulSoup(a, "html.parser")

        # Encontrar los elementos a con la clase especificada
        p_elements = soup.find_all("a", class_="w-full")

        # Procesar los elementos y crear el DataFrame
        df = process_elements(p_elements)

        # Agregar al DataFrame combinado
        combined_df = pd.concat([combined_df, df], ignore_index=True)

    combined_df = combined_df.drop_duplicates(subset='Name')
    palabras_excluir = ["ETH", "BTC", "ARB", "MANTA", "QUICK", "ERA", "DYAD", "WSEI", "MATIC", "LDO", "MNT", "RIF","SHFL",
                        "TAO", "UNI","LCD","LINK", "MKR","WGLMR","LST","SAFE","GNO"]
    final_df = combined_df[~combined_df['Name'].str.contains('|'.join(palabras_excluir))]

    st.write("### Datos obtenidos y filtrados")
    st.dataframe(final_df)

# Sidebar para cambiar entre páginas
page = st.sidebar.selectbox("Selecciona la página", ["Página Principal", "Scraping de Datos"])

if page == "Página Principal":
    main_page()
else:
    second_page()
