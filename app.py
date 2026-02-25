from datetime import date
import pandas as pd
import streamlit as st
import db
from db import init_db, insert_order, fetch_latest

# 1. Setup - Added layout="wide" to match the photo's spacing
st.set_page_config(page_title="E-commerce Orders", page_icon="🛒", layout="wide")
init_db()

st.title("🛒 E-commerce Order Entry")
st.caption("Order ID is generated automatically by the system.")

def clean_text(s: str) -> str:
    return " ".join((s or "").strip().split())

with st.form("order_form", clear_on_submit=True):
    # Left and right columns for the form to keep it organized
    f_col1, f_col2 = st.columns(2)
    
    customer_id = f_col1.text_input("customer_id", placeholder="e.g., C1023")
    order_date = f_col1.date_input("order_date", value=date.today())
    ship_date = f_col1.date_input("ship_date (optional)", value=None)
    
    # ADDED CATEGORY to match your image
    category = f_col1.selectbox("category", ["Coffee", "Pastry", "Merchandise", "Beans"])

    status = f_col2.selectbox("status", ["pending", "processing", "shipped", "delivered", "cancelled"])
    channel = f_col2.selectbox("channel", ["website", "social", "marketplace", "partner", "online"])
    
    # We will use 'total_amount_usd' in the form but save it to the DB
    total_amount_usd = f_col2.number_input("total_amount_usd", min_value=0.0, step=1.0)
    payment_method = f_col2.selectbox("payment_method", ["card", "cash", "bank_transfer", "e-wallet"])
    
    region = st.text_input("region", placeholder="e.g., Phnom Penh")
    submitted = st.form_submit_button("Save Order")

if submitted:
    data = {
        "customer_id": clean_text(customer_id).upper(),
        "order_date": order_date,
        "ship_date": ship_date,
        "status": status.lower(),
        "category": category, # Added this
        "channel": channel.lower(),
        "total_amount": float(total_amount_usd), # Renamed to 'total_amount' to fix error
        "payment_method": payment_method.lower(),
        "region": clean_text(region).title(),
    }

    if ship_date is not None and ship_date < order_date:
        st.error("❌ Ship date cannot be earlier than Order date.")
    elif not data["customer_id"]:
        st.error("customer_id is required.")
    elif data["total_amount"] <= 0:
        st.error("total_amount must be greater than 0.")
    else:
        new_id = insert_order(data)
        st.success(f"✅ Order saved (order_id = {new_id})")

st.divider()
st.header("📄 Latest Orders")

rows = fetch_latest(200)

if rows:
    df = pd.DataFrame(rows)
    
    # Important: Convert date strings to actual datetime objects
    df['order_date'] = pd.to_datetime(df['order_date'])

    # --- TOP CHARTS (AS SEEN IN PHOTO) ---
    col1, col2 = st.columns(2)

    with col1:
        st.write("### Revenue by day (from latest 200 orders)")
        # Fixed: Use 'total_amount' to match the data dict above
        revenue_by_day = df.groupby(df['order_date'].dt.strftime('%a %d'))['total_amount'].sum()
        st.line_chart(revenue_by_day)

    with col2:
        st.write("### Orders by day (from latest 200 orders)")
        orders_by_day = df.groupby(df['order_date'].dt.strftime('%a %d')).size()
        st.bar_chart(orders_by_day)

    # Raw Data Table
    st.dataframe(df, use_container_width=True)

    # --- BOTTOM CHARTS ---
    st.divider()
    c3, c4 = st.columns(2)
    
    with c3:
        st.subheader("📊 Total Sales by Payment Method")
        sales_by_payment = df.groupby("payment_method")["total_amount"].sum()
        st.bar_chart(sales_by_payment)

    with c4:
        st.subheader("☕ Sales by Category")
        if "category" in df.columns:
            sales_by_category = df.groupby("category")["total_amount"].sum()
            st.bar_chart(sales_by_category)
        else:
            st.info("No 'category' data found.")

else:
    st.info("No orders yet.")
