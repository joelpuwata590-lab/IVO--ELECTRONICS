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
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
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
