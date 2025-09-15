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
# NEW: To store the selected grade from the buttons
if 'selected_grade' not in st.session_state: st.session_state.selected_grade = None

st.set_page_config(page_title="🧗 Sunset Session Climbs", layout="wide")

# --- STYLING WITH GRADE BUTTONS ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&family=Roboto:wght@400;700&display=swap');
    
    h1, h2, h3 { font-family: 'Poppins', sans-serif; color: #FFFFFF; }
    p, .stDataFrame, .stSelectbox, .stTextInput { font-family: 'Roboto', sans-serif; }
    
    .card {
        background-color: #2B3A67; border-radius: 12px; padding: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    
    .metric-card {
        background-color: #1E2128; border-radius: 8px; padding: 16px;
        display: flex; align-items: center; justify-content: center; gap: 15px; height: 100%;
    }
    .metric-icon { font-size: 2.5rem; }
    .metric-text .stMetricLabel { font-size: 0.9rem; color: #D1D1D1; }
    .metric-text .stMetricValue { font-size: 1.5rem; color: #FF7D5A; font-weight: 600; }

    /* --- NEW: Grade Button Styling --- */
    .stButton > button {
        border-radius: 8px;
        padding: 10px;
        width: 100%;
        font-weight: bold;
        border: 2px solid #FF7D5A; /* Default border */
        background-color: transparent;
        color: #FF7D5A;
    }
    .stButton > button:hover {
        border-color: #E66A4F;
        color: #E66A4F;
    }
    /* Special button for "Finish Session" */
    .stButton.finish-btn > button {
        background-color: #FF7D5A;
        color: white;
    }

    /* Stonegoat Color-coded Buttons */
    .grade-Red > div > button { border-color: #d13d3d; color: #d13d3d; }
    .grade-Red-Orange > div > button { border-color: #e36a38; color: #e36a38; }
    .grade-Orange > div > button { border-color: #f09433; color: #f09433; }
    .grade-Orange-Yellow > div > button { border-color: #f7b538; color: #f7b538; }
    .grade-Yellow > div > button { border-color: #fce14b; color: #fce14b; }
    .grade-Yellow-Green > div > button { border-color: #b9d749; color: #b9d749; }
    .grade-Green > div > button { border-color: #64c243; color: #64c243; }
    .grade-Green-Blue > div > button { border-color: #43b3c2; color: #43b3c2; }
    .grade-Blue > div > button { border-color: #436ac2; color: #436ac2; }

    /* Media Query for Dashboard */
    @media (max-width: 768px) {
        .dashboard-grid { display: flex; flex-direction: row; gap: 10px; }
        .metric-card { padding: 10px; gap: 8px; flex-direction: column; text-align: center; }
        .metric-icon { font-size: 2rem; }
        .metric-text .stMetricLabel { font-size: 0.7rem; }
        .metric-text .stMetricValue { font-size: 1.1rem; }
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
    # (Homepage code is unchanged)
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        # ... (homepage form) ...
        st.markdown('</div>', unsafe_allow_html=True)
else:
    # --- MAIN LOGGING APP ---
    worksheet = backend.get_worksheet(st.secrets["gcp_service_account"])
    master_df = backend.get_all_climbs(worksheet)
    user_df = master_df[master_df['Name'] == st.session_state.name] if 'Name' in master_df.columns else pd.DataFrame()

    st.title(f"Climbing Log for {st.session_state.name}")

    # --- UPDATED Dashboard with new icons ---
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
                    <div class="metric-icon">🪨</div>
                    <div class="metric-text">
                        <div class="stMetricLabel">Hardest Boulder</div>
                        <div class="stMetricValue">{stats["hardest_boulder"]}</div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">➰</div>
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
            
            # --- NEW: Grade Selection via Buttons ---
            grade_options = []
            is_stonegoat = st.session_state.discipline == "Bouldering" and st.session_state.gym == "Stonegoat"

            if st.session_state.discipline == "Bouldering":
                grade_options = grade_scales["Bouldering"][st.session_state.gym]
            else: # Sport Climbing
                grade_options = grade_scales["Sport Climbing"]
            
            # Set the first grade as default if none is selected
            if not st.session_state.selected_grade:
                st.session_state.selected_grade = grade_options[0]

            st.write("**Select Grade:**")
            # Create a grid of columns for the buttons
            cols = st.columns(4)
            for i, grade in enumerate(grade_options):
                col = cols[i % 4]
                # Apply custom color class if it's a Stonegoat climb
                css_class = f"grade-{grade.replace('/', '-')}" if is_stonegoat else ""
                
                with col:
                    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                    if st.button(grade, key=f"grade_{grade}"):
                        st.session_state.selected_grade = grade
                    st.markdown('</div>', unsafe_allow_html=True)

            with st.form("add_climb_form"):
                submitted = st.form_submit_button("➕ Add to Session")
                if submitted:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_climb = {
                        "Discipline": st.session_state.discipline, 
                        "Grade": st.session_state.selected_grade, # Use grade from session state
                        "Timestamp": timestamp, 
                        "Gym": st.session_state.gym
                    }
                    st.session_state.current_session_climbs.append(new_climb)
                    localS.setItem("current_session_climbs", st.session_state.current_session_climbs)
                    st.toast(f"Added {st.session_state.selected_grade}! 🔥")
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
                # Apply special class to this button
                st.markdown('<div class="finish-btn">', unsafe_allow_html=True)
                if st.button("✅ Finish and Save Session"):
                    st.session_state.show_save_modal = True
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Your current session is empty.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ... (rest of your app code for the modal and past sessions is unchanged)