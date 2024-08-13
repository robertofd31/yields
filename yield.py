import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import re

# Configuración de la página
st.set_page_config(page_title="Yield Farming App", page_icon="💰", layout="wide")

# Función para obtener y procesar datos de DeFiLlama
def get_defi_llama_data():
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
        st.error('Error fetching data from DeFiLlama')
        return pd.DataFrame()

# Función para obtener datos de la pool de DeFiLlama
def get_pool_data(pool_id):
    url = f'https://yields.llama.fi/chart/{pool_id}'
    headers = {'accept': '*/*'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return pd.DataFrame(data['data'])
    else:
        st.error('Error fetching pool data from DeFiLlama')
        return pd.DataFrame()

# Función para procesar elementos del web scraping
def process_elements(p_elements):
    data = []
    for element in p_elements:
        text = element.text.strip()
        match = re.match(r'(.+?)Live([\d.]+[k]?)%\s+\$([\d.]+[km]?)\$([\d.]+[km]?)', text)
        if match:
            name = match.group(1).strip()
            percentage = match.group(2)
            value1 = match.group(3)
            value2 = match.group(4)

            percentage = float(percentage.replace('k', '')) * 1000 if 'k' in percentage else float(percentage)
            value1 = float(value1.replace('k', '').replace('m', '')) * (1000 if 'k' in value1 else 1000000 if 'm' in value1 else 1)
            value2 = float(value2.replace('k', '').replace('m', '')) * (1000 if 'k' in value2 else 1000000 if 'm' in value2 else 1)

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

            variables = name.split(" ", 2)
            variable1 = variables[0]
            variable2 = variables[1]
            variable3 = variables[2] if len(variables) > 2 else ""

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

# Función para obtener datos del web scraping
def get_scraped_data():
    lista = ["USDC USDT", "USDC", "USDT", "DAI", "FRAX", "USDe", "MAI"]
    proxies = {
        "https": "scraperapi.render=true:427b3db93cce1266f1a94aef300f1c5c@proxy-server.scraperapi.com:8001"
    }
    combined_df = pd.DataFrame()

    for term in lista:
        url = f'https://merkl.angle.money/?search={term}'
        r = requests.get(url, proxies=proxies, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        p_elements = soup.find_all("a", class_="w-full")
        df = process_elements(p_elements)
        combined_df = pd.concat([combined_df, df], ignore_index=True)

    combined_df = combined_df.drop_duplicates(subset='Name')
    palabras_excluir = ["ETH", "BTC", "ARB", "MANTA", "QUICK", "ERA", "DYAD", "WSEI", "MATIC", "LDO", "MNT", "RIF","SHFL",
                        "TAO", "UNI","LCD","LINK", "MKR","WGLMR","LST","SAFE","GNO"]
    final_df = combined_df[~combined_df['Name'].str.contains('|'.join(palabras_excluir))]
    return final_df

# Función principal para la página de DeFiLlama
def defi_llama_page():
    st.title("DeFiLlama Yield Farming Dashboard")

    if 'defi_llama_data' not in st.session_state:
        st.session_state.defi_llama_data = get_defi_llama_data()

    # Sidebar filters
    st.sidebar.header('Filtros')
    projects = st.sidebar.selectbox('Proyecto', options=["Todos"] + list(st.session_state.defi_llama_data['project'].unique()))
    chains = st.sidebar.selectbox('Chain', options=["Todos"] + list(st.session_state.defi_llama_data['chain'].unique()))
    symbol_filter = st.sidebar.text_input('Símbolo contiene', '')
    apy_min = st.sidebar.number_input('APY mínimo', min_value=int(st.session_state.defi_llama_data['apy'].min()), max_value=int(st.session_state.defi_llama_data['apy'].max()), value=int(st.session_state.defi_llama_data['apy'].min()), step=1)
    apy_max = st.sidebar.number_input('APY máximo', min_value=int(st.session_state.defi_llama_data['apy'].min()), max_value=int(st.session_state.defi_llama_data['apy'].max()), value=int(st.session_state.defi_llama_data['apy'].max()), step=1)
    tvl_min = st.sidebar.number_input('TVL mínimo (USD)', min_value=int(st.session_state.defi_llama_data['tvlUsd'].min()), max_value=int(st.session_state.defi_llama_data['tvlUsd'].max()), value=int(st.session_state.defi_llama_data['tvlUsd'].min()), step=5000)
    tvl_max = st.sidebar.number_input('TVL máximo (USD)', min_value=int(st.session_state.defi_llama_data['tvlUsd'].min()), max_value=int(st.session_state.defi_llama_data['tvlUsd'].max()), value=int(st.session_state.defi_llama_data['tvlUsd'].max()), step=5000)

    # Apply filters
    filtered_data = st.session_state.defi_llama_data[
        ((st.session_state.defi_llama_data['project'] == projects) if projects != "Todos" else True) &
        ((st.session_state.defi_llama_data['chain'] == chains) if chains != "Todos" else True) &
        (st.session_state.defi_llama_data['symbol'].str.contains(symbol_filter, case=False)) &
        (st.session_state.defi_llama_data['apy'] >= apy_min) &
        (st.session_state.defi_llama_data['apy'] <= apy_max) &
        (st.session_state.defi_llama_data['tvlUsd'] >= tvl_min) &
        (st.session_state.defi_llama_data['tvlUsd'] <= tvl_max)
    ]

    st.write('### Tabla de datos filtrados')
    st.dataframe(filtered_data)

    pool_id = st.text_input('Ingresa el ID de la pool', '')
    if pool_id:
        st.write(f"Datos de la pool: {pool_id}")
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

# Función principal para la página de Web Scraping
def web_scraping_page():
    st.title("Merkl Angle Money Web Scraping Results")

    if 'scraped_data' not in st.session_state:
        with st.spinner('Fetching data from Merkl Angle Money...'):
            st.session_state.scraped_data = get_scraped_data()

    st.write("### Datos obtenidos de Merkl Angle Money")
    st.dataframe(st.session_state.scraped_data)

    st.write("### Estadísticas generales")
    st.write(f"Total de oportunidades: {len(st.session_state.scraped_data)}")
    st.write(f"APR promedio: {st.session_state.scraped_data['APR'].mean():.2f}%")
    st.write(f"TVL total: ${st.session_state.scraped_data['TVL'].sum():,.2f}")

    st.write("### Top 10 oportunidades por APR")
    top_10_apr = st.session_state.scraped_data.sort_values('APR', ascending=False).head(10)
    st.dataframe(top_10_apr)

    st.write("### Distribución de tipos de oportunidades")
    type_counts = st.session_state.scraped_data['Type'].value_counts()
    st.bar_chart(type_counts)

# Menú principal
def main():
    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Ir a", ["DeFiLlama Dashboard", "Merkl Angle Money Scraper"])

    if page == "DeFiLlama Dashboard":
        defi_llama_page()
    elif page == "Merkl Angle Money Scraper":
        web_scraping_page()

if __name__ == "__main__":
    main()
