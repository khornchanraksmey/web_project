from datetime import date
import pandas as pd
import streamlit as st
import db
from db import init_db, insert_order, fetch_latest

st.set_page_config(page_title="E-commerce Orders", page_icon="🛒", layout="wide")

init_db()

# Database initialization
try:
    db.init_db()
except Exception as e:
    st.error("Database initialization failed.")
    st.exception(e)
    st.stop()

st.title("🛒 E-commerce Order Entry")

def clean_text(s: str) -> str:
    return " ".join((s or "").strip().split())

# Form Section
with st.form("order_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        customer_id = st.text_input("Customer ID", placeholder="e.g., C1023")
        order_date = st.date_input("Order Date", value=date.today())
        status = st.selectbox("Status", ["pending", "processing", "shipped", "delivered", "cancelled"])
        total_amount_usd = st.number_input("Total Amount (USD)", min_value=0.0, step=1.0)
    
    with col2:
        region = st.text_input("Region", placeholder="e.g., Phnom Penh")
        ship_date = st.date_input("Ship Date (Optional)", value=None)
        channel = st.selectbox("Channel", ["website", "social", "marketplace", "partner"])
        payment_method = st.selectbox("Payment Method", ["card", "cash", "bank_transfer", "e-wallet"])

    submitted = st.form_submit_button("Save Order")

if submitted:
    # Logic for validation and insertion remains the same...
    if not customer_id or total_amount_usd <= 0:
        st.error("Please provide a valid Customer ID and Amount.")
    else:
        data = {
            "customer_id": clean_text(customer_id).upper(),
            "order_date": order_date,
            "ship_date": ship_date,
            "status": status.lower(),
            "channel": channel.lower(),
            "total_amount_usd": float(total_amount_usd),
            "payment_method": payment_method.lower(),
            "region": clean_text(region).title(),
        }
        new_id = insert_order(data)
        st.success(f"✅ Order saved (ID: {new_id})")

st.divider()

# Visualization Section
st.subheader("📊 Dashboard: Latest Trends")
rows = fetch_latest(200)

if rows:
    df = pd.DataFrame(rows)
    # Ensure order_date is datetime for proper sorting on the graph
    df['order_date'] = pd.to_datetime(df['order_date'])
    
    # Create two columns for the graphs just like your image
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.write("**Revenue by Day**")
        revenue_df = df.groupby("order_date")["total_amount_usd"].sum()
        st.line_chart(revenue_df)

    with chart_col2:
        st.write("**Orders by Day**")
        count_df = df.groupby("order_date").size()
        st.bar_chart(count_df)

    st.subheader("📄 Recent Order Data")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No orders yet.")
