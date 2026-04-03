import streamlit as st
import pandas as pd
import sqlite3

# --- PAGE CONFIG ---
st.set_page_config(page_title="IVO Electronics - KADAMA", layout="wide")

# --- HTML/CSS CUSTOM STYLING ---
# This is where we use the HTML/CSS you remember to style the app
st.markdown("""
    <style>
    .main-header {
        background-color: #003399;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        color: white;
        font-family: 'Arial';
    }
    .stButton>button {
        background-color: #28a745;
        color: white;
        border-radius: 5px;
        width: 100%;
    }
    .debt-box {
        background-color: #fff3cd;
        padding: 15px;
        border-left: 5px solid #ffc107;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER WITH HTML ---
st.markdown('<div class="main-header"><h1>IVO ELECTRONICS - KADAMA</h1></div>',
            unsafe_allow_html=True)

# --- APP LOGIC ---
menu = ["Sales Counter", "Debt Records", "Admin Panel"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Sales Counter":
    st.subheader("🛒 Sales Terminal")

    col1, col2 = st.columns(2)
    with col1:
        search = st.text_input("Search Brand (e.g., TECNO):")
    with col2:
        # Feature: Default quantity to 0
        qty = st.number_input("Quantity", min_value=0, value=0)

    st.button("Complete Sale")

elif choice == "Debt Records":
    st.markdown('<div class="debt-box"><h3>Outstanding Debt Records</h3></div>',
                unsafe_allow_html=True)
    customer = st.text_input("Customer Name")
    amount = st.number_input("Amount Owed", min_value=0.0)
    if st.button("Save Debt"):
        st.success(f"Recorded {amount} for {customer}")

elif choice == "Admin Panel":
    st.subheader("🔐 Partner Access")
    pin = st.text_input("Enter Partner PIN", type="password")

    if pin == "1234":
        st.write("### Business Reports")
        st.info("Monthly Profit Filter Active")
        # Here we would load the database for reports
    elif pin != "":
        st.error("Incorrect PIN")
