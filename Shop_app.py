<<<<<<< HEAD
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
=======
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
import requests
import difflib  # For spell-correction/fuzzy matching
from duckduckgo_search import DDGS

# --- 1. CONFIGURATION & SECURITY ---
PARTNER_A_PIN = "1111"
PARTNER_B_PIN = "2222"
PASSWORD_FILE = "admin_config.json"
IMAGE_FOLDER = "item_images"
HEADER_FILE = "ivo_header.jpg"

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# --- 2. GADGET DATABASE (FULL TECNO LIST) ---
SUGGESTION_DATABASE = [
    "TECNO Phantom V Flip 2", "TECNO Phantom V Fold 2", "TECNO Camon 30 Premier",
    "TECNO Camon 30 Pro", "TECNO Camon 30 5G", "TECNO Camon 20 Pro", "TECNO Camon 20",
    "TECNO Spark 20 Pro+", "TECNO Spark 20 Pro", "TECNO Spark 20", "TECNO Spark 20C",
    "TECNO Pop 8", "TECNO Pop 7", "TECNO Pova 6 Pro", "TECNO Pova 5",
    "Infinix Note 40 Pro", "Infinix Hot 40 Pro", "Infinix Smart 8",
    "Itel A70", "Itel P55+", "Itel S23 Plus",
    "Samsung Galaxy S24 Ultra", "iPhone 15 Pro Max", "Oraimo 20000mAh Powerbank",
    "Sony Smart TV 55 inch", "HP Laptop 15", "Digital TV Guard", "Extension 6-Way"
]

# --- 3. CORE ENGINE FUNCTIONS ---


def display_welcome_header():
    """Permanent heading at the top of the welcome page."""
    st.markdown("<h1 style='text-align: center;'>📱 IVO Electronics - KADAMA</h1>",
                unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: gray;'>Official Shop Management System</h4>",
                unsafe_allow_html=True)
    if os.path.exists(HEADER_FILE):
        st.image(HEADER_FILE, use_container_width=True)
    st.divider()


@st.cache_data(show_spinner=False)
def download_item_image(item_name):
    clean_name = "".join(
        [c for c in item_name if c.isalnum() or c == ' ']).strip()
    save_path = os.path.join(IMAGE_FOLDER, f"{clean_name}.jpg")
    if os.path.exists(save_path):
        return save_path
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(
                f"{item_name} official smartphone", max_results=1))
            if results:
                resp = requests.get(results[0]['image'], timeout=5)
                if resp.status_code == 200:
                    with open(save_path, 'wb') as f:
                        f.write(resp.content)
                    return save_path
    except:
        return None
    return None


def load_admin_password():
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r") as f:
            try:
                return json.load(f).get("password", "1234")
            except:
                return "1234"
    return "1234"


def save_all_data():
    pd.DataFrame(st.session_state.inventory).to_csv(
        "inventory.csv", index=False)
    if st.session_state.sales_history:
        pd.DataFrame(st.session_state.sales_history).to_csv(
            "sales_history.csv", index=False)
    if st.session_state.debts:
        pd.DataFrame(st.session_state.debts).to_csv("debts.csv", index=False)


def load_all_data():
    if 'inventory' not in st.session_state:
        if os.path.exists("inventory.csv"):
            st.session_state.inventory = pd.read_csv(
                "inventory.csv").to_dict('records')
        else:
            st.session_state.inventory = [
                {"name": "TECNO Camon 30", "price": 1200000, "cost": 950000, "stock": 10}]

    if 'sales_history' not in st.session_state:
        if os.path.exists("sales_history.csv"):
            df = pd.read_csv("sales_history.csv")
            if not df.empty:
                df['Date'] = pd.to_datetime(df['Date'])
                df['Month'] = df['Date'].dt.strftime('%Y-%m')
            st.session_state.sales_history = df.to_dict('records')
        else:
            st.session_state.sales_history = []

    if 'debts' not in st.session_state:
        if os.path.exists("debts.csv"):
            st.session_state.debts = pd.read_csv(
                "debts.csv").to_dict('records')
        else:
            st.session_state.debts = []


# --- 4. INITIALIZATION ---
st.set_page_config(page_title="IVO Electronics - KADAMA", layout="wide")
load_all_data()

