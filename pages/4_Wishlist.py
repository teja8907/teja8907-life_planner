import streamlit as st
import json, os
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Wishlist & Shopping List", page_icon="🛍️", layout="wide")

# ---------------- CSS ----------------
with open("styles/dark_purple.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

DATA_FILE = "data.json"

# ---------------- LOAD / SAVE ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"wishlist": []}

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    # 🔒 ensure wishlist is always a list of dicts
    cleaned = []
    for item in data.get("wishlist", []):
        if isinstance(item, dict):
            cleaned.append(item)

    data["wishlist"] = cleaned
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

# ---------------- SESSION ----------------
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# ---------------- HEADER ----------------
st.markdown("## 🛍️ Wishlist & Shopping List")
st.caption("Plan your purchases — not impulse buys")

# ---------------- CONSTANTS ----------------
CATEGORIES = [
    "General",
    "Electronics",
    "Apparel",
    "Personal Care",
    "Bags & Luggage",
    "Home",
    "Other"
]

PRIORITIES = ["Need", "Want", "Nice to Have"]

# ==================================================
# ➕ ADD / EDIT ITEM
# ==================================================
edit_mode = st.session_state.edit_index is not None

if edit_mode:
    current = data["wishlist"][st.session_state.edit_index]
else:
    current = {
        "item": "",
        "price": 0.0,
        "specs": "",
        "brand": "",
        "priority": "Want",
        "category": "General",
        "url": ""
    }

with st.form("wishlist_form", clear_on_submit=False):
    c1, c2, c3 = st.columns(3)

    with c1:
        item = st.text_input("Item name", value=current["item"])
        brand = st.text_input("Brand", value=current["brand"])

    with c2:
        price = st.number_input(
            "Price (₹)",
            min_value=0.0,
            step=10.0,
            value=float(current["price"])
        )
        specs = st.text_input("Specs", value=current["specs"])

    with c3:
        priority = st.selectbox(
            "Priority",
            PRIORITIES,
            index=PRIORITIES.index(current["priority"])
            if current["priority"] in PRIORITIES else 1
        )

        category = st.selectbox(
            "Category",
            CATEGORIES,
            index=CATEGORIES.index(current["category"])
            if current["category"] in CATEGORIES else 0
        )

    url = st.text_input("Product link (URL)", value=current["url"])

    submit = st.form_submit_button("💾 Save Item")

    if submit and item.strip():
        entry = {
            "item": item.strip(),
            "price": price,
            "specs": specs,
            "brand": brand,
            "priority": priority,
            "category": category,
            "url": url
        }

        if edit_mode:
            data["wishlist"][st.session_state.edit_index] = entry
            st.session_state.edit_index = None
        else:
            data["wishlist"].append(entry)

        save_data(data)
        st.success("Item saved successfully")
        st.rerun()

# ==================================================
# 📋 WISHLIST TABLE
# ==================================================
st.markdown("---")
st.markdown("### 📋 Items")

if not data["wishlist"]:
    st.info("Your wishlist is empty")
    st.stop()

df = pd.DataFrame(data["wishlist"])

# ---- Filters ----
f1, f2 = st.columns(2)

with f1:
    cat_filter = st.multiselect("Filter by category", sorted(df["category"].unique()))

with f2:
    pr_filter = st.multiselect("Filter by priority", sorted(df["priority"].unique()))

if cat_filter:
    df = df[df["category"].isin(cat_filter)]

if pr_filter:
    df = df[df["priority"].isin(pr_filter)]

# ---- Display table ----
st.dataframe(df, use_container_width=True, hide_index=True)

# ==================================================
# ✏️ EDIT / DELETE CONTROLS
# ==================================================
st.markdown("### ✏️ Manage Items")

cols = st.columns(4)

for i, row in df.reset_index().iterrows():
    real_index = row["index"]

    with cols[i % 4]:
        st.markdown(
            f"""
            <div style="
                padding:14px;
                border-radius:12px;
                background:rgba(255,255,255,0.05);
                border:1px solid rgba(255,255,255,0.08);
            ">
                <b>{row['item']}</b><br>
                ₹ {row['price']}<br>
                🏷 {row['priority']}<br>
                📂 {row['category']}
            </div>
            """,
            unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)

        with c1:
            if st.button("✏️ Edit", key=f"edit_{real_index}"):
                st.session_state.edit_index = real_index
                st.rerun()

        with c2:
            if st.button("🗑 Delete", key=f"del_{real_index}"):
                data["wishlist"].pop(real_index)
                save_data(data)
                st.rerun()

# ==================================================
# 💰 TOTAL COST
# ==================================================
st.markdown("---")
st.metric("💰 Total Wishlist Cost", f"₹{df['price'].sum():,.2f}")
