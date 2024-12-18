import streamlit as st
import pandas as pd
import traceback

# Initialize session state if not already done
if 'init' not in st.session_state:
    st.session_state.init = True
    st.set_page_config(page_title="Product Price Configurator", layout="wide")

# Load exchange rates and AuM brackets
exchange_rates = {"EUR": 1, "USD": 1.09, "GBP": 0.86}
aum_brackets = {"<0.5Bn": 0.40, "0.5-1Bn": 0.52, "1-5Bn": 0.62, "5-15Bn": 0.80, "15-25Bn": 1.00, "25-50Bn": 1.40, "50-250Bn": 1.80, "250+Bn": 2.20}
contract_discounts = {"1 year": [0, 0, 0], "2 year": [10, 5, 0], "3 year": [15, 10, 5]}

# Access method multipliers
access_methods = {
    "Webapp (reports only)": -0.15,
    "Webapp (download)": 0,
    "API": 0,
    "Datafeed": 0.15
}

# Module count discounts
module_discounts = {2: 0, 3: 0.15, 4: 0.20, 5: 0.25, 6: 0.30, 7: 0.35}

@st.cache_data
def load_module_data():
    try:
        return pd.read_csv('modules.csv')
    except Exception as e:
        st.error(f"Error loading modules.csv: {str(e)}")
        return pd.DataFrame(columns=['Topic', 'Product module', 'Price'])

modules_df = load_module_data()

def calculate_price(base_price, currency, aum, contract_length, selected_modules, access_methods):
    # ... (keep the existing calculate_price function)

def format_price(price, currency):
    # ... (keep the existing format_price function)

def main():
    try:
        st.title("Product Price Configurator")

        st.write("Debug: Modules DataFrame")
        st.write(modules_df)

        col1, col2, col3 = st.columns(3)
        with col1:
            currency = st.selectbox("Select Currency", list(exchange_rates.keys()))
        with col2:
            aum = st.selectbox("Select AuM Bracket", list(aum_brackets.keys()))
        with col3:
            contract_length = st.selectbox("Select Contract Length", list(contract_discounts.keys()))

        st.subheader("Access Methods")
        selected_access_methods = {}
        for method, multiplier in access_methods.items():
            selected_access_methods[method] = st.checkbox(f"{method} ({multiplier*100:+.0f}%)")

        st.subheader("Select Product Modules")
        selected_modules = []
        
        # Group modules by Topic
        grouped_modules = modules_df.groupby('Topic')
        
        for topic, group in grouped_modules:
            st.write(f"**{topic}**")
            for _, row in group.iterrows():
                if st.checkbox(f"{row['Product module']} ({format_price(row['Price'], currency)})", key=row['Product module']):
                    selected_modules.append(row['Product module'])
            st.write("")  # Add some space between topics

        if selected_modules:
            st.subheader("Selected Modules")
            selected_df = modules_df[modules_df['Product module'].isin(selected_modules)].copy()
            selected_df['Adjusted Price'] = selected_df['Price'] * aum_brackets[aum]
            selected_df['Price'] = selected_df['Price'].apply(lambda x: format_price(x, currency))
            selected_df['Adjusted Price'] = selected_df['Adjusted Price'].apply(lambda x: format_price(x, currency))
            st.table(selected_df[['Topic', 'Product module', 'Price', 'Adjusted Price']])

        base_price = 0
        total_price = calculate_price(base_price, currency, aum, contract_length, selected_modules, selected_access_methods)
        st.subheader("Total Price")
        st.write(format_price(total_price, currency))

        st.subheader("Additional Information")
        st.write(f"Exchange rate: 1 EUR = {exchange_rates[currency]} {currency}")
        st.write(f"AuM Multiplier: {aum_brackets[aum]}x")
        st.write(f"Module Count Discount: {module_discounts.get(len(selected_modules), module_discounts[7] if len(selected_modules) > 7 else 0):.0%}")

        st.write("Contract Length Discounts:")
        df_discounts = pd.DataFrame(contract_discounts).T
        df_discounts.columns = ['Year 1', 'Year 2', 'Year 3']
        df_discounts = df_discounts.applymap(lambda x: f"{x}%" if x != 0 else "-")
        st.table(df_discounts)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error(traceback.format_exc())

if __name__ == "__main__":
    main()