if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
if 'editing_index' not in st.session_state:
    st.session_state.editing_index = None
if 'admin_password' not in st.session_state:
    st.session_state.admin_password = load_admin_password()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("IVO HUB")
    user_role = st.radio("Access Level:", ["Shop Attendant", "ADMIN"])

    if user_role == "ADMIN" and not st.session_state.is_logged_in:
        pwd_input = st.text_input("Admin Password:", type="password")
        if st.button("Unlock Admin"):
            if pwd_input == st.session_state.admin_password:
                st.session_state.is_logged_in = True
                st.rerun()
            else:
                st.error("Wrong Password")

    st.divider()
    st.info("📍 Kadama, Uganda")

    st.subheader("⚠️ Stock Alerts")
    for item in st.session_state.inventory:
        if item.get('stock', 0) <= 2:
            st.warning(f"{item['name']}: {item['stock']} left")

# --- 6. MAIN PAGE START ---
display_welcome_header()

# --- SHOP ATTENDANT INTERFACE ---
if user_role == "Shop Attendant":
    st.subheader("🛒 Shop Sales Counter")
    tab_sales, tab_debt = st.tabs(["Daily Sales", "Customer Debts"])

    with tab_sales:
        raw_search = st.text_input(
            "🔍 Search Gadgets (Fuzzy search active)...").strip().lower()

        # Fuzzy Match / Spell Correction Logic
        all_item_names = [x['name'] for x in st.session_state.inventory]
        if raw_search:
            # Matches names that are 60% similar or better
            matches = difflib.get_close_matches(
                raw_search, [n.lower() for n in all_item_names], n=5, cutoff=0.4)
            items = [(i, x) for i, x in enumerate(
                st.session_state.inventory) if x['name'].lower() in matches]
        else:
            items = list(enumerate(st.session_state.inventory))

        for idx, item in items:
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 2, 1])
                with c1:
                    img = download_item_image(item['name'])
                    if img:
                        st.image(img, width=150)
                with c2:
                    st.subheader(item['name'])
                    st.write(
                        f"**Price:** UGX {item['price']:,} | **Stock:** {item['stock']}")
                with c3:
                    qty = st.number_input("Qty", min_value=0, max_value=int(
                        item['stock']), value=0, key=f"s_{idx}")
                    if st.button("Confirm Sale", key=f"b_{idx}"):
                        if qty > 0:
                            st.session_state.inventory[idx]['stock'] -= qty
                            st.session_state.sales_history.append({
                                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "Month": datetime.now().strftime("%Y-%m"),
                                "Item": item['name'], "Qty": qty,
                                "Total Sale": item['price'] * qty,
                                "Net Profit": (item['price'] - item['cost']) * qty
                            })
                            save_all_data()
                            st.success("Sale Recorded!")
                            st.rerun()

    with tab_debt:
        st.subheader("Record New Debt")
        with st.form("debt_form"):
            customer = st.text_input("Customer Name")
            contact = st.text_input("Phone Number")
            item_debt = st.selectbox(
                "Item Taken", [i['name'] for i in st.session_state.inventory])
            amount_due = st.number_input("Amount Remaining (UGX)", min_value=0)
            if st.form_submit_button("Save Debt"):
                st.session_state.debts.append({
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Customer": customer, "Contact": contact,
                    "Item": item_debt, "Balance": amount_due, "Status": "Unpaid"
                })
                save_all_data()
                st.success("Debt Saved!")
                st.rerun()

