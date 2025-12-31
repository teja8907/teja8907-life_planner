import streamlit as st
import json, os
import pandas as pd
import plotly.express as px
from datetime import date

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Savings Tracker", page_icon="💰", layout="wide")

# ---------------- CSS ----------------
with open("styles/dark_purple.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

DATA_FILE = "data.json"

# ---------------- LOAD / SAVE DATA ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"expenses": [], "savings": []}

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    # clean savings
    cleaned = []
    if isinstance(data.get("savings"), list):
        for s in data["savings"]:
            if isinstance(s, dict):
                cleaned.append(s)

    data["savings"] = cleaned
    data.setdefault("expenses", [])
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

# ---------------- SESSION STATE ----------------
if "edit_budget" not in st.session_state:
    st.session_state.edit_budget = None

# ---------------- PREP EXPENSE DATA ----------------
exp_df = pd.DataFrame(data["expenses"])
if exp_df.empty:
    exp_df = pd.DataFrame(columns=["amount", "category", "date"])

exp_df["date"] = pd.to_datetime(exp_df["date"], errors="coerce")
exp_df["month"] = exp_df["date"].dt.strftime("%B")
exp_df["year"] = exp_df["date"].dt.year
exp_df["week"] = exp_df["date"].dt.isocalendar().week

# ---------------- HEADER ----------------
st.markdown("## 💰 Savings Tracker")
st.caption("Budget • Actual • Savings — automatically calculated")

# ==================================================
# ➕ ADD / EDIT MONTHLY BUDGET
# ==================================================
st.markdown("### ➕ Set Monthly Budget")

months = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]

default_month = (
    st.session_state.edit_budget["month"]
    if st.session_state.edit_budget
    else months[date.today().month - 1]
)

default_year = (
    st.session_state.edit_budget["year"]
    if st.session_state.edit_budget
    else date.today().year
)

default_budget = (
    st.session_state.edit_budget["budget"]
    if st.session_state.edit_budget
    else 0
)

c1, c2, c3 = st.columns(3)

with c1:
    sel_month = st.selectbox("Month", months, index=months.index(default_month))

with c2:
    sel_year = st.number_input("Year", 2020, 2050, value=default_year)

with c3:
    budget = st.number_input("Monthly Budget (₹)", min_value=0, step=500, value=default_budget)

if st.button("💾 Save Budget"):
    # remove existing month-year entry
    data["savings"] = [
        s for s in data["savings"]
        if not (s["month"] == sel_month and s["year"] == sel_year)
    ]

    data["savings"].append({
        "month": sel_month,
        "year": sel_year,
        "budget": budget
    })

    st.session_state.edit_budget = None
    save_data(data)
    st.success("Budget saved")
    st.rerun()

# ==================================================
# 📅 ANNUAL OVERVIEW
# ==================================================
st.markdown("---")
st.markdown("### 📅 Annual Overview")

year_filter = st.selectbox(
    "Select Year",
    list(range(2020, 2051)),
    index=list(range(2020, 2051)).index(date.today().year)
)

cols = st.columns(4)
savings_trend = []

for i, m in enumerate(months):
    with cols[i % 4]:
        spent = exp_df[
            (exp_df["month"] == m) & (exp_df["year"] == year_filter)
        ]["amount"].sum()

        entry = next(
            (b for b in data["savings"] if b["month"] == m and b["year"] == year_filter),
            None
        )

        budget_val = entry["budget"] if entry else 0
        saved = budget_val - spent
        savings_trend.append({"Month": m[:3], "Saved": saved})

        if spent > budget_val and budget_val > 0:
            st.error(f"⚠ Overspent by ₹{spent - budget_val}")

        st.markdown(
            f"""
            <div style="padding:14px;border-radius:12px;
            background:rgba(255,255,255,0.05);
            border:1px solid rgba(255,255,255,0.08);">
                <b>{m[:3]} {str(year_filter)[-2:]}</b><br>
                Budget: ₹{budget_val}<br>
                Actual: ₹{spent}<br>
                <b>Saved: ₹{saved}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

        if entry:
            c_edit, c_del = st.columns(2)
            with c_edit:
                if st.button("✏️ Edit", key=f"edit_{m}"):
                    st.session_state.edit_budget = entry
                    st.rerun()
            with c_del:
                if st.button("🗑 Delete", key=f"del_{m}"):
                    data["savings"].remove(entry)
                    save_data(data)
                    st.rerun()

# ==================================================
# 📊 MONTHLY ANALYSIS
# ==================================================
st.markdown("---")
st.markdown("### 📊 Monthly Analysis")

month_df = exp_df[
    (exp_df["month"] == sel_month) & (exp_df["year"] == sel_year)
]

if not month_df.empty:
    c1, c2 = st.columns(2)

    with c1:
        weekly = month_df.groupby("week", as_index=False)["amount"].sum()
        st.plotly_chart(
            px.bar(
                weekly,
                x="week",
                y="amount",
                labels={"amount": "Amount (₹)", "week": "Week"},
                title="Weekly Spending",
                text_auto=True
            ),
            use_container_width=True
        )

    with c2:
        cat_df = month_df.groupby("category", as_index=False)["amount"].sum()
        st.plotly_chart(
            px.pie(
                cat_df,
                names="category",
                values="amount",
                hole=0.45,
                title="Where your money went"
            ),
            use_container_width=True
        )
else:
    st.info("No expenses for this month")

# ==================================================
# 💰 BUDGET vs ACTUAL
# ==================================================
st.markdown("---")
st.markdown("### 💰 Budget vs Actual")

entry = next(
    (b for b in data["savings"] if b["month"] == sel_month and b["year"] == sel_year),
    None
)

if entry:
    spent = month_df["amount"].sum()
    remaining = entry["budget"] - spent

    comp_df = pd.DataFrame({
        "Type": ["Budget", "Actual Spent", "Saved"],
        "Amount": [entry["budget"], spent, max(remaining, 0)]
    })

    st.plotly_chart(
        px.bar(
            comp_df,
            x="Type",
            y="Amount",
            text_auto=True,
            title=f"{sel_month} {sel_year} Overview"
        ),
        use_container_width=True
    )
else:
    st.info("Set a budget to see comparison")

# ==================================================
# 📈 SAVINGS TREND
# ==================================================
st.markdown("---")
st.markdown("### 📈 Savings Trend")

trend_df = pd.DataFrame(savings_trend)
st.plotly_chart(
    px.line(
        trend_df,
        x="Month",
        y="Saved",
        markers=True,
        title="Monthly Savings Trend"
    ),
    use_container_width=True
)
