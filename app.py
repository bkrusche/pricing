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


@st.cache_data
def load_access_methods():
    try:
        access_methods_df = pd.read_csv('accessmethods.csv')
        access_method_factors = {}
        for row in access_methods_df.itertuples(index=False):
            key = tuple(str(value).lower() == 'true' for value in row[:4])  # Convert first 4 columns to boolean
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
    st.stop()  # Stop execution if there's an error

# Load module data from CSV file
@st.cache_data
def load_module_data():
    try:
        return pd.read_csv('modules.csv')
    except Exception as e:
        st.error(f"Error loading modules.csv: {str(e)}")
        return pd.DataFrame(columns=['Topic', 'Product module', 'Price', 'Webapp (reports only)', 'Webapp (download)', 'API', 'Datafeed'])

modules_df = load_module_data()

# Clean column names by stripping spaces (to avoid issues)
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

# Main application logic
def main():
    try:
        access_method_factors = load_access_methods()  # Load access methods
        st.title("Product Price Configurator")

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
        selected_modules = []
        
        # Custom sorting of topics
        custom_order = [
            "Regulatory",
            "Climate",
            "Risk",
            "Impact",
            "Nature & Biodiversity",
            "Labels",
            "Raw data",
            "Benchmarks"
        ]
        
        # Sort modules based on custom order
        modules_df['Topic'] = pd.Categorical(modules_df['Topic'], categories=custom_order, ordered=True)
        modules_df.sort_values('Topic', inplace=True)

        # Group modules by Topic and display them
        grouped_modules = modules_df.groupby('Topic')
        for topic, group in grouped_modules:
            with st.expander(f"**{topic}**", expanded=True):
                for _, row in group.iterrows():
                    if st.checkbox(f"{row['Product module']}", key=row['Product module']):
                        selected_modules.append(row['Product module'])

        # Process selected modules
        if selected_modules:
            st.subheader("Selected Modules")
            selected_df = modules_df[modules_df['Product module'].isin(selected_modules)].copy()
        
            # Ensure 'Price' is numeric
            selected_df['Price'] = pd.to_numeric(selected_df['Price'], errors='coerce')
        
            # Calculate list price
            selected_df['List Price'] = selected_df['Price'] * aum_brackets[aum] * exchange_rates[currency]
        
            # Initialize access method multiplier
            access_method_keys = (
                bool(selected_access_methods.get('Webapp (reports only)', False)),
                bool(selected_access_methods.get('Webapp (download)', False)),
                bool(selected_access_methods.get('API', False)),
                bool(selected_access_methods.get('Datafeed', False))
            )

            
            # Get the access_multiplier based on selected access methods
            access_multiplier = access_method_factors.get(access_method_keys, 0)  # Default to 0 if no match found

            # Apply total access multiplier
            selected_df['List Price'] *= (1 + access_multiplier)
        
            # Calculate discounts
            bundle_discount = calculate_discount(len(selected_modules), contract_length)  # Use existing function for bundle discount
            multi_year_discount = sum(contract_discounts[contract_length]) / 100  # Calculate multi-year discount based on contract length
        
            # Add new discount columns
            selected_df['Bundle Discount'] = f"{bundle_discount:.2%}"
            selected_df['Multi-Year Discount'] = f"{multi_year_discount:.2%}"
        
            # Add AE Discount column with dropdown selection for up to 15%
            ae_discount_options = [0, 5, 10, 15]  # Define options for AE Discount
            col_ae_discount = st.columns(3)[0]  # Create a column that takes up one-third of the page
            ae_discount_percentage = col_ae_discount.selectbox("Select AE Discount (%)", ae_discount_options) / 100  # Dropdown for AE Discount
            selected_df['AE Discount'] = f"{ae_discount_percentage:.2%}"
        
            # Calculate final price considering all discounts
            selected_df['Final Price'] = selected_df['List Price'].astype(float) * (1 - bundle_discount) * (1 - multi_year_discount) * (1 - ae_discount_percentage)
        
            # Format prices for display
            selected_df['List Price'] = selected_df['List Price'].apply(lambda x: format_price(x, currency))
            selected_df['Final Price'] = selected_df['Final Price'].apply(lambda x: format_price(x, currency))
        
            # Display results table with new columns
            st.table(selected_df[['Topic', 'Product module', 'List Price', 'Bundle Discount', 'Multi-Year Discount', 'AE Discount', 'Final Price']])
        

            # Check incompatible module-access method combinations
            incompatible_combinations = []
            for module in selected_modules:
                module_row = modules_df[modules_df['Product module'] == module].iloc[0]
                for method, selected in selected_access_methods.items():
                    # Ensure proper handling of availability column (True or False)
                    if selected == True:
                        if selected != module_row[method]: 
                            incompatible_combinations.append((module, method))
                        
            
            # Display incompatible combinations
            if incompatible_combinations:
                st.markdown("### **Incompatible Access Methods**")
                for module, method in incompatible_combinations:
                    st.markdown(
                        f'<p style="color: red;">⚠️ {module} is not available with {method}</p>',
                        unsafe_allow_html=True,
                    )


            # Total price
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
