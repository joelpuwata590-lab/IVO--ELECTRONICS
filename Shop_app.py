import streamlit as st
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="IVO Electronics - KADAMA", layout="wide")

# --- SETTINGS ---
LOW_STOCK_THRESHOLD = 2
HEADER_IMAGE = 'ivo_header.jpg'
IMAGE_FOLDER = 'item_images'
STOCK_FILE = 'ivo_inventory.csv'
CREDIT_FILE = 'ivo_credits.csv'
SALES_FILE = 'ivo_sales_history.csv'
ADMIN1_PASS_FILE = 'ivo_admin1.txt'
ADMIN2_PASS_FILE = 'ivo_admin2.txt'

# Ensure password files exist
for f_path, default in [(ADMIN1_PASS_FILE, "1111"), (ADMIN2_PASS_FILE, "2222")]:
    if not os.path.exists(f_path):
        with open(f_path, 'w') as f:
            f.write(default)


def get_admin_passwords():
    try:
        with open(ADMIN1_PASS_FILE, 'r') as f:
            a1 = f.read().strip()
        with open(ADMIN2_PASS_FILE, 'r') as f:
            a2 = f.read().strip()
        return a1, a2
    except:
        return "1111", "2222"


# Ensure directories exist
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

session = requests.Session()
session.headers.update(
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

# --- IMAGE DOWNLOADER ---


def fetch_and_save_image(model_name, force_refresh=False):
    safe_filename = "".join(
        [c for c in model_name if c.isalnum() or c in (' ', '_')]).rstrip()
    save_path = os.path.join(IMAGE_FOLDER, f"{safe_filename}.jpg")
    if os.path.exists(save_path) and not force_refresh:
        return save_path
    try:
        search_url = f"https://www.google.com/search?q={quote(model_name)}+phone+product+image&tbm=isch"
        response = session.get(search_url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all("img")
        if len(img_tags) > 1:
            img_url = img_tags[1].get("src")
            img_data = session.get(img_url, timeout=5).content
            with open(save_path, 'wb') as handler:
                handler.write(img_data)
            return save_path
    except:
        pass
    return None

# --- DATA HELPERS ---


def load_data():
    if os.path.exists(STOCK_FILE):
        df = pd.read_csv(STOCK_FILE)
        if "Cost" not in df.columns:
            df["Cost"] = 0
        return df
    return pd.DataFrame([{"Brand": "Apple", "Model": "iPhone 15 Pro Max", "Price": 5500000, "Cost": 5000000, "Stock": 2}])


def load_credits():
    if os.path.exists(CREDIT_FILE):
        return pd.read_csv(CREDIT_FILE)
    return pd.DataFrame(columns=["Date", "Customer", "Phone", "Item", "Qty", "Total"])


def load_sales():
    if os.path.exists(SALES_FILE):
        return pd.read_csv(SALES_FILE)
    return pd.DataFrame(columns=["Date", "Item", "Qty", "SalePrice", "CostPrice", "Profit"])


def save_data(df, filename):
    df.to_csv(filename, index=False)


df_stock = load_data()

# --- CSS ---
st.markdown("""
    <style>
    .main-title { color: #003399; text-align: center; font-weight: bold; font-size: 42px; }
    .product-card { background-color: #ffffff; padding: 15px; border-radius: 0 0 10px 10px; border: 1px solid #e0e0e0; text-align: center; }
    .item-highlight { color: #ffffff; background-color: #003399; text-align: center; font-weight: bold; font-size: 22px; padding: 12px; border-radius: 10px 10px 0 0; }
    .price-tag { color: #d32f2f; font-size: 28px; font-weight: bold; }
    .profit-card { background-color: #e8f5e9; padding: 20px; border-radius: 10px; border-left: 5px solid #2e7d32; text-align: center; }
    .metric-card { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #003399; text-align: center; }
    .low-stock-box { background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; border: 1px solid #ffeeba; margin-bottom: 5px; font-size: 14px; }
    .oversold-box { background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; border: 1px solid #f5c6cb; margin-bottom: 5px; font-size: 14px; border-left: 5px solid #721c24; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h1 class='main-title'>IVO ELECTRONICS - KADAMA</h1>",
            unsafe_allow_html=True)
if os.path.exists(HEADER_IMAGE):
    st.image(HEADER_IMAGE, use_container_width=True)

# --- SIDEBAR: ALERTS ---
st.sidebar.header("⚠️ Inventory Alerts")

# 1. Monthly Overselling Alert
st.sidebar.subheader("Monthly Oversold")
df_sales_alert = load_sales()
if not df_sales_alert.empty:
    df_sales_alert['Date'] = pd.to_datetime(df_sales_alert['Date'])
    current_month_sales = df_sales_alert[df_sales_alert['Date'].dt.month == datetime.now(
    ).month]
    oversold_items = df_stock[df_stock['Stock'] < 0]

    if not oversold_items.empty:
        for _, row in oversold_items.iterrows():
            st.sidebar.markdown(
                f"""<div class='oversold-box'><strong>🚨 OVERSOLD: {row['Model']}</strong><br>Deficit: {abs(row['Stock'])} units</div>""", unsafe_allow_html=True)
    else:
        st.sidebar.write("No items oversold this month.")

# 2. Low Stock Alert
st.sidebar.subheader("Low Stock")
low_stock_items = df_stock[(df_stock['Stock'] >= 0) & (
    df_stock['Stock'] <= LOW_STOCK_THRESHOLD)]
if not low_stock_items.empty:
    for _, row in low_stock_items.iterrows():
        st.sidebar.markdown(
            f"""<div class='low-stock-box'><strong>{row['Model']}</strong><br>Remaining: {row['Stock']}</div>""", unsafe_allow_html=True)
else:
    st.sidebar.success("Stock levels healthy.")

st.sidebar.divider()

# --- NAVIGATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
page_options = ["Attendant", "Admin Login"]
if st.session_state.logged_in:
    page_options = ["Attendant", "Admin Dashboard", "Inventory Management",
                    "Credit Records", "Security Settings", "Logout"]
page = st.sidebar.radio("Navigation", page_options)

# --- 1. ATTENDANT ---
if page == "Attendant":
    search = st.text_input("🔍 Search stock...", "").lower()
    display_df = df_stock[df_stock['Model'].str.lower(
    ).str.contains(search)] if search else df_stock
    cols = st.columns(2)
    for index, row in display_df.iterrows():
        with cols[index % 2]:
            st.markdown(
                f"<div class='item-highlight'>{row['Model']}</div>", unsafe_allow_html=True)
            safe_name = "".join(
                [c for c in row['Model'] if c.isalnum() or c in (' ', '_')]).rstrip()
            img_path = os.path.join(IMAGE_FOLDER, f"{safe_name}.jpg")
            if os.path.exists(img_path):
                st.image(img_path, use_container_width=True)
            else:
                fetch_and_save_image(row['Model'])

            st.markdown(
                f"<div class='product-card'><div class='price-tag'>UGX {row['Price']:,.0f}</div><div>Stock: {row['Stock']}</div></div>", unsafe_allow_html=True)

            qty = st.number_input(f"Qty", min_value=0,
                                  value=0, key=f"q_{index}")

            if qty > row['Stock']:
                st.warning(
                    f"Overselling: {qty - row['Stock']} unit(s) will be backordered.")

            on_credit = st.checkbox(f"Sell on Credit", key=f"cr_{index}")
            c_name, c_phone = "", ""
            if on_credit:
                c_name = st.text_input("Customer Name", key=f"cn_{index}")
                c_phone = st.text_input("Phone", key=f"cp_{index}")

            if st.button(f"Confirm Sale", key=f"bt_{index}"):
                if qty > 0:
                    df_sales = load_sales()
                    profit = (row['Price'] - row['Cost']) * qty
                    new_s = pd.DataFrame([{"Date": datetime.now().strftime(
                        "%Y-%m-%d"), "Item": row['Model'], "Qty": qty, "SalePrice": row['Price'], "CostPrice": row['Cost'], "Profit": profit}])
                    save_data(pd.concat([df_sales, new_s]), SALES_FILE)
                    df_stock.at[index, 'Stock'] -= qty
                    save_data(df_stock, STOCK_FILE)
                    if on_credit:
                        df_c = load_credits()
                        new_c = pd.DataFrame([{"Date": datetime.now().strftime(
                            "%Y-%m-%d %H:%M"), "Customer": c_name, "Phone": c_phone, "Item": row['Model'], "Qty": qty, "Total": qty * row['Price']}])
                        save_data(pd.concat([df_c, new_c]), CREDIT_FILE)
                    st.rerun()

# --- 2. ADMIN DASHBOARD ---
elif page == "Admin Dashboard":
    st.subheader("📊 Business Overview")
    ds, dc = load_sales(), load_credits()
    ds['Date'] = pd.to_datetime(ds['Date'])
    m_profit = ds[ds['Date'].dt.month == datetime.now().month]['Profit'].sum()

    m1, m2, m3 = st.columns(3)
    m1.markdown(
        f"<div class='profit-card'><h3>Monthly Profit</h3><h2>UGX {m_profit:,.0f}</h2></div>", unsafe_allow_html=True)
    m2.markdown(
        f"<div class='metric-card'><h3>Stock Value</h3><h2>UGX {(df_stock['Price']*df_stock['Stock']).sum():,.0f}</h2></div>", unsafe_allow_html=True)
    m3.markdown(
        f"<div class='metric-card'><h3>Total Debt</h3><h2>UGX {dc['Total'].sum():,.0f}</h2></div>", unsafe_allow_html=True)
    st.dataframe(ds.tail(10), use_container_width=True)

# --- 3. INVENTORY MANAGEMENT ---
elif page == "Inventory Management":
    t1, t2 = st.tabs(["Edit Stock", "Add New"])
    with t1:
        for idx, row in df_stock.iterrows():
            with st.expander(f"Edit {row['Model']}"):
                eb = st.text_input("Brand", row['Brand'], key=f"eb{idx}")
                em = st.text_input("Model", row['Model'], key=f"em{idx}")
                ep = st.number_input("Price", value=int(
                    row['Price']), key=f"ep{idx}")
                ec = st.number_input("Cost", value=int(
                    row['Cost']), key=f"ec{idx}")
                es = st.number_input("Stock", value=int(
                    row['Stock']), key=f"es{idx}")
                if st.button("Save Changes", key=f"sv{idx}"):
                    fetch_and_save_image(em, force_refresh=True)
                    df_stock.loc[idx, ['Brand', 'Model', 'Price',
                                       'Cost', 'Stock']] = [eb, em, ep, ec, es]
                    save_data(df_stock, STOCK_FILE)
                    st.rerun()
                if st.button("Delete Item", key=f"dl{idx}"):
                    df_stock = df_stock.drop(idx)
                    save_data(df_stock, STOCK_FILE)
                    st.rerun()
    with t2:
        with st.form("new_p"):
            nb, nm = st.text_input("Brand"), st.text_input("Model")
            np, nc, ns = st.number_input("Price"), st.number_input(
                "Cost"), st.number_input("Stock")
            if st.form_submit_button("Add Product"):
                fetch_and_save_image(nm)
                new_p = pd.DataFrame(
                    [{"Brand": nb, "Model": nm, "Price": np, "Cost": nc, "Stock": ns}])
                save_data(pd.concat([df_stock, new_p]), STOCK_FILE)
                st.rerun()

# --- 4. CREDIT RECORDS ---
elif page == "Credit Records":
    st.subheader("💳 Customer Debts")
    st.dataframe(load_credits(), use_container_width=True)

# --- 5. SECURITY SETTINGS ---
elif page == "Security Settings":
    st.subheader("🔐 Change Passwords")
    with st.form("sec"):
        v1, v2 = st.text_input("Current Admin 1", type="password"), st.text_input(
            "Current Admin 2", type="password")
        n1, n2 = st.text_input("New Admin 1", type="password"), st.text_input(
            "New Admin 2", type="password")
        if st.form_submit_button("Update Codes"):
            c1, c2 = get_admin_passwords()
            if v1 == c1 and v2 == c2:
                with open(ADMIN1_PASS_FILE, 'w') as f:
                    f.write(n1)
                with open(ADMIN2_PASS_FILE, 'w') as f:
                    f.write(n2)
                st.success("Updated!")
            else:
                st.error("Verification failed")

# --- LOGIN/LOGOUT ---
elif page == "Admin Login":
    pwd = st.text_input("Secret Code", type="password")
    if st.button("Login"):
        a1, a2 = get_admin_passwords()
        if pwd in [a1, a2]:
            st.session_state.logged_in = True
            st.rerun()
elif page == "Logout":
    st.session_state.logged_in = False
    st.rerun()
