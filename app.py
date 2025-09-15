import streamlit as st
import pandas as pd
from datetime import datetime
import backend
from streamlit_local_storage import LocalStorage

# --- Session State Initialization ---
localS = LocalStorage()
if 'session_active' not in st.session_state: st.session_state.session_active = False
if 'current_session_climbs' not in st.session_state:
    initial_session_climbs = localS.getItem("current_session_climbs")
    st.session_state.current_session_climbs = initial_session_climbs if initial_session_climbs is not None else []
if 'show_save_modal' not in st.session_state: st.session_state.show_save_modal = False
if 'discipline' not in st.session_state: st.session_state.discipline = "Bouldering"
if 'gym' not in st.session_state: st.session_state.gym = None
if 'name' not in st.session_state: st.session_state.name = ""

st.set_page_config(page_title="🧗 Sunset Session Climbs", layout="wide") # Use wide layout for better card spacing

# --- NEW UX-FOCUSED STYLING ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&family=Roboto:wght@400;700&display=swap');
    
    /* --- Global & Base Styling --- */
    .stApp {
        background-color: #F7F7F7;
        background-image: url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23d1d1d1' fill-opacity='0.1' fill-rule='evenodd'%3E%3Cpath d='M0 40L40 0H20L0 20M40 40V20L20 40'/%3E%3C/g%3E%3C/svg%3E");
    }
    h1, h2, h3 { font-family: 'Poppins', sans-serif; color: #2B3A67; }
    p, .stDataFrame, .stSelectbox, .stTextInput, .stButton { font-family: 'Roboto', sans-serif; color: #333333; }
    
    /* --- 1. Card-Based Layout --- */
    .card {
        background-color: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    /* --- 2. Component Improvements --- */
    /* Dashboard Metric Cards */
    .stMetric {
        background-color: #F7F7F7;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .stMetric label {
        font-weight: 600;
        color: #2B3A67;
    }
    .stMetric value {
        color: #FF7D5A;
    }

    /* Current Session List Items */
    .session-item {
        border-bottom: 1px solid #F0F2F6;
        padding: 8px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Past Session Summary Cards */
    .stExpander {
        background-color: white;
        border: none;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .stExpander header {
        font-weight: 600;
        font-family: 'Poppins', sans-serif;
        font-size: 1.1em;
        padding: 16px;
    }

    /* --- 3. Micro-interaction Improvements --- */
    .stButton > button {
        background-color: #FF7D5A; color: white; border: none; border-radius: 8px;
        padding: 10px 20px; font-weight: bold; transition: background-color 0.3s ease;
    }
    .stButton > button:hover { background-color: #E66A4F; }

    </style>
    """,
    unsafe_allow_html=True
)

grade_scales = {
    "Bouldering": {"Stonegoat": ["Red", "Red/Orange", "Orange", "Orange/Yellow", "Yellow", "Yellow/Green", "Green", "Green/Blue", "Blue"], "Balance": ["1", "2", "3", "4", "5", "6", "7", "8"]},
    "Sport Climbing": ["5a", "5b", "5c", "6a", "6a+", "6b", "6b+", "6c", "6c+", "7a", "7a+", "7b", "7b+", "7c", "7c+", "8a"]
}

# --- Main App Router ---
if not st.session_state.session_active:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.title("Welcome to Your Climbing Log")
        st.header("Start a New Session")
        last_name = localS.getItem("user_name")
        with st.form("start_session_form"):
            user_name = st.text_input("Your Name", value=last_name if last_name else "")
            discipline_choice = st.selectbox("Select Discipline", options=grade_scales.keys())
            gym_choice = None
            if discipline_choice == "Bouldering":
                gym_choice = st.selectbox("Select Gym", options=grade_scales["Bouldering"].keys())
            submitted = st.form_submit_button("🚀 Start Climbing")
            if submitted:
                if not user_name:
                    st.warning("Please enter your name.")
                else:
                    st.session_state.name = user_name
                    st.session_state.discipline = discipline_choice
                    st.session_state.gym = gym_choice
                    st.session_state.session_active = True
                    localS.setItem("user_name", user_name)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
else:
    # --- MAIN LOGGING APP ---
    worksheet = backend.get_worksheet(st.secrets["gcp_service_account"])
    master_df = backend.get_all_climbs(worksheet)
    user_df = master_df[master_df['Name'] == st.session_state.name] if 'Name' in master_df.columns else pd.DataFrame()

    st.title(f"Climbing Log for {st.session_state.name}")

    # 1. At-a-Glance Dashboard
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("📈 Your Dashboard")
        stats = backend.get_dashboard_stats(user_df)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Climbs This Month", stats["total_climbs_month"])
        with col2:
            st.metric("Hardest Boulder", stats["hardest_boulder"])
        with col3:
            st.metric("Hardest Sport Climb", stats["hardest_sport"])
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. Two-Column Main Interface
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        log_col, session_col = st.columns(2, gap="large")
        with log_col:
            st.header("Log a Climb")
            st.markdown(f"**Discipline:** `{st.session_state.discipline}` | **Gym:** `{st.session_state.gym or 'N/A'}`")
            grade_options = []
            if st.session_state.discipline == "Bouldering":
                grade_options = grade_scales["Bouldering"][st.session_state.gym]
            else:
                grade_options = grade_scales["Sport Climbing"]
            grade = st.selectbox("Grade", options=grade_options, label_visibility="collapsed")

            with st.form("add_climb_form"):
                submitted = st.form_submit_button("➕ Add to Session")
                if submitted:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_climb = {"Discipline": st.session_state.discipline, "Grade": grade, "Timestamp": timestamp, "Gym": st.session_state.gym}
                    st.session_state.current_session_climbs.append(new_climb)
                    localS.setItem("current_session_climbs", st.session_state.current_session_climbs)
                    st.toast(f"Added {grade}! 🔥") # 3. Micro-interaction: Toast notification
                    st.rerun()

        with session_col:
            st.header("Current Session")
            if st.session_state.current_session_climbs:
                for i, climb in enumerate(st.session_state.current_session_climbs):
                    climb_info = f"**{climb['Grade']}** ({climb['Discipline']})"
                    c1, c2 = st.columns([0.8, 0.2])
                    c1.write(climb_info)
                    if c2.button("🗑️", key=f"delete_{i}", help="Delete climb"):
                        st.session_state.current_session_climbs.pop(i)
                        localS.setItem("current_session_climbs", st.session_state.current_session_climbs)
                        st.rerun()
                st.markdown("---")
                if st.button("✅ Finish and Save Session"):
                    st.session_state.show_save_modal = True
                    st.rerun()
            else:
                st.info("Your current session is empty.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Save Session Modal
    if st.session_state.show_save_modal:
        default_name = st.session_state.discipline
        if st.session_state.gym: default_name = f"{st.session_state.gym} - {st.session_state.discipline}"
        with st.form("save_session_form"):
            st.subheader("Name Your Session")
            session_name = st.text_input("Session Name (optional)", value=default_name)
            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 Save Session", use_container_width=True):
                backend.save_new_session(worksheet, st.session_state.current_session_climbs, st.session_state.name, session_name)
                st.success("Session saved!")
                st.balloons()
                localS.setItem("current_session_climbs", [])
                st.session_state.current_session_climbs = []
                st.session_state.show_save_modal = False
                st.session_state.session_active = False 
                st.cache_data.clear() 
                st.rerun()
            if c2.form_submit_button("Cancel", use_container_width=True):
                st.session_state.show_save_modal = False
                st.rerun()

    st.header("Past Sessions")
    if user_df.empty:
        st.info("No past sessions found for your name.")
    else:
        if 'Session' in user_df.columns:
            df_sorted_by_date = user_df.sort_values(by='Date', ascending=False)
            grouped = df_sorted_by_date.groupby('Session')
            for session_name, session_df_group in grouped:
                session_date = session_df_group['Date'].iloc[0].strftime('%Y-%m-%d')
                
                # Past Session Summary Card
                summary = backend.get_session_summary(session_df_group)
                expander_title = f"**{session_name}** ({session_date}) — {summary['total_climbs']} climbs, top grade: {summary['hardest_climb']}"

                with st.expander(expander_title):
                    st.dataframe(session_df_group[['Discipline', 'Grade', 'Timestamp', 'Gym']].reset_index(drop=True))