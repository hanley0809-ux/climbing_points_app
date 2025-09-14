import streamlit as st
import pandas as pd
from datetime import datetime
import backend  # Import your backend

# Initialize Session State for climbs
if 'current_session_climbs' not in st.session_state:
    st.session_state.current_session_climbs = []

# Set page title and theme
st.set_page_config(page_title="🧗 Sunset Session Climbs", layout="centered")

# --- "SUNSET SESSION" CUSTOM STYLING ---
st.markdown("""... your CSS from the previous step ...""", unsafe_allow_html=True) # Keeping this brief

# --- DATA LOADING ---
worksheet = backend.get_worksheet(st.secrets["gcp_service_account"])
df = backend.get_all_climbs(worksheet)

# --- 1. NEW PERSONAL STATS DASHBOARD ---
st.header("Your Dashboard")
stats = backend.get_dashboard_stats(df)

col1, col2, col3 = st.columns(3)
col1.metric("Climbs This Month", stats["total_climbs_month"])
col2.metric("Hardest Boulder", stats["hardest_boulder"])
col3.metric("Hardest Sport Climb", stats["hardest_sport"])

st.markdown("---") # Visual separator

# Define grade scales
grade_scales = {
    "Bouldering": [f"V{i}" for i in range(11)],
    "Sport Climbing": ["5a", "5b", "5c", "6a", "6a+", "6b", "6b+", "6c", "6c+", "7a", "7a+", "7b", "7b+", "7c", "7c+", "8a"]
}

# --- 2. NEW TWO-COLUMN LAYOUT FOR LOGGING ---
log_col, session_col = st.columns([0.6, 0.4]) # Make the left column slightly wider

with log_col:
    st.header("Log a Climb")
    discipline = st.selectbox("Discipline", options=list(grade_scales.keys()))
    grade = st.selectbox("Grade", options=grade_scales[discipline])

    with st.form("add_climb_form"):
        submitted = st.form_submit_button("🚀 Add to Session")
        if submitted:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_climb = {"Discipline": discipline, "Grade": grade, "Timestamp": timestamp}
            st.session_state.current_session_climbs.append(new_climb)
            st.rerun()

with session_col:
    st.header("Current Session")
    if st.session_state.current_session_climbs:
        current_df = pd.DataFrame(st.session_state.current_session_climbs)
        st.dataframe(current_df)

        if st.button("✅ Finish and Save Session"):
            backend.save_new_session(worksheet, st.session_state.current_session_climbs)
            st.success("Session saved! 🎉")
            st.balloons()
            st.session_state.current_session_climbs = []
            st.cache_data.clear() # Clear data cache to show new stats
            st.rerun()
    else:
        st.info("Your current session is empty.")

st.markdown("---")
st.header("Past Sessions")

if df.empty:
    st.info("No past sessions found.")
else:
    if 'SessionID' in df.columns:
        sessions_df = df.dropna(subset=['SessionID'])
        if not sessions_df.empty:
            grouped = sessions_df.groupby('SessionID')
            sorted_sessions = sorted(grouped, key=lambda x: pd.to_datetime(x[0]), reverse=True)

            for session_id, session_df_group in sorted_sessions:
                with st.expander(f"Session from {session_id}"):
                    # --- 3. NEW ENHANCED SESSION DISPLAY ---
                    summary = backend.get_session_summary(session_df_group)
                    
                    st.markdown(f"**Total Climbs**: {summary['total_climbs']}")
                    st.markdown(f"**Top Grade**: {summary['hardest_climb']}")
                    
                    st.markdown("---")
                    st.dataframe(session_df_group[['Discipline', 'Grade', 'Timestamp']].reset_index(drop=True))
    else:
        st.warning("Action Required: Please ensure the 'SessionID' column exists in your Google Sheet.")