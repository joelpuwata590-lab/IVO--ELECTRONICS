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
IMAGE_FOLDER = 'item_images'
HEADER_IMAGE = 'ivo_header.jpg'
LOW_STOCK_THRESHOLD = 2

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# --- 2. THE TEST SAMPLES ---
# This list will be added if your inventory is currently empty.
SAMPLE_DATA = [
    {"Brand": "TECNO", "Model": "TECNO Spark 20 Pro+",
        "Price": 950000, "Cost": 800000, "Stock": 5},
    {"Brand": "Infinix", "Model": "Infinix Smart 8",
        "Price": 450000, "Cost": 380000, "Stock": 10},
    {"Brand": "Samsung", "Model": "Samsung Galaxy S24 Ultra",
        "Price": 5200000, "Cost": 4500000, "Stock": 2},
    {"Brand": "Oraimo", "Model": "Oraimo 20000mAh Powerbank",
        "Price": 120000, "Cost": 85000, "Stock": 15},
    {"Brand": "Apple", "Model": "iPhone 15 Pro Max",
        "Price": 6500000, "Cost": 5800000, "Stock": 1},
    {"Brand": "Generic", "Model": "Digital TV Guard",
        "Price": 45000, "Cost": 30000, "Stock": 20}
]

# --- 3. DATA ENGINE ---


def load_data():
    if os.path.exists(STOCK_FILE):
        return pd.read_csv(STOCK_FILE)
    else:
        # If no file exists, create one with the 6 sample items
        df = pd.DataFrame(SAMPLE_DATA)
        df.to_csv(STOCK_FILE, index=False)
        return df


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
    .main-title { color: #003399; text-align: center; font-weight: bold; font-size: 36px; margin-bottom: 10px; }
    .price-text { color: #d32f2f; font-size: 24px; font-weight: bold; }
    .stock-text { color: #555; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# Load data at start
df_stock = load_data()

# --- 5. SIDEBAR ---
st.sidebar.title("IVO HUB 📍")
st.sidebar.subheader("⚠️ Stock Alerts")
low_stock = df_stock[(df_stock['Stock'] >= 0) & (
    df_stock['Stock'] <= LOW_STOCK_THRESHOLD)]
for _, row in low_stock.iterrows():
    st.sidebar.warning(f"Low Stock: {row['Model']} ({row['Stock']} left)")

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
st.divider()

# --- PAGE: SHOP COUNTER ---
if choice == "Shop Counter":
    st.subheader("🛒 Sales Counter")
    search = st.text_input("🔍 Search for a phone or gadget...", "").lower()

    if search:
        all_models = df_stock['Model'].tolist()
        matches = difflib.get_close_matches(
            search, [m.lower() for m in all_models], n=5, cutoff=0.3)
        display_df = df_stock[df_stock['Model'].str.lower().isin(matches)]
    else:
        display_df = df_stock

    cols = st.columns(2)
    for idx, row in display_df.iterrows():
        with cols[idx % 2]:
            with st.container(border=True):
                c1, c2 = st.columns([1, 1.5])
                with c1:
                    img = fetch_image(row['Model'])
                    if img:
                        st.image(img, use_container_width=True)
                    else:
                        st.info("No Image")
                with c2:
                    st.markdown(f"## {row['Model']}")
                    st.markdown(
                        f"<span class='price-text'>UGX {row['Price']:,}</span>", unsafe_allow_html=True)
                    st.markdown(
                        f"<p class='stock-text'>In Stock: <b>{row['Stock']}</b></p>", unsafe_allow_html=True)

                    qty = st.number_input(
                        "Qty", min_value=0, step=1, key=f"qty_{idx}")
                    if st.button(f"Confirm Sale", key=f"btn_{idx}", use_container_width=True, type="primary"):
                        if qty > 0:
                            # Save Sale
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

                            # Deduct Stock
                            df_stock.at[idx, 'Stock'] -= qty
                            save_data(df_stock, STOCK_FILE)
                            st.success("Sale Recorded!")
                            st.rerun()

# --- ADMIN LOGIN ---
elif choice == "Admin Login":
    pin = st.text_input("Enter Partner PIN", type="password")
    if st.button("Login"):
        if pin in ["1111", "2222"]:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Wrong PIN")

elif choice == "Logout":
    st.session_state.logged_in = False
    st.rerun()

# (The Dashboard and Inventory pages remain the same as previous versions)
