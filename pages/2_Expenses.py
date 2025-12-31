import streamlit as st
import json, os
from datetime import date, timedelta
import pandas as pd
import plotly.express as px

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="wide")

# ---------- CSS ----------
with open("styles/dark_purple.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------- HERO HEADER ----------
st.markdown(
    """
    <style>
    .hero-expense {
        height: 140px;
        border-radius: 14px;
        background-image: url("images/expense_banner.jpg");
        background-size: cover;
        background-position: center;
        display: flex;
        align-items: flex-end;
        padding: 18px 28px;
        margin-bottom: 20px;
    }
    .hero-expense h1 { color: white; margin: 0; font-size: 28px; }
    .hero-expense p { color: #e0d9ff; margin: 4px 0 0; font-size: 14px; }
    </style>

    <div class="hero-expense">
        <div>
            <h1>💸 Expense Tracker</h1>
            <p>Daily • Weekly • Monthly spending overview</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- DATA ----------
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"expenses": []}
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    data.setdefault("expenses", [])
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

# ---------- SESSION ----------
if "edit_expense_index" not in st.session_state:
    st.session_state.edit_expense_index = None

# ---------- SAFE DATAFRAME ----------
df = pd.DataFrame(data["expenses"])
for col in ["amount", "category", "date"]:
    if col not in df.columns:
        df[col] = None

df["date"] = pd.to_datetime(df["date"], errors="coerce")

# ---------- TABS ----------
tab_daily, tab_weekly, tab_monthly = st.tabs(["📅 Daily", "📆 Weekly", "🗓 Monthly"])

# ==================================================
# 📅 DAILY
# ==================================================
with tab_daily:
    st.subheader("📅 Daily Expenses")

    selected_date = st.date_input("Select date", value=date.today())

    with st.form("daily_expense_form", clear_on_submit=True):
        amount = st.number_input("Amount (₹)", min_value=0, step=100)
        category = st.selectbox(
            "Category",
            ["Food", "Shopping", "Travel", "Bills", "Xerox", "Stationary", "Other"]
        )
        add = st.form_submit_button("Add Expense")

        if add and amount > 0:
            data["expenses"].append({
                "amount": amount,
                "category": category,
                "date": selected_date.isoformat()
            })
            save_data(data)
            st.success("Expense added")
            st.rerun()

    daily_df = df[df["date"] == pd.to_datetime(selected_date)]

    if daily_df.empty:
        st.info("No expenses on this day")
    else:
        st.markdown("### ✏️ Manage Expenses")

        h1, h2, h3, h4 = st.columns([3, 3, 3, 2])
        h1.markdown("**Amount (₹)**")
        h2.markdown("**Category**")
        h3.markdown("**Date**")
        h4.markdown("**Actions**")
        st.markdown("---")

        for i, row in daily_df.reset_index().iterrows():
            c1, c2, c3, c4 = st.columns([3, 3, 3, 2])

            c1.write(f"₹ {row['amount']}")
            c2.write(row["category"])
            c3.write(row["date"].strftime("%d %b %Y"))

            with c4:
                e1, e2 = st.columns(2)
                if e1.button("✏️", key=f"edit_{i}"):
                    st.session_state.edit_expense_index = row["index"]
                    st.rerun()
                if e2.button("🗑", key=f"del_{i}"):
                    data["expenses"].pop(row["index"])
                    save_data(data)
                    st.rerun()

# ==================================================
# ✏️ EDIT EXPENSE
# ==================================================
if st.session_state.edit_expense_index is not None:
    st.markdown("---")
    st.markdown("### ✏️ Edit Expense")

    exp = data["expenses"][st.session_state.edit_expense_index]

    with st.form("edit_expense_form"):
        amount = st.number_input("Amount (₹)", min_value=0, step=100, value=int(exp["amount"]))
        category = st.selectbox(
            "Category",
            ["Food", "Shopping", "Travel", "Bills", "Xerox", "Stationary", "Other"],
            index=["Food","Shopping","Travel","Bills","Xerox","Stationary","Other"].index(exp["category"])
        )
        save = st.form_submit_button("💾 Update")

        if save:
            exp["amount"] = amount
            exp["category"] = category
            save_data(data)
            st.session_state.edit_expense_index = None
            st.success("Expense updated")
            st.rerun()

# ==================================================
# 📆 WEEKLY
# ==================================================
with tab_weekly:
    st.subheader("📆 Weekly Expenses")

    pick = st.date_input("Pick any date in the week", date.today(), key="week")
    start = pd.to_datetime(pick - timedelta(days=pick.weekday()))
    end = pd.to_datetime(start + timedelta(days=6))

    weekly_df = df[(df["date"] >= start) & (df["date"] <= end)]

    if weekly_df.empty:
        st.info("No expenses this week")
    else:
        st.metric("💰 Total Spent", f"₹{weekly_df['amount'].sum()}")
        st.plotly_chart(
            px.bar(
                weekly_df.groupby("category", as_index=False)["amount"].sum(),
                x="category",
                y="amount",
                text_auto=True
            ),
            use_container_width=True
        )

# ==================================================
# 🗓 MONTHLY
# ==================================================
with tab_monthly:
    st.subheader("🗓 Monthly Expenses")

    if df.empty:
        st.info("No expenses available")
    else:
        df["month"] = df["date"].dt.strftime("%B")
        df["year"] = df["date"].dt.year

        ALL_MONTHS = [
            "January","February","March","April","May","June",
            "July","August","September","October","November","December"
        ]
        ALL_YEARS = list(range(2020, 2051))

        m1, m2 = st.columns(2)
        sel_month = m1.selectbox("Month", ALL_MONTHS, index=date.today().month - 1)
        sel_year = m2.selectbox("Year", ALL_YEARS, index=ALL_YEARS.index(date.today().year))

        month_df = df[(df["month"] == sel_month) & (df["year"] == sel_year)]

        if month_df.empty:
            st.info("No expenses for this month")
        else:
            st.metric("💰 Total Spent", f"₹{month_df['amount'].sum()}")
            st.plotly_chart(
                px.pie(
                    month_df.groupby("category", as_index=False)["amount"].sum(),
                    names="category",
                    values="amount",
                    hole=0.45
                ),
                use_container_width=True
            )
            st.dataframe(month_df[["date", "category", "amount"]], use_container_width=True)