# --- ADMIN MANAGEMENT INTERFACE ---
if user_role == "ADMIN" and st.session_state.is_logged_in:
    st.subheader("🛠️ Management Control Panel")
    t1, t2, t3, t4 = st.tabs(
        ["📊 Profit Reports", "📥 Stock Control", "💰 Debt Recovery", "🔐 Security"])

    with t1:
        st.header("Financial Performance")
        if st.session_state.sales_history:
            df = pd.DataFrame(st.session_state.sales_history)
            months = ["All Time"] + \
                sorted(df['Month'].unique().tolist(), reverse=True)
            sel_m = st.selectbox("📅 Filter by Month:", months)
            view_df = df if sel_m == "All Time" else df[df['Month'] == sel_m]
            ca, cb = st.columns(2)
            ca.metric("Total Revenue", f"UGX {view_df['Total Sale'].sum():,}")
            cb.metric("Total Profit", f"UGX {view_df['Net Profit'].sum():,}")
            st.dataframe(view_df.sort_values(by="Date", ascending=False))

    with t2:
        st.header("Inventory Management")
        # Quick Restock
        with st.expander("➕ Quick Restock Existing Items"):
            item_to_r = st.selectbox(
                "Select Item", [i['name'] for i in st.session_state.inventory])
            add_q = st.number_input("Units to Add", min_value=1, value=1)
            if st.button("Add to Stock"):
                for i in st.session_state.inventory:
                    if i['name'] == item_to_r:
                        i['stock'] += add_q
                        save_all_data()
                        st.success("Stock Updated!")
                        st.rerun()

        st.divider()
        # Item List with Edit/Delete
        for i, item in enumerate(st.session_state.inventory):
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(
                    f"**{item['name']}** | Price: {item['price']:,} | Stock: {item['stock']}")
                if col2.button("✏️ Edit", key=f"ed_{i}"):
                    st.session_state.editing_index = i
                    st.rerun()
                if col3.button("🗑️ Delete", key=f"del_{i}"):
                    st.session_state.inventory.pop(i)
                    save_all_data()
                    st.rerun()

        # Add/Edit Form
        st.divider()
        e_idx = st.session_state.editing_index
        with st.form("edit_form", clear_on_submit=True):
            st.subheader(
                "Modify Product" if e_idx is not None else "Add New Product")
            f_name = st.selectbox("Select From List", SUGGESTION_DATABASE) if e_idx is None else st.text_input(
                "Name", value=st.session_state.inventory[e_idx]['name'])
            # Support for manual entry even in Add mode
            if e_idx is None:
                manual_name = st.text_input(
                    "Or Type Manually (if not in list)")
                if manual_name:
                    f_name = manual_name

            f_p = st.number_input("Selling Price (UGX)", value=int(
                st.session_state.inventory[e_idx]['price']) if e_idx is not None else 0)
            f_c = st.number_input("Cost Price (UGX)", value=int(
                st.session_state.inventory[e_idx]['cost']) if e_idx is not None else 0)
            f_s = st.number_input("Stock", value=int(
                st.session_state.inventory[e_idx]['stock']) if e_idx is not None else 0)

            if st.form_submit_button("Save Changes"):
                new_item = {"name": f_name, "price": f_p,
                            "cost": f_c, "stock": f_s}
                if e_idx is not None:
                    st.session_state.inventory[e_idx] = new_item
                else:
                    st.session_state.inventory.append(new_item)
                st.session_state.editing_index = None
                save_all_data()
                st.success("Database Updated!")
                st.rerun()

    with t3:
        st.header("Debt Management")
        if st.session_state.debts:
            df_d = pd.DataFrame(st.session_state.debts)
            st.dataframe(df_d)
            clear_n = st.selectbox("Select Customer to Clear:", [
                                   d['Customer'] for d in st.session_state.debts if d['Status'] == "Unpaid"])
            if st.button("Mark as PAID"):
                for d in st.session_state.debts:
                    if d['Customer'] == clear_n:
                        d['Status'] = "PAID"
                save_all_data()
                st.success("Status Updated!")
                st.rerun()
        else:
            st.info("No current debts recorded.")

    with t4:
        st.header("Partner Security Reset")
        with st.form("sec_form"):
            new_p = st.text_input("New Admin Password", type="password")
            pA = st.text_input("Partner A PIN", type="password")
            pB = st.text_input("Partner B PIN", type="password")
            if st.form_submit_button("Reset Master Password"):
                if pA == PARTNER_A_PIN and pB == PARTNER_B_PIN:
                    st.session_state.admin_password = new_p
                    with open(PASSWORD_FILE, "w") as f:
                        json.dump({"password": new_p}, f)
                    st.success("Security Updated!")
                    st.rerun()
                else:
                    st.error("Verification Failed: PINs incorrect")
>>>>>>> d8109272ea1c8a2c7db6b1d66ed6c2b965ef88f7
