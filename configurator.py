import streamlit as st
import pandas as pd

# Exchange rates (as of the current date)
exchange_rates = {
    "EUR": 1,
    "USD": 1.09,
    "GBP": 0.86
}

# AuM brackets and multipliers
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

# Contract length discounts
contract_discounts = {
    "1 year": [0, 0, 0],
    "2 year": [10, 5, 0],
    "3 year": [15, 10, 5]
}

def calculate_price(base_price, currency, aum, contract_length):
    price = base_price * aum_brackets[aum]
    years = int(contract_length.split()[0])
    total_price = sum([price * (1 - contract_discounts[contract_length][year]/100) for year in range(years)])
    return total_price * exchange_rates[currency]

st.set_page_config(page_title="Product Price Configurator", layout="wide")
st.title("Product Price Configurator")

base_price = 100000  # Example base price
st.write(f"Base Price: €{base_price:,.2f}")

col1, col2, col3 = st.columns(3)
with col1:
    currency = st.selectbox("Select Currency", list(exchange_rates.keys()))
with col2:
    aum = st.selectbox("Select AuM Bracket", list(aum_brackets.keys()))
with col3:
    contract_length = st.selectbox("Select Contract Length", list(contract_discounts.keys()))

total_price = calculate_price(base_price, currency, aum, contract_length)
st.subheader("Total Price")
st.write(f"{currency} {total_price:,.2f}")

st.subheader("Additional Information")
st.write(f"Exchange rate: 1 EUR = {exchange_rates[currency]} {currency}")
st.write(f"AuM Multiplier: {aum_brackets[aum]}x")

st.write("Contract Length Discounts:")
df_discounts = pd.DataFrame(contract_discounts).T
df_discounts.columns = ['Year 1', 'Year 2', 'Year 3']
df_discounts = df_discounts.applymap(lambda x: f"{x}%" if x != 0 else "-")
st.table(df_discounts)
