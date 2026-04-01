import streamlit as st
import pandas as pd
from datetime import datetime

# 1. PROFESSIONAL THEME & LAYOUT
st.set_page_config(page_title="IVO Electronics Portal", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; border: 1px solid #dee2e6; padding: 15px; border-radius: 10px; }
    .sidebar .sidebar-content { background-color: #004d40; color: white; }
    h1, h2 { color: #004d40; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATABASE INITIALIZATION
if 'inventory' not in st.session_state:
    st.session_state.inventory = [
        {"name": "iPhone 15 Pro Max", "price": 4481000, "cost": 3950000, "stock": 5},
        {"name": "Samsung Galaxy A54", "price": 1550000,
            "cost": 1300000, "stock": 10},
        {"name": "HP Laptop 15", "price": 2450000, "cost": 2150000, "stock": 3},
        {"name": "JBL Flip 6", "price": 425000, "cost": 340000, "stock": 15}
    ]

if 'sales_history' not in st.session_state:
    st.session_state.sales_history = []

# 3. SIDEBAR NAVIGATION
with st.sidebar:
    st.title("⚙️ IVO Manager")
    user_role = st.radio("Access Role:", ["Shop Attendant", "Partner / Owner"])
    st.divider()
    st.success(f"Current Access: **{user_role}**")
    st.info("Location: Kampala, Uganda")

# 4. FRONT PAGE (FIXED SECTION)
st.title("📱 IVO Electronics - Kampala")

# This is the single, clean line for your header image
st.image("ivo_header.jpg", caption="Your Professional Shop Attendant - IVO Electronics",
         use_container_width=True)

st.divider()

# 5. ATTENDANT VIEW
st.header("📦 Current Inventory")
cols = st.columns(2)

for idx, item in enumerate(st.session_state.inventory):
    with cols[idx % 2]:
        with st.container(border=True):
            st.subheader(item['name'])
            st.write(f"**Price:** UGX {item['price']:,}")
            st.write(f"**In Stock:** {item['stock']}")

            qty = st.number_input(f"Qty Sold", min_value=0,
                                  max_value=item['stock'], key=f"q_{idx}")

            if st.button(f"Record Sale for {item['name']}", key=f"b_{idx}"):
                if qty > 0:
                    item['stock'] -= qty
                    profit_val = (item['price'] - item['cost']) * qty
                    st.session_state.sales_history.append({
                        "Date": datetime.now().strftime("%H:%M"),
                        "Item": item['name'],
                        "Qty": qty,
                        "Total Sale": item['price'] * qty,
                        "Profit": profit_val
                    })
                    st.balloons()
                    st.rerun()

# 6. PARTNER DASHBOARD (STRICTLY FOR OWNERS)
if user_role == "Partner / Owner":
    st.divider()
    st.header("📊 Financial Report (Private)")

    if st.session_state.sales_history:
        df = pd.DataFrame(st.session_state.sales_history)
        c1, c2 = st.columns(2)
        c1.metric("Total Revenue", f"UGX {df['Total Sale'].sum():,}")
        c2.metric("Today's Profit", f"UGX {df['Profit'].sum():,}")

        st.subheader("Units Sold per Product")
        chart_data = df.groupby('Item')['Qty'].sum()
        st.bar_chart(chart_data)

        st.subheader("Sales Audit Log")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No sales data recorded yet.")
