import streamlit as st
from datetime import date, timedelta
import json, os

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Daily Tasks", page_icon="✅", layout="wide")

# ---------- CSS ----------
with open("styles/dark_purple.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
   


    st.markdown(
    """
    <div class="hero-container">
        <div class="hero-overlay">
            <h1>💜 Life Planner</h1>
            <p>Weekly Task & Habit Tracker</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ---------- DATA ----------
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"weeks": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()
data.setdefault("weeks", {})

# ---------- WEEK LOGIC ----------
if "week_offset" not in st.session_state:
    st.session_state.week_offset = 0

today = date.today()
monday = today - timedelta(days=today.weekday())
week_start = monday + timedelta(weeks=st.session_state.week_offset)
week_key = week_start.isoformat()

days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ---------- NAV ----------
st.markdown(
    """
    <div class="week-nav">
        <div class="nav-left"></div>
        <div class="nav-center"></div>
        <div class="nav-right"></div>
    </div>
    """,
    unsafe_allow_html=True
)

nav_left, nav_center, nav_right = st.columns([2, 6, 2])

with nav_left:
    if st.button("⬅ Previous Week", use_container_width=True):
        st.session_state.week_offset -= 1
        st.rerun()

with nav_center:
    st.markdown(
        f"<h3 style='text-align:center; margin-top:0;'>📅 Week of {week_start.strftime('%d %b %Y')}</h3>",
        unsafe_allow_html=True
    )

with nav_right:
    if st.button("Next Week ➡", use_container_width=True):
        st.session_state.week_offset += 1
        st.rerun()

# ---------- INIT WEEK ----------
data["weeks"].setdefault(week_key, {})

# ---------- MAIN GRID ----------
st.subheader("✅ Weekly Task & Habit Tracker")
cols = st.columns(7)

for i, col in enumerate(cols):
    day_date = week_start + timedelta(days=i)
    day_key = day_date.isoformat()

    data["weeks"][week_key].setdefault(day_key, {
        "habits": [],
        "tasks": []
    })

    with col:
        st.markdown(f"**{days[i]}**")
        st.caption(day_date.strftime("%d %b"))

        # ================= HABITS =================
        st.markdown("**Habits**")

        with st.form(key=f"habit_form_{day_key}", clear_on_submit=True):
            habit_text = st.text_input("Add habit")
            add_habit = st.form_submit_button("Add")

            if add_habit and habit_text.strip():
                data["weeks"][week_key][day_key]["habits"].append({
                    "text": habit_text.strip(),
                    "done": False
                })
                save_data(data)
                st.rerun()

        for hi, habit in enumerate(data["weeks"][week_key][day_key]["habits"]):
            h1, h2, h3 = st.columns([6, 1, 1])

            with h1:
                habit["text"] = st.text_input(
                    "",
                    habit["text"],
                    key=f"habit_edit_{day_key}_{hi}"
                )

            with h2:
                habit["done"] = st.checkbox(
                    "✓",
                    value=habit["done"],
                    key=f"habit_done_{day_key}_{hi}"
                )

            with h3:
                if st.button("🗑", key=f"habit_del_{day_key}_{hi}"):
                    data["weeks"][week_key][day_key]["habits"].pop(hi)
                    save_data(data)
                    st.rerun()

        st.markdown("---")

        # ================= TASKS =================
        st.markdown("**Tasks**")

        with st.form(key=f"task_form_{day_key}", clear_on_submit=True):
            task_text = st.text_input("Add task")
            add_task = st.form_submit_button("Add")

            if add_task and task_text.strip():
                data["weeks"][week_key][day_key]["tasks"].append({
                    "text": task_text.strip(),
                    "done": False
                })
                save_data(data)
                st.rerun()

        for ti, task in enumerate(data["weeks"][week_key][day_key]["tasks"]):
            t1, t2, t3 = st.columns([6, 1, 1])

            with t1:
                task["text"] = st.text_input(
                    "",
                    task["text"],
                    key=f"task_edit_{day_key}_{ti}"
                )

            with t2:
                task["done"] = st.checkbox(
                    "✓",
                    value=task["done"],
                    key=f"task_done_{day_key}_{ti}"
                )

            with t3:
                if st.button("🗑", key=f"task_del_{day_key}_{ti}"):
                    data["weeks"][week_key][day_key]["tasks"].pop(ti)
                    save_data(data)
                    st.rerun()
                    # ---------- WEEKLY PROGRESS ----------
total_items = 0
completed_items = 0

for day in data["weeks"][week_key].values():
    for h in day["habits"]:
        total_items += 1
        if h["done"]:
            completed_items += 1
    for t in day["tasks"]:
        total_items += 1
        if t["done"]:
            completed_items += 1

if total_items > 0:
    percent = completed_items / total_items
    st.markdown("### 📊 Weekly Progress")
    st.progress(percent)
    st.caption(f"{int(percent*100)}% completed")


# ---------- SAVE ----------
save_data(data)
