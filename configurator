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
    "2 year": [0.10, 0.05, 0],
    "3 year": [0.15, 0.10, 0.05]
}

def calculate_price(base_price, currency, aum, contract_length):
    # Apply AuM multiplier
    price = base_price * aum_brackets[aum]
    
    # Apply contract length discounts
    years = int(contract_length.split()[0])
    total_price = 0
    for year in range(years):
        year_price = price * (1 - contract_discounts[contract_length][year])
        total_price += year_price
    
    # Convert to selected currency
    total_price = total_price * exchange_rates[currency]
    
    retur
