import streamlit as st
import pandas as pd
import traceback

# Initialize session state if not already done
if 'init' not in st.session_state:
    st.session_state.init = True
    st.set_page_config(page_title="Product Price Configurator", layout="wide")

# Load exchange rates and AuM brackets
exchange_rates = {"USD": 1, "EUR": 1/1.09, "GBP": 0.86/1.09}  # Updated to make USD the base currency
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

def calculate_discount(module_count, contract_length):
    years = int(contract_length.split()[0])
    module_discount = module_discounts.get(module_count, module_discounts[7] if module_count > 7 else 0)
    contract_discount = sum(contract_discounts[contract_length][:years]) / years / 100
    total_discount = 1 - (1 - module_discount) * (1 - contract_discount)
    return total_discount

def format_price(price, currency):
    if currency == 'EUR':
        return f"€{price:,.2f}"
    elif currency == 'USD':
        return f"${price:,.2f}"
    elif currency == 'GBP':
        return f"£{price:,.2f}"

def main():
    try:
        st.title("Product Price Configurator")

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
        selected_modules = []
        
        # Group modules by Topic
        grouped_modules = modules_df.groupby('Topic')
        
        for topic, group in grouped_modules:
            with st.expander(f"**{topic}**", expanded=True):
                for _, row in group.iterrows():
                    if st.checkbox(f"{row['Product module']}", key=row['Product module']):
                        selected_modules.append(row['Product module'])

        if selected_modules:
            st.subheader("Selected Modules")
            selected_df = modules_df[modules_df['Product module'].isin(selected_modules)].copy()
            selected_df['List Price'] = selected_df['Price'] * aum_brackets[aum] * exchange_rates[currency]
            
            # Calculate discount
            discount = calculate_discount(len(selected_modules), contract_length)
            
            selected_df['Discount'] = f"{discount:.2%}"
            selected_df['Offer Price'] = selected_df['List Price'] * (1 - discount)
            
            # Apply access method multiplier
            access_multiplier = max([access_methods[method] for method in selected_access_methods if selected_access_methods[method]])
            selected_df['Offer Price'] *= (1 + access_multiplier)
            
            selected_df['List Price'] = selected_df['List Price'].apply(lambda x: format_price(x, currency))
            selected_df['Offer Price'] = selected_df['Offer Price'].apply(lambda x: format_price(x, currency))
            st.table(selected_df[['Topic', 'Product module', 'List Price', 'Discount', 'Offer Price']])

        total_price = selected_df['Offer Price'].str.replace(r'[^\d.]', '', regex=True).astype(float).sum()
        st.subheader("Total Price")
        st.write(format_price(total_price, currency))

        st.subheader("Additional Information")
        st.write(f"Exchange rate: 1 USD = {1/exchange_rates[currency]:.2f} {currency}")
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
