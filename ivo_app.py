import streamlit as st
import pandas as pd
import os
import json
import requests
import difflib
from datetime import datetime
from duckduckgo_search import DDGS

# --- 1. SETTINGS & FILE PATHS ---
STOCK_FILE = 'inventory.csv'
SALES_FILE = 'sales_history.csv'
CREDIT_FILE = 'debts.csv'
CONFIG_FILE = 'admin_config.json'
IMAGE_FOLDER = 'item_images'
HEADER_IMAGE = 'ivo_header.jpg'
LOW_STOCK_THRESHOLD = 2

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# --- 2. PRODUCT DATABASE (Quick Add) ---
SUGGESTION_DATABASE = [
    "TECNO Phantom V Flip 2", "TECNO Camon 30 Premier", "TECNO Camon 30 Pro",
    "TECNO Spark 20 Pro+", "TECNO Spark 20", "TECNO Pop 8", "Infinix Note 40 Pro",
    "Infinix Hot 40 Pro", "Infinix Smart 8", "Itel A70", "Samsung Galaxy S24 Ultra",
    "iPhone 15 Pro Max", "Oraimo 20000mAh Powerbank", "Sony Smart TV 55 inch",
    "HP Laptop 15", "Digital TV Guard", "Extension 6-Way"
]

# --- 3. DATA ENGINE ---


def load_data():
    if os.path.exists(STOCK_FILE):
        return pd.read_csv(STOCK_FILE)
    return pd.DataFrame(columns=["Brand", "Model", "Price", "Cost", "Stock"])


def load_sales():
    if os.path.exists(SALES_FILE):
        df = pd.read_csv(SALES_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    return pd.DataFrame(columns=["Date", "Item", "Qty", "SalePrice", "CostPrice", "Profit", "Month"])


def load_credits():
    if os.path.exists(CREDIT_FILE):
        return pd.read_csv(CREDIT_FILE)
    return pd.DataFrame(columns=["Date", "Customer", "Phone", "Item", "Balance", "Status"])


def save_data(df, filename):
    df.to_csv(filename, index=False)


@st.cache_data(show_spinner=False)
def fetch_image(item_name):
    safe_name = "".join(
        [c for c in item_name if c.isalnum() or c == ' ']).strip()
    path = os.path.join(IMAGE_FOLDER, f"{safe_name}.jpg")
    if os.path.exists(path):
        return path
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(
                f"{item_name} official product", max_results=1))
            if results:
                img_data = requests.get(results[0]['image'], timeout=5).content
                with open(path, 'wb') as f:
                    f.write(img_data)
                return path
    except:
        return None


