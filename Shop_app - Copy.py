<<<<<<< HEAD
import streamlit as st

st.title("IVO Electronics - SYSTEM TEST")
st.write("If you can see this, the system is WORKING.")

if st.button("CLICK TO START SHOP"):
    st.balloons()
    st.success("System Connection Stable!")
=======
import streamlit as st
import pandas as pd

# 1. Page Configuration & Theme
st.set_page_config(page_title="Partner Electronics Shop", layout="wide")

# Custom CSS for "Nice Colors"
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { background-color: #2e7d32; color: white; border-radius: 8px; }
    h1 { color: #1565c0; }
    </style>
    """, unsafe_allow_html=True)

# 2. Mock Database (In a real app, this would be a CSV file or SQL)
if 'inventory' not in st.session_state:
    st.session_state.inventory = [
        {"name": "Smartphone X", "price": 500, "cost": 350,
            "stock": 10, "img": "https://via.placeholder.com/150"},
        {"name": "Laptop Pro", "price": 1200, "cost": 900,
            "stock": 2, "img": "https://via.placeholder.com/150"},
        {"name": "Wireless Buds", "price": 80, "cost": 40,
            "stock": 15, "img": "https://via.placeholder.com/150"}
    ]
if 'sales' not in st.session_state:
    st.session_state.sales = []

# 3. Sidebar Navigation (Access Control)
user_role = st.sidebar.selectbox("Login as:", ["Attendant", "Partner"])

# 4. Front Page - Attendant Image
st.title("Welcome to the Shop Portal")
col_img, col_text = st.columns([1, 3])
with col_img:
    # Replace the URL below with your actual attendant's photo link
    st.image("https://www.w3schools.com/howto/img_avatar.png",
             width=150, caption="Shop Attendant")
with col_text:
    st.write(f"### Current User: {user_role}")
    st.write("Manage your inventory and sales efficiently below.")

st.divider()

# 5. Inventory Display (Pictures, Names, Prices)
st.subheader("Current Stock")
cols = st.columns(3)

for idx, item in enumerate(st.session_state.inventory):
    with cols[idx % 3]:
        st.image(item['img'])
        st.write(f"**{item['name']}**")
        st.write(f"Price: ${item['price']}")
        st.write(f"In Stock: {item['stock']}")

        # Low Stock Notification for Partners
        if item['stock'] < 3:
            st.error("⚠️ Low Stock!")

        # 6. Sales Entry Section
        qty = st.number_input(
            f"Amount sold ({item['name']})", min_value=0, max_value=item['stock'], key=f"input_{idx}")
        if st.button(f"Record Sale: {item['name']}", key=f"btn_{idx}"):
            if qty > 0:
                # Update Stock
                st.session_state.inventory[idx]['stock'] -= qty
                # Record Sale for Profit calculation
                profit = (item['price'] - item['cost']) * qty
                st.session_state.sales.append(profit)
                st.success(f"Sold {qty} units!")
                st.rerun()

# 7. Partner Section (Profits)
if user_role == "Partner":
    st.divider()
    st.subheader("Partner Dashboard: Monthly Profits")
    total_profit = sum(st.session_state.sales)
    st.metric("Total Monthly Profit", f"${total_profit}")

    # Simple Visual Chart
    if st.session_state.sales:
        st.line_chart(st.session_state.sales)
    else:
        st.info("No sales recorded yet.")
>>>>>>> d8109272ea1c8a2c7db6b1d66ed6c2b965ef88f7
