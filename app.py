import streamlit as st
import pandas as pd
import traceback

# Initialize session state if not already done
if 'init' not in st.session_state:
    st.session_state.init = True
    st.set_page_config(page_title="Product Price Configurator", layout="wide")

# Load configuration from CSV file
@st.cache_data
def load_config():
    try:
        return pd.read_csv('config.csv')
    except Exception as e:
        st.error(f"Error loading config.csv: {str(e)}")
        return pd.DataFrame(columns=['Type', 'Key', 'Value'])

config_df = load_config()

# Extract configurations from the DataFrame
try:
    aum_brackets = {row[2].strip(): float(row[3]) for row in config_df[config_df['Type'] == 'AuM Multiplier'].itertuples()}
    access_methods = {row[2].strip(): float(row[3]) for row in config_df[config_df['Type'] == 'Access Method'].itertuples()}
    module_discounts = {int(row[2]): float(row[3]) for row in config_df[config_df['Type'] == 'Module Discount'].itertuples()}
    
    # Load contract discounts from a hardcoded dictionary or from CSV if needed
    contract_discounts = {
        "1 year": [0, 0, 0],
        "2 year": [10, 5, 0],
        "3 year": [15, 10, 5]
    }
    
    # Load exchange rates and convert them to a dictionary safely.
    exchange_rates = {}
    for row in config_df[config_df['Type'] == 'Exchange Rate'].itertuples():
        key = row[1]  # Currency code (e.g., EUR)
        value_str = row[2].strip()  # Get the string representation of the rate
        # Convert the string to a float value safely
        if '/' in value_str:
            numerator, denominator = map(float, value_str.split('/'))
            value = numerator / denominator
        else:
            value = float(value_str)
        exchange_rates[key] = value

except Exception as e:
    st.error(f"Error processing configuration data: {str(e)}")
    st.stop()  # Stop execution if there's an error

# Load module data from CSV file (keep this part unchanged)
@st.cache_data
def load
