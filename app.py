import streamlit as st
import pandas as pd

# Initialize session state if not already done
if 'init' not in st.session_state:
    st.session_state.init = True
    st.set_page_config(page_title="Product Price Configurator", layout="wide")

# Load exchange rates and AuM brackets
exchange_rates = {
    "EUR": 1,
    "USD": 1.09,
    "GBP": 0.86
}

aum_brackets = {
    "<0.5Bn": 0.40,
    "0.5-1Bn": 0.52,
    "1-5Bn": 0.62,
    "5-15Bn": 0.80,
    "15-25Bn": 1.00,
    "25-50Bn": 1.40,
    "50-250Bn": 1.80,
    "250+Bn": 2.20
}

contract_discounts = {
    "1 year": [0, 0, 0],
    "2 year": [10, 5, 0],
    "3 year": [15, 10, 5]
}

# Load module data from CSV
@st.cache_data
def load_module_data():
    return pd.read_csv('modules.csv')

modules_df = load_module_data()

def calculate_price(base_price, currency, aum, contract_length, selected_modules):
    aum_multiplier = aum_brackets[aum]
    years = int(contract_length.split()[0])
    
    total_price = sum([base_price * (1 - contract_discounts[contract_length][year]/100) for year in range(years)])
    
    for module in selected_modules:
        module_price = modules_df[modules_df['Product module'] == module]['Price'].values[0]
        total_price += module_price * aum_multiplier * years
    
    return total_price * exchange_rates[currency]

def main():
    st.title("Product Price Configurator")

    col1, col2, col3 = st.columns(3)
    with col1:
        currency = st.selectbox("Select Currency", list(exchange_rates.keys()))
    with col2:
