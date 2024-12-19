import streamlit as st
import pandas as pd
import traceback
import pyperclip

# Initialize session state if not already done
if 'init' not in st.session_state:
    st.session_state.init = True
    st.session_state.selected_modules = []

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

@st.cache_data
def load_access_methods():
    try:
        access_methods_df = pd.read_csv('accessmethods.csv')
        access_method_factors = {}
        for row in access_methods_df.itertuples(index=False):
            key = tuple(str(value).lower() == 'true' for value in row[:4])
            value = float(row[4]) if isinstance(row[4], float) else float(row[4].strip())
            access_method_factors[key] = value
        return access_method_factors
    except Exception as e:
        st.error(f"Error loading accessmethods.csv: {str(e)}")
        return {}

# Extract configurations from the DataFrame
try:
    aum_brackets = {row[2].strip(): float(row[3]) for row in config_df[config_df['Type'] == 'AuM Multiplier'].itertuples()}
    access_methods = {row[2].strip(): float(row[3]) for row in config_df[config_df['Type'] == 'Access Method'].itertuples()}
    module_discounts = {int(row[2]): float(row[3]) for row in config_df[config_df['Type'] == 'Module Discount'].itertuples()}
    contract_discounts = {
        "1 year": [0, 0, 0],
        "2 year": [10, 5, 0],
        "3 year": [15, 10, 5]
    }
    exchange_rates = {row[2]: eval(row[3]) for row in config_df[config_df['Type'] == 'Exchange Rate'].itertuples()}
except Exception as e:
    st.error(f"Error processing configuration data: {str(e)}")
    st.stop()

# Load module data from CSV file
@st.cache_data
def load_module_data():
    try:
        return pd.read_csv('modules.csv')
    except Exception as e:
        st.error(f"Error loading modules.csv: {str(e)}")
        return pd.DataFrame(columns=['Topic', 'Product module', 'Price', 'Webapp (reports only)', 'Webapp (download)', 'API', 'Datafeed'])

modules_df = load_module_data()
modules_df.columns = modules_df.columns.str.strip()

# Function to calculate discounts
def calculate_discount(module_count, contract_length):
    years = int(contract_length.split()[0])
    module_discount = module_discounts.get(module_count, module_discounts[7] if module_count > 7 else 0)
    contract_discount = sum(contract_discounts[contract_length][:years]) / years / 100
    total_discount = 1 - (1 - module_discount) * (1 - contract_discount)
    return total_discount

# Function to format price based on currency
def format_price(price, currency):
    if currency == 'EUR':
        return f"€{price:,.2f}"
    elif currency == 'USD':
        return f"${price:,.2f}"
    elif currency == 'GBP':
        return f"£{price:,.2f}"

# Function to clear all selections
def clear_selections():
    st.session_state.selected_modules = []
    for key in st.session_state.keys():
        if key.startswith('checkbox_'):
            st.session_state[key] = False

# Main application logic
def main():
    try:
        access_method_factors = load_access_methods()

        st.title("Product Price Configurator")

        # Clear All Selections button
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Clear All Selections", key="clear_all"):
                clear_selections()

        # User inputs
        col1, col2, col3 = st.columns(3)
        with col1:
            currency = st.selectbox("Select Currency", list(exchange_rates.keys()))
        with col2:
            aum = st.selectbox("Select AuM Bracket", list(aum_brackets.keys()))
        with col3:
            contract_length = st.selectbox("Select Contract Length", list(contract_discounts.keys()))

        st.subheader("Access Methods")
        cols = st.columns(len(access_methods))
        selected_access_methods = {}
        for i, method in enumerate(access_methods.keys()):
            with cols[i]:
                selected_access_methods[method] = st.checkbox(f"{method}")

        st.subheader("Select Product Modules")
        selected_modules = st.session_state.selected_modules

        # Custom sorting of topics
        custom_order = [
            "Regulatory", "Climate", "Risk", "Impact", "Nature & Biodiversity", "Labels", "Raw data", "Benchmarks"
        ]
        modules_df['Topic'] = pd.Categorical(modules_df['Topic'], categories=custom_order, ordered=True)
        modules_df.sort_values('Topic', inplace=True)

        # Group modules by Topic and display them
        grouped_modules = modules_df.groupby('Topic')
        for topic, group in grouped_modules:
            with st.expander(f"**{topic}**", expanded=False):
                for _, row in group.iterrows():
                    checkbox_key = f"checkbox_{row['Product module']}"
                    if st.checkbox(f"{row['Product module']}", key=checkbox_key, value=row['Product module'] in selected_modules):
                        if row['Product module'] not in selected_modules:
                            selected_modules.append(row['Product module'])
                    elif row['Product module'] in selected_modules:
                        selected_modules.remove(row['Product module'])

        st.session_state.selected_modules = selected_modules

        # Process selected modules
        if selected_modules:
            st.subheader("Selected Modules")
            selected_df = modules_df[modules_df['Product module'].isin(selected_modules)].copy()
            selected_df['Price'] = pd.to_numeric(selected_df['Price'], errors='coerce')
            selected_df['List Price'] = selected_df['Price'] * aum_brackets[aum] * exchange_rates[currency]

            access_method_keys = (
                bool(selected_access_methods.get('Webapp (reports only)', False)),
                bool(selected_access_methods.get('Webapp (download)', False)),
                bool(selected_access_methods.get('API', False)),
                bool(selected_access_methods.get('Datafeed', False))
            )
            access_multiplier = access_method_factors.get(access_method_keys, 0)
            selected_df['List Price'] *= (1 + access_multiplier)

            bundle_discount = calculate_discount(len(selected_modules), contract_length)
            multi_year_discount = sum(contract_discounts[contract_length]) / 100

            selected_df['Bundle Discount'] = f"{bundle_discount:.2%}"
            selected_df['Multi-Year Discount'] = f"{multi_year_discount:.2%}"

            col_ae_discount = st.columns(3)[0]
            ae_discount_options = [0, 5, 10, 15]
            ae_discount_percentage = col_ae_discount.selectbox("Select AE Discount (%)", ae_discount_options) / 100
            selected_df['AE Discount'] = f"{ae_discount_percentage:.2%}"

            selected_df['Final Price'] = selected_df['List Price'].astype(float) * (1 - bundle_discount) * (1 - multi_year_discount) * (1 - ae_discount_percentage)

            selected_df['List Price'] = selected_df['List Price'].apply(lambda x: format_price(x, currency))
            selected_df['Final Price'] = selected_df['Final Price'].apply(lambda x: format_price(x, currency))

            result_table = selected_df[['Topic', 'Product module', 'List Price', 'Bundle Discount', 'Multi-Year Discount', 'AE Discount', 'Final Price']]
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.table(result_table)
            with col2:
                if st.button("Copy Results"):
                    total_price = selected_df['Final Price'].str.replace(r'[^\d.]', '', regex=True).astype(float).sum()
                    formatted_total_price = format_price(total_price, currency)
                    exchange_rate_info = f"Exchange rate: 1 USD = {1/exchange_rates[currency]:.2f} {currency}"
                    
                    result_string = f"Selected Modules:\n{result_table.to_string()}\n\nTotal Price: {formatted_total_price}\n\n{exchange_rate_info}"
                    pyperclip.copy(result_string)
                    st.success("Results copied to clipboard!")

            incompatible_combinations = []
            for module in selected_modules:
                module_row = modules_df[modules_df['Product module'] == module].iloc[0]
                for method, selected in selected_access_methods.items():
                    if selected == True:
                        if selected != module_row[method]:
                            incompatible_combinations.append((module, method))

            if incompatible_combinations:
                st.markdown("### **Incompatible Access Methods**")
                for module, method in incompatible_combinations:
                    st.markdown(
                        f'<p style="color: red;">⚠️ {module} is not available with {method}</p>',
                        unsafe_allow_html=True,
                    )

            total_price = selected_df['Final Price'].str.replace(r'[^\d.]', '', regex=True).astype(float).sum()
            st.subheader("Total Price")
            st.write(format_price(total_price, currency))

            st.subheader("Additional Information")
            st.write(f"Exchange rate: 1 USD = {1/exchange_rates[currency]:.2f} {currency}")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error(traceback.format_exc())

# Run the application
if __name__ == "__main__":
    main()
