from datetime import date
import pandas as pd
import streamlit as st

import db
from db import init_db, insert_order, fetch_latest

st.set_page_config(page_title="E-commerce Orders", page_icon="🛒")
init_db()


# Cloud concept: Idempotency - safe to run multiple times
try:
    db.init_db()
except Exception as e:
    st.error("Database initialization failed.")
    st.exception(e)
    st.stop()

st.title("🛒 E-commerce Order Entry")
st.caption("Order ID is generated automatically by the system.")

def clean_text(s: str) -> str:
    return " ".join((s or "").strip().split())

with st.form("order_form", clear_on_submit=True):
    customer_id = st.text_input("customer_id", placeholder="e.g., C1023")

    order_date = st.date_input("order_date", value=date.today())
    ship_date = st.date_input("ship_date (optional)", value=None)

    status = st.selectbox(
        "status",
        ["pending", "processing", "shipped", "delivered", "cancelled"]
    )

    channel = st.selectbox(
        "channel",
        ["website", "social", "marketplace", "partner"]
    )

    total_amount_usd = st.number_input(
        "total_amount_usd", min_value=0.0, step=1.0
    )

    discount_pct = st.number_input(
        "discount_pct", min_value=0.0, max_value=100.0, step=0.1
    )

    payment_method = st.selectbox(
        "payment_method",
        ["card", "cash", "bank_transfer", "e-wallet"]
    )

    region = st.text_input("region", placeholder="e.g., Phnom Penh")

    submitted = st.form_submit_button("Save Order")

if submitted:
    data = {
        "customer_id": clean_text(customer_id).upper(),
        "order_date": order_date,
        "ship_date": ship_date,
        "status": status.lower(),
        "channel": channel.lower(),
        "total_amount_usd": float(total_amount_usd),
        "discount_pct": float(discount_pct),
        "payment_method": payment_method.lower(),
        "region": clean_text(region).title(),
    }
    # ship_date validation
    if ship_date is not None and ship_date < order_date:
      st.error("❌ Ship date cannot be earlier than Order date.")
      st.stop()

    # validation
    errors = []
    if not data["customer_id"]:
        errors.append("customer_id is required.")
    if data["total_amount_usd"] <= 0:
        errors.append("total_amount_usd must be greater than 0.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        new_id = insert_order(data)
        st.success(f"✅ Order saved (order_id = {new_id})")

st.divider()
st.subheader("📄 Latest Orders")

rows = fetch_latest(200)
# Check if there are rows in the fetched data
if rows:
    df = pd.DataFrame(rows)
    
    # Ensure order_date is a datetime object for grouping
    df['order_date'] = pd.to_datetime(df['order_date'])

    # Create two columns for the charts as seen in the photo
    col1, col2 = st.columns(2)

    with col1:
        st.write("### Revenue by day (from latest 200 orders)")
        # Sum total_amount by date
        revenue_by_day = df.groupby(df['order_date'].dt.strftime('%a %d'))['total_amount'].sum()
        st.line_chart(revenue_by_day)

    with col2:
        st.write("### Orders by day (from latest 200 orders)")
        # Count number of orders by date
        orders_by_day = df.groupby(df['order_date'].dt.strftime('%a %d')).size()
        st.bar_chart(orders_by_day)

    # Display the raw data table below the charts
    st.dataframe(df, use_container_width=True)

    # --- Payment & Category Section ---
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
            st.info("Add a 'category' field to see category sales.")

else:
    st.info("No orders yet.")

