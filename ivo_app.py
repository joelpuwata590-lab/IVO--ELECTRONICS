import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTINGS & PATHS ---
STOCK_FILE = 'inventory.csv'
SALES_FILE = 'sales_log.csv'
CONFIG_FILE = 'config.txt'
IMAGE_FOLDER = 'item_images'
HEADER_IMAGE = 'ivo_header.jpg'

# --- SECURITY KEYS ---
IVO_KEY = "IVO_123"
OTHER_KEY = "PARTNER_456"

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)


def get_admin_password():
    default_pw = "IVO_MASTER_2026"
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                content = f.read().strip()
                return content if content else default_pw
        except Exception:
            return default_pw
    return default_pw


def save_admin_password(new_pw):
    with open(CONFIG_FILE, 'w') as f:
        f.write(new_pw.strip())

# --- 2. DATA & SALES LOGGING ---


def load_data():
    if os.path.exists(STOCK_FILE):
        return pd.read_csv(STOCK_FILE)
    else:
        data = [
            {"Category": "Smartphone", "Brand": "TECNO", "Model": "Spark 20 Pro+",
                "Cost": 800000, "Price": 950000, "Stock": 10},
            {"Category": "Subwoofer", "Brand": "Sayona", "Model": "SHT-1133BT",
                "Cost": 280000, "Price": 350000, "Stock": 5},
        ]
        df = pd.DataFrame(data)
        df.to_csv(STOCK_FILE, index=False)
        return df


def log_sale(row, is_credit=False):
    profit = (row['Price'] - row['Cost']) if not is_credit else 0
    sale_type = "CASH" if not is_credit else "CREDIT"

    new_sale = pd.DataFrame([{
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Item": f"{row['Brand']} {row['Model']}",
        "Price Sold": row['Price'],
        "Profit": profit,
        "Type": sale_type
    }])

    df = pd.read_csv(STOCK_FILE)
    df.loc[df['Model'] == row['Model'], 'Stock'] -= 1
    df.to_csv(STOCK_FILE, index=False)

    if os.path.exists(SALES_FILE):
        new_sale.to_csv(SALES_FILE, mode='a', header=False, index=False)
    else:
        new_sale.to_csv(SALES_FILE, index=False)


# --- 3. INTERFACE ---
st.set_page_config(page_title="IVO Electronics - KADAMA", layout="wide")