# --- 4. STYLING ---
st.set_page_config(page_title="IVO Electronics - KADAMA", layout="wide")
st.markdown("""
    <style>
    .main-title { color: #003399; text-align: center; font-weight: bold; font-size: 36px; margin-bottom: 0px; }
    .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #003399; text-align: center; }
    .oversold-box { background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin-bottom: 5px; border-left: 5px solid #721c24; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ALERTS ---
df_stock = load_data()
st.sidebar.title("IVO HUB 📍")
st.sidebar.subheader("⚠️ Stock Alerts")

# Low Stock Alert
low_stock = df_stock[(df_stock['Stock'] >= 0) & (
    df_stock['Stock'] <= LOW_STOCK_THRESHOLD)]
for _, row in low_stock.iterrows():
    st.sidebar.warning(f"Low Stock: {row['Model']} ({row['Stock']} left)")

# Oversold Alert
oversold = df_stock[df_stock['Stock'] < 0]
for _, row in oversold.iterrows():
    st.sidebar.error(
        f"OVERSOLD: {row['Model']} (Deficit: {abs(row['Stock'])})")

# --- 6. NAVIGATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

menu = ["Shop Counter", "Admin Login"]
if st.session_state.logged_in:
    menu = ["Shop Counter", "Dashboard",
            "Inventory Management", "Credit Records", "Logout"]

choice = st.sidebar.radio("Go to:", menu)

# --- HEADER ---
st.markdown("<h1 class='main-title'>IVO ELECTRONICS - KADAMA</h1>",
            unsafe_allow_html=True)
if os.path.exists(HEADER_IMAGE):
    st.image(HEADER_IMAGE, use_container_width=True)
st.divider()

# --- PAGE: SHOP COUNTER ---
if choice == "Shop Counter":
    st.subheader("🛒 Sales Terminal")
    search = st.text_input("🔍 Search Gadgets (Fuzzy search active)...").lower()

    # Fuzzy Search Logic
    if search:
        all_models = df_stock['Model'].tolist()
        matches = difflib.get_close_matches(
            search, [m.lower() for m in all_models], n=5, cutoff=0.4)
        display_df = df_stock[df_stock['Model'].str.lower().isin(matches)]
    else:
        display_df = df_stock

    cols = st.columns(2)
    for idx, row in display_df.iterrows():
        with cols[idx % 2]:
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                img = fetch_image(row['Model'])
                if img:
                    c1.image(img, use_container_width=True)

                with c2:
                    st.write(f"### {row['Model']}")
                    st.write(
                        f"**Price:** UGX {row['Price']:,} | **In Stock:** {row['Stock']}")
                    qty = st.number_input(
                        "Quantity", min_value=0, key=f"qty_{idx}")
                    on_credit = st.checkbox("Sell on Credit", key=f"cr_{idx}")

                    if st.button("Confirm Sale", key=f"btn_{idx}", use_container_width=True):
                        if qty > 0:
                            # Process Sale
                            profit = (row['Price'] - row['Cost']) * qty
                            sales_df = load_sales()
                            new_sale = pd.DataFrame([{
                                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "Item": row['Model'], "Qty": qty, "SalePrice": row['Price'],
                                "CostPrice": row['Cost'], "Profit": profit,
                                "Month": datetime.now().strftime("%Y-%m")
                            }])
                            save_data(
                                pd.concat([sales_df, new_sale]), SALES_FILE)

                            # Update Stock
                            df_stock.at[idx, 'Stock'] -= qty
                            save_data(df_stock, STOCK_FILE)

                            # Record Debt if applicable
                            if on_credit:
                                credit_df = load_credits()
                                new_debt = pd.DataFrame([{
                                    "Date": datetime.now().strftime("%Y-%m-%d"),
                                    "Customer": "New Customer", "Phone": "07...",
                                    "Item": row['Model'], "Balance": row['Price'] * qty, "Status": "Unpaid"
                                }])
                                save_data(
                                    pd.concat([credit_df, new_debt]), CREDIT_FILE)

                            st.success("Sale Recorded!")
                            st.rerun()

# --- PAGE: ADMIN DASHBOARD ---
elif choice == "Dashboard":
    st.subheader("📊 Business Overview")
    ds = load_sales()
    dc = load_credits()

    m_profit = ds[ds['Month'] == datetime.now().strftime("%Y-%m")
                  ]['Profit'].sum()
    total_debt = dc[dc['Status'] == "Unpaid"]['Balance'].sum()
    stock_val = (df_stock['Price'] * df_stock['Stock']).sum()

    m1, m2, m3 = st.columns(3)
    m1.markdown(
        f"<div class='metric-card'><h4>Monthly Profit</h4><h2>UGX {m_profit:,.0f}</h2></div>", unsafe_allow_html=True)
    m2.markdown(
        f"<div class='metric-card'><h4>Stock Value</h4><h2>UGX {stock_val:,.0f}</h2></div>", unsafe_allow_html=True)
    m3.markdown(
        f"<div class='metric-card'><h4>Total Debt</h4><h2>UGX {total_debt:,.0f}</h2></div>", unsafe_allow_html=True)

    st.write("### Recent Sales")
    st.dataframe(ds.tail(10), use_container_width=True)

# --- PAGE: INVENTORY MANAGEMENT ---
elif choice == "Inventory Management":
    t1, t2 = st.tabs(["Stock List", "Add New Item"])

    with t1:
        for idx, row in df_stock.iterrows():
            with st.expander(f"Edit {row['Model']}"):
                col_a, col_b = st.columns(2)
                u_p = col_a.number_input(
                    "Selling Price", value=int(row['Price']), key=f"up_{idx}")
                u_s = col_b.number_input(
                    "Current Stock", value=int(row['Stock']), key=f"us_{idx}")
                if st.button("Update Item", key=f"ub_{idx}"):
                    df_stock.at[idx, 'Price'] = u_p
                    df_stock.at[idx, 'Stock'] = u_s
                    save_data(df_stock, STOCK_FILE)
                    st.rerun()

    with t2:
        with st.form("new_item"):
            st.write("### Register Product")
            f_model = st.selectbox("Select Model", SUGGESTION_DATABASE)
            manual_model = st.text_input("Or Type Manually")
            final_model = manual_model if manual_model else f_model

            f_cost = st.number_input("Cost Price (Buying)", min_value=0)
            f_price = st.number_input("Selling Price", min_value=0)
            f_stock = st.number_input("Opening Stock Quantity", min_value=1)

            if st.form_submit_button("Add to System"):
                new_row = pd.DataFrame(
                    [{"Brand": "Generic", "Model": final_model, "Price": f_price, "Cost": f_cost, "Stock": f_stock}])
                save_data(pd.concat([df_stock, new_row]), STOCK_FILE)
                st.success(f"{final_model} added!")
                st.rerun()

# --- PAGE: CREDIT RECORDS ---
elif choice == "Credit Records":
    st.subheader("💳 Customer Debts")
    df_c = load_credits()
    st.dataframe(df_c, use_container_width=True)

    if not df_c.empty:
        unpaid = df_c[df_c['Status'] == "Unpaid"]
        if not unpaid.empty:
            customer_to_pay = st.selectbox(
                "Mark Paid:", unpaid['Customer'].unique())
            if st.button("Mark as PAID"):
                df_c.loc[df_c['Customer'] ==
                         customer_to_pay, 'Status'] = "PAID"
                save_data(df_c, CREDIT_FILE)
                st.success("Record Updated!")
                st.rerun()

# --- LOGIN / LOGOUT ---
elif choice == "Admin Login":
    code = st.text_input("Enter Admin PIN", type="password")
    if st.button("Login"):
        if code in ["1111", "2222"]:  # Master PINs for partners
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid Code")

elif choice == "Logout":
    st.session_state.logged_in = False
    st.rerun()
