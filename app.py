import streamlit as st
import pandas as pd
from datetime import datetime
import backend  # <-- 1. Import your new backend file

# Initialize Session State for climbs
if 'current_session_climbs' not in st.session_state:
    st.session_state.current_session_climbs = []

# Set page title and theme
st.set_page_config(page_title="🧗 Climbing Points", layout="centered")

# Custom Theming
st.markdown(
    """
    <style>
    .reportview-container { background: #F8F8F8; }
    .stSelectbox > label { color: #F5A623; }
    .stButton > button { background-color: #F5A623; color: white; border-radius: 5px; border: none; padding: 10px 20px; font-size: 16px; font-weight: bold; }
    .stButton > button:hover { background-color: #E08E0B; }
    h1 { color: #F5A623; }
    </style>
    """,
    unsafe_allow_html=True
)

# Define grade scales
grade_scales = {
    "Bouldering": [f"V{i}" for i in range(11)],
    "Sport Climbing": ["5a", "5b", "5c", "6a", "6a+", "6b", "6b+", "6c", "6c+", "7a", "7a+", "7b", "7b+", "7c", "7c+", "8a"]
}

st.title("Log a New Climb")

# --- 2. Connect to Google Sheets using the backend ---
# The logic is now hidden in backend.py. We just call the function.
worksheet = backend.get_worksheet(st.secrets["gcp_service_account"])

# Dropdowns for logging a new climb
discipline = st.selectbox("Discipline", options=list(grade_scales.keys()))
grade = st.selectbox("Grade", options=grade_scales[discipline])

with st.form("add_climb_form"):
    submitted = st.form_submit_button("🚀 Add Climb to Session")
    if submitted:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_climb = {"Discipline": discipline, "Grade": grade, "Timestamp": timestamp}
        st.session_state.current_session_climbs.append(new_climb)
        st.success(f"Added {grade} to current session!")

st.markdown("---")
st.header("Current Session")

if st.session_state.current_session_climbs:
    current_df = pd.DataFrame(st.session_state.current_session_climbs)
    st.dataframe(current_df)

    if st.button("✅ Finish and Save Session"):
        # --- 3. Save the session using the backend ---
        backend.save_new_session(worksheet, st.session_state.current_session_climbs)
        
        st.success("Session saved successfully! Well done! 🎉")
        st.balloons()
        st.session_state.current_session_climbs = []
        # We don't need to clear the data cache here anymore
        st.rerun()

else:
    st.info("Log a climb to start a new session.")

st.markdown("---")
st.header("Past Sessions")

# --- 4. Fetch all data using the backend ---
df = backend.get_all_climbs(worksheet)

if df.empty:
    st.info("No past sessions found.")
else:
    if 'SessionID' in df.columns:
        sessions_df = df.dropna(subset=['SessionID'])
        sessions_df = sessions_df[sessions_df['SessionID'] != '']

        if not sessions_df.empty:
            grouped = sessions_df.groupby('SessionID')
            sorted_sessions = sorted(grouped, key=lambda x: pd.to_datetime(x[0]), reverse=True)

            for session_id, session_df_group in sorted_sessions:
                with st.expander(f"Session from {session_id}"):
                    st.dataframe(session_df_group[['Discipline', 'Grade', 'Timestamp']].reset_index(drop=True))
        else:
            st.info("No completed sessions found yet.")
    else:
        st.warning("Action Required: Please ensure the 'SessionID' column exists in your Google Sheet.")