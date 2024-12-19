import streamlit as st
import pandas as pd
import traceback

# Initialize session state if not already done
if 'init' not in st.session_state:
    st.session_state.init = True
    st.set_page_config(page_title="Product Price Configurator", layout="wide")

# Add function to clear all selections
def clear_all_selections():
    # Clear access method selections
    for method in access_methods.keys():
        st.session_state[f"access_method_{method}"] = False
    
    # Clear module selections
    for module in modules_df['Product module']:
        st.session_state[module] = False


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

#load licences information 
@st.cache_data
def load_licenses():
    try:
        return pd.read_csv('licenses.csv')
    except Exception as e:
        st.error(f"Error loading licenses.csv: {str(e)}")
        return pd.DataFrame(columns=['Ticket size', '# licenses'])

licenses_df = load_licenses()

def get_included_licenses(total_price):
    if licenses_df.empty:
        st.warning("Licenses data is empty or not loaded properly. Using default value of 1 license.")
        return 1
    
    for _, row in licenses_df.iterrows():
        if total_price <= row['Ticket size']:
            return row['# licenses']
    
    # If we've gone through all rows without finding a match, return the last value
    if not licenses_df.empty:
        return licenses_df.iloc[-1]['# licenses']
    else:
        return 1  # Default to 1 license if DataFrame is empty


@st.cache_data
def load_label_requirements():
    try:
        return pd.read_csv('labels.csv')
    except Exception as e:
        st.error(f"Error loading labels.csv: {str(e)}")
        return pd.DataFrame()
def get_required_modules_for_label(label_name, labels_df):
    """Get the required modules based on the metrics count in labels.csv"""
    label_reqs = labels_df[labels_df['Label name'] == label_name].iloc[0]
    required_modules = []
    
    # Map the requirements to specific modules
    if int(label_reqs['Exposures']) > 0:
        required_modules.append('Exposures')
    
    if int(label_reqs['ESG Risk']) > 0:
        required_modules.append('ESG Risk')
    
    if int(label_reqs['SFDR PAIs']) > 0:
        required_modules.append('SFDR PAIs')
    
    if int(label_reqs['UN SDGs Alignment']) > 0:
        required_modules.append('UN SDGs Alignment')
    
    if int(label_reqs['Carbon Footprint']) > 0:
        required_modules.append('Carbon Footprint')
    
    if int(label_reqs['EU Taxonomy - product level reporting']) > 0:
        required_modules.append('EU Taxonomy - product level reporting')
    
    # For 'Other' metrics, we'll assume they need the smallest Raw data package
    if int(label_reqs['Other']) > 0:
        required_modules.append('Emissions / Up to 10 metrics')
    
    return required_modules

def check_label_requirements(selected_modules, modules_df, labels_df):
    # Get all selected labels
    selected_labels = [module for module in selected_modules 
                      if module in labels_df['Label name'].values]
    
    if not selected_labels:
        return None
    
    missing_requirements = {}
    
    for selected_label in selected_labels:
        required_modules = get_required_modules_for_label(selected_label, labels_df)
        missing_modules = [module for module in required_modules 
                         if module not in selected_modules]
        
        if missing_modules:
            missing_requirements[selected_label] = missing_modules
            
    return missing_requirements
    

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
        
        # Create two columns for title and clear button
        col_title, col_button = st.columns([5,1])
        with col_title:
            st.title("Product Price Configurator")
        with col_button:
            st.button("Clear All Selections", on_click=clear_all_selections, type="secondary")


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
            with st.expander(f"**{topic}**", expanded=False):
                for _, row in group.iterrows():
                    if st.checkbox(f"{row['Product module']}", key=row['Product module']):
                        selected_modules.append(row['Product module'])

        # Process selected modules
        if selected_modules:
            # Load labels data
            labels_df = load_label_requirements()
                
        # check requirements for labels
        if selected_modules:
            # Load labels data
            labels_df = load_label_requirements()
            
            # Check requirements for any selected labels
            missing_requirements = check_label_requirements(selected_modules, modules_df, labels_df)
            
            if missing_requirements:
                            st.markdown("### **Label Requirements Check**")
                            for label, missing_modules in missing_requirements.items():
                                label_reqs = labels_df[labels_df['Label name'] == label].iloc[0]
                                for module in missing_modules:
                                    # Map module to its requirement count from labels.csv
                                    if module == 'Exposures':
                                        count = label_reqs['Exposures']
                                    elif module == 'ESG Risk':
                                        count = label_reqs['ESG Risk']
                                    elif module == 'SFDR PAIs':
                                        count = label_reqs['SFDR PAIs']
                                    elif module == 'UN SDGs Alignment':
                                        count = label_reqs['UN SDGs Alignment']
                                    elif module == 'Carbon Footprint':
                                        count = label_reqs['Carbon Footprint']
                                    elif module == 'EU Taxonomy - product level reporting':
                                        count = label_reqs['EU Taxonomy - product level reporting']
                                    elif module == 'Emissions / Up to 10 metrics':
                                        count = label_reqs['Other']
                                        
                                    st.markdown(
                                        f'<p style="color: orange;">⚠️ {label} requires {int(count)} metrics from {module}</p>',
                                        unsafe_allow_html=True
                                    )
                
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


                    # Calculate total price
        total_price = selected_df['Final Price'].str.replace(r'[^\d.]', '', regex=True).astype(float).sum()

        # Determine included licenses
        included_licenses = get_included_licenses(total_price)



        # Display results in three columns
        col1, col2, col3 = st.columns(3)
        with col1:

            # Allow user to add extra licenses
            st.subheader("Licenses")
            extra_licenses = st.number_input("Additional licenses", min_value=0, value=0, step=1)
            license_cost = 1000  # Set the cost per additional license (adjust as needed)
            total_licenses = included_licenses + extra_licenses
            extra_license_cost = extra_licenses * license_cost

            st.write(f"{total_licenses} ({included_licenses} included + {extra_licenses} additional)")
    
            # Update total price with extra license cost
            final_total_price = total_price + extra_license_cost
        with col2:
            st.subheader("Included Service Level")
            st.write("N/A")  # Empty for now, as requested
        with col3:
            st.subheader("Total Price")
            st.write(format_price(final_total_price, currency))

        st.subheader("Additional Information")
        st.write(f"Exchange rate: 1 USD = {1/exchange_rates[currency]:.2f} {currency}")
        st.write(f"Cost per additional license: {format_price(license_cost, currency)}")
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error(traceback.format_exc())

# Run the application
if __name__ == "__main__":
    main()
