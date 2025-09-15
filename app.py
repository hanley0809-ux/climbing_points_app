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

st.set_page_config(page_title="🧗 Sunset Session Climbs", layout="wide")

# --- STYLING WITH ROBUST FLEXBOX FIX ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&family=Roboto:wght@400;700&display=swap');
    
    h1, h2, h3 { font-family: 'Poppins', sans-serif; color: #FFFFFF; }
    p, .stDataFrame, .stSelectbox, .stTextInput, .stButton { font-family: 'Roboto', sans-serif; }
    
    .card {
        background-color: #2B3A67; border-radius: 12px; padding: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    
    /* --- NEW: Flexbox CSS for the Dashboard --- */
    .dashboard-grid {
        display: flex;
        flex-direction: row;
        gap: 16px;
    }
    .metric-card {
        flex: 1; /* Make each card take up equal space */
        background-color: #1E2128; border-radius: 8px; padding: 16px;
        display: flex; align-items: center; justify-content: center; gap: 15px;
    }
    .metric-icon { font-size: 2.5rem; }
    .metric-text { text-align: left; }
    .metric-text .stMetricLabel { font-size: 0.9rem; color: #D1D1D1; }
    .metric-text .stMetricValue { font-size: 1.5rem; color: #FF7D5A; font-weight: 600; }

    .stButton > button {
        background-color: #FF7D5A; color: white; border: none; border-radius: 8px;
        padding: 10px 20px; font-weight: bold; transition: background-color 0.3s ease;
    }
    .stButton > button:hover { background-color: #E66A4F; }
    
    /* Media Query to adjust for very small screens */
    @media (max-width: 480px) {
        .metric-card {
            flex-direction: column;
            text-align: center;
        }
        .metric-icon { font-size: 2rem; }
    }
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

    # --- UPDATED Dashboard using a single HTML block with Flexbox ---
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("📈 Your Dashboard")
        stats = backend.get_dashboard_stats(user_df)
        
        st.markdown(
            f"""
            <div class="dashboard-grid">
                <div class="metric-card">
                    <div class="metric-icon">🗓️</div>
                    <div class="metric-text">
                        <div class="stMetricLabel">Total Sessions</div>
                        <div class="stMetricValue">{stats["total_sessions"]}</div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">🧗</div>
                    <div class="metric-text">
                        <div class="stMetricLabel">Hardest Boulder</div>
                        <div class="stMetricValue">{stats["hardest_boulder"]}</div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">🧗‍♀️</div>
                    <div class="metric-text">
                        <div class="stMetricLabel">Top Sport Grade</div>
                        <div class="stMetricValue">{stats["hardest_sport"]}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Two-Column Main Interface ---
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
                    st.toast(f"Added {grade}! 🔥")
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

    # --- Save Session Modal ---
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

    # --- Past Sessions Section ---
    st.markdown("---")
    st.header("Past Sessions")
    if user_df.empty:
        st.info("No past sessions found for your name.")
    else:
        if 'Session' in user_df.columns:
            df_sorted_by_date = user_df.sort_values(by='Date', ascending=False)
            grouped = df_sorted_by_date.groupby('Session')
            for session_name, session_df_group in grouped:
                session_date = session_df_group['Date'].iloc[0].strftime('%Y-%m-%d')
                with st.expander(f"**{session_name}** ({session_date})"):
                    summary = backend.get_session_summary(session_df_group)
                    st.markdown(f"**Total Climbs**: {summary['total_climbs']} | **Top Grade**: {summary['hardest_climb']}")
                    st.markdown("---")
                    display_cols = ['Discipline', 'Grade', 'Timestamp']
                    if 'Gym' in session_df_group.columns and not session_df_group['Gym'].fillna('').all() == '':
                        display_cols.insert(2, 'Gym')
                    st.dataframe(session_df_group[display_cols].reset_index(drop=True))
        else:
            st.warning("Action Required: Please update your Google Sheet columns.")