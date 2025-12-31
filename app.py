import streamlit as st
import json, os
import pandas as pd
import plotly.express as px

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Life Planner",
    page_icon="💜",
    layout="wide"
)

# ---------- CSS ----------
with open("styles/dark_purple.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------- DATA ----------
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "weeks": {},
            "expenses": [],
            "savings": [],
            "wishlist": []
        }

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    data.setdefault("weeks", {})
    data.setdefault("expenses", [])
    data.setdefault("savings", [])
    data.setdefault("wishlist", [])

    return data

data = load_data()

# ==================================================
# ✅ TASKS (CORRECT)
# ==================================================
total_tasks = 0
completed_tasks = 0

for week in data["weeks"].values():
    for day in week.values():
        tasks = day.get("tasks", [])
        total_tasks += len(tasks)
        completed_tasks += sum(1 for t in tasks if t.get("done") is True)

# ==================================================
# ✅ EXPENSES
# ==================================================
expenses_df = pd.DataFrame(data["expenses"])
if expenses_df.empty:
    expenses_df = pd.DataFrame(columns=["amount", "category", "date"])
else:
    expenses_df["date"] = pd.to_datetime(expenses_df["date"], errors="coerce")

total_expenses = expenses_df["amount"].sum()

# ==================================================
# ✅ SAVINGS (AUTO-CALCULATED)
# ==================================================
savings_df = pd.DataFrame(data["savings"])
if savings_df.empty:
    savings_df = pd.DataFrame(columns=["month", "year", "budget"])

latest_budget = 0
saved_amount = 0
overspent_amount = 0

if not savings_df.empty:
    latest = savings_df.iloc[-1]
    sel_month = latest["month"]
    sel_year = latest["year"]
    latest_budget = latest["budget"]

    month_exp = expenses_df[
        (expenses_df["date"].dt.strftime("%B") == sel_month) &
        (expenses_df["date"].dt.year == sel_year)
    ]

    actual_spent = month_exp["amount"].sum()
    saved_amount = latest_budget - actual_spent

    if saved_amount < 0:
        overspent_amount = abs(saved_amount)
        saved_amount = 0

progress = (
    (latest_budget - overspent_amount) / latest_budget
    if latest_budget > 0 else 0
)

# ==================================================
# ✅ WISHLIST
# ==================================================
wishlist_count = len(data["wishlist"])

# ==================================================
# 🧠 DASHBOARD UI
# ==================================================
st.markdown("## 💜 Life Planner Dashboard")
st.caption("Your personal Notion-style system")

c1, c2, c3, c4 = st.columns(4)

c1.metric("📋 Total Tasks", total_tasks)
c2.metric("✅ Completed Tasks", completed_tasks)
c3.metric("💸 Total Expenses", f"₹{int(total_expenses)}")
c4.metric("🛒 Wishlist Items", wishlist_count)

st.divider()

# ==================================================
# 💸 EXPENSE BREAKDOWN
# ==================================================
left, right = st.columns(2)

with left:
    st.subheader("💸 Expense Breakdown")

    if not expenses_df.empty:
        fig = px.pie(
            expenses_df,
            values="amount",
            names="category",
            hole=0.5
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expenses yet")

# ==================================================
# 💰 SAVINGS PROGRESS (FIXED)
# ==================================================
with right:
    st.subheader("💰 Savings Progress")

    if latest_budget == 0:
        st.info("No savings goal set")
    else:
        st.progress(min(max(progress, 0), 1))

        if overspent_amount > 0:
            st.error(f"⚠ Overspent by ₹{overspent_amount}")
        else:
            st.success(f"💜 Saved ₹{saved_amount} out of ₹{latest_budget}")

st.divider()

# ==================================================
# 📝 PENDING TASKS
# ==================================================
left, right = st.columns(2)

with left:
    st.subheader("📝 Pending Tasks")

    if total_tasks == completed_tasks:
        st.success("All tasks completed 🎉")
    else:
        shown = 0
        for week in data["weeks"].values():
            for day in week.values():
                for t in day.get("tasks", []):
                    if not t.get("done") and shown < 5:
                        st.write("•", t.get("text"))
                        shown += 1

# ==================================================
# 🛍 WISHLIST PREVIEW
# ==================================================
with right:
    st.subheader("🛍 Wishlist Preview")

    if data["wishlist"]:
        for item in data["wishlist"][:5]:
            st.write(f"• {item.get('item')} – ₹{item.get('price')}")
    else:
        st.info("Wishlist empty")