st.markdown("""
    <style>
    .main-title { color: white; background-color: #003399; text-align: center; font-weight: bold; font-size: 46px; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .counter-highlight { background-color: #e3f2fd; color: #003399; padding: 10px; border-radius: 5px; font-weight: bold; display: inline-block; width: 100%; margin-bottom: 15px; }
    .price-tag { color: white; background: #d32f2f; padding: 10px; border-radius: 5px; font-weight: bold; font-size: 22px; text-align: center; }
    .item-title { min-height: 60px; font-size: 22px; font-weight: bold; color: #333; margin-top: 10px;}
    .stat-card { background: white; padding: 15px; border-radius: 10px; border: 2px solid #003399; text-align: center; margin-bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

df_stock = load_data()
current_admin_pw = get_admin_password()

if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False

# Sidebar logic
st.sidebar.title("IVO HUB 📍")
low_stock_items = df_stock[df_stock['Stock'] <= 2]
if not low_stock_items.empty:
    st.sidebar.error("⚠️ LOW STOCK ALERT!")
    for _, item in low_stock_items.iterrows():
        st.sidebar.write(f"**{item['Model']}**: only {item['Stock']} left")

mode = st.sidebar.radio("Select Area:", ["Attendant Area", "Admin Area"])

if st.sidebar.button("Lock Admin Panel"):
    st.session_state["admin_authenticated"] = False
    st.rerun()

# --- ATTENDANT AREA ---
if mode == "Attendant Area":
    st.markdown("<div class='main-title'>IVO ELECTRONICS - KADAMA</div>",
                unsafe_allow_html=True)

    if os.path.exists(HEADER_IMAGE):
        st.image(HEADER_IMAGE, use_container_width=True)

    # --- FEATURE: TOP SELLER DISPLAY (FIXED DATE HANDLING) ---
    if os.path.exists(SALES_FILE):
        s_df = pd.read_csv(SALES_FILE)
        # FIX: Added format='mixed' to prevent app collapse
        s_df['Date'] = pd.to_datetime(s_df['Date'], format='mixed')
        now = datetime.now()
        m_data = s_df[(s_df['Date'].dt.month == now.month)
                      & (s_df['Date'].dt.year == now.year)]

        if not m_data.empty:
            top_item = m_data['Item'].value_counts().idxmax()
            top_count = m_data['Item'].value_counts().max()
            st.markdown(f"""
                <div class='stat-card'>
                    <h3 style='margin:0; color:#003399;'>🏆 MOST SELLING ITEM THIS MONTH</h3>
                    <h2 style='margin:10px 0;'>{top_item}</h2>
                    <p style='margin:0; font-weight:bold;'>Total Units Sold: {top_count}</p>
                </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.markdown("<div class='counter-highlight'>🛒 SHOP COUNTER</div>",
                unsafe_allow_html=True)

    search = st.text_input("🔍 Search Brand or Model...")
    display_df = df_stock[df_stock['Model'].str.contains(
        search, case=False) | df_stock['Brand'].str.contains(search, case=False)] if search else df_stock

    cols = st.columns(2, gap="medium")
    for idx, row in display_df.iterrows():
        with cols[idx % 2]:
            with st.container(border=True):
                model_name = str(row['Model']).strip()
                img_path = None
                for ext in ['.jpg', '.jpeg', '.png']:
                    test_path = os.path.join(
                        IMAGE_FOLDER, f"{model_name}{ext}")
                    if os.path.exists(test_path):
                        img_path = test_path
                        break

                if img_path:
                    st.image(img_path, use_container_width=True)
                else:
                    st.info(f"📸 No image for {model_name}")

                st.markdown(
                    f"<div class='item-title'>{row['Brand']} {row['Model']}</div>", unsafe_allow_html=True)
                st.write(f"**Stock:** {row['Stock']} left")
                st.markdown(
                    f"<div class='price-tag'>UGX {row['Price']:,}</div>", unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                if c1.button("LOG SALE", key=f"s_{idx}", use_container_width=True):
                    log_sale(row, is_credit=False)
                    st.success("Cash Sale Recorded!")
                    st.rerun()
                if c2.button("CREDIT", key=f"c_{idx}", use_container_width=True):
                    log_sale(row, is_credit=True)
                    st.warning("Credit Sale Logged!")
                    st.rerun()

# --- ADMIN AREA ---
elif mode == "Admin Area":
    if not st.session_state["admin_authenticated"]:
        pw_input = st.text_input(
            "Admin Master Password", type="password").strip()
        if st.button("Login"):
            if pw_input == current_admin_pw:
                st.session_state["admin_authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect Password.")
    else:
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📦 Stock List", "➕ Add Item", "💰 Profits & Stats", "🔐 Security"])

        with tab1:
            st.subheader("Manage Inventory")
            updated_df = st.data_editor(
                df_stock, use_container_width=True, num_rows="dynamic")
            if st.button("Save Changes"):
                updated_df.to_csv(STOCK_FILE, index=False)
                st.success("Stock updated!")

        with tab2:
            st.subheader("Add Product")
            with st.form("new_item"):
                b, m, c = st.text_input("Brand"), st.text_input("Model"), st.selectbox(
                    "Type", ["Smartphone", "Subwoofer", "TV", "Other"])
                cost, price, stock = st.number_input("Cost"), st.number_input(
                    "Price"), st.number_input("Stock")
                if st.form_submit_button("Add Item"):
                    new_row = pd.DataFrame(
                        [{"Category": c, "Brand": b, "Model": m, "Cost": cost, "Price": price, "Stock": stock}])
                    pd.concat([df_stock, new_row], ignore_index=True).to_csv(
                        STOCK_FILE, index=False)
                    st.success("Added!")

        with tab3:
            st.subheader("Business Performance")
            if os.path.exists(SALES_FILE):
                sales_df = pd.read_csv(SALES_FILE)
                # FIX: Added format='mixed' to prevent app collapse
                sales_df['Date'] = pd.to_datetime(
                    sales_df['Date'], format='mixed')
                now = datetime.now()
                monthly_data = sales_df[(sales_df['Date'].dt.month == now.month) & (
                    sales_df['Date'].dt.year == now.year)]

                m1, m2 = st.columns(2)
                total_monthly_profit = monthly_data['Profit'].sum()
                m1.markdown(
                    f"<div style='background:#e8f5e9; padding:15px; border-radius:10px; text-align:center;'><h3>Monthly Profit</h3><h2 style='color:green;'>UGX {total_monthly_profit:,}</h2></div>", unsafe_allow_html=True)

                if not monthly_data.empty:
                    most_sold = monthly_data['Item'].value_counts().idxmax()
                    sold_count = monthly_data['Item'].value_counts().max()
                    m2.markdown(
                        f"<div style='background:#e3f2fd; padding:15px; border-radius:10px; text-align:center;'><h3>Top Seller</h3><h2 style='color:#003399;'>{most_sold}</h2><p>({sold_count} units)</p></div>", unsafe_allow_html=True)

                st.write("### Full Sales History")
                st.dataframe(sales_df.sort_values(
                    by='Date', ascending=False), use_container_width=True)

        with tab4:
            st.subheader("System Security Settings")
            with st.form("security_form"):
                v_ivo = st.text_input(
                    "Ivo's Verification Key", type="password").strip()
                v_other = st.text_input(
                    "Other's Verification Key", type="password").strip()
                new_pw = st.text_input(
                    "Create New Admin Password", type="password").strip()
                if st.form_submit_button("Authorize Password Reset"):
                    if v_ivo == IVO_KEY and v_other == OTHER_KEY:
                        save_admin_password(new_pw)
                        st.success("Password updated!")
                        st.session_state["admin_authenticated"] = False
                        st.rerun()
                    else:
                        st.error("Verification Failed.")
