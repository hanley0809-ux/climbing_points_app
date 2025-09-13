import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
import uuid  # Library to generate unique IDs
import extra_streamlit_components as stx # The cookie manager library

# --- 1. SETUP COOKIE-BASED USER ID ---
@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

# Get the unique user ID from the cookie, or create a new one
USER_ID_COOKIE = "climbing_app_user_id"
user_id = cookie_manager.get(cookie=USER_ID_COOKIE)
if not user_id:
    user_id = str(uuid.uuid4())
    # Set the cookie with a long expiration date
    cookie_manager.set(USER_ID_COOKIE, user_id, expires_at=datetime(year=2035, month=1, day=1))
    st.rerun() # Rerun to ensure the cookie is set on the first visit

# --- Initialize Session State ---
if 'current_session_climbs' not in st.session_state:
    st.session_state.current_session_climbs = []

# Set page title and theme
st.set_page_config(
    page_title="🧗 Climbing Points",
    layout="centered",
    initial_sidebar_state="auto"
)

# Custom Theming (your styles are unchanged)
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

# Define grade scales in a dictionary
grade_scales = {
    "Bouldering": [f"V{i}" for i in range(11)],  # V0 to V10
    "Sport Climbing": [
        "5a", "5b", "5c", "6a", "6a+", "6b", "6b+", "6c", "6c+",
        "7a", "7a+", "7b", "7b+", "7c", "7c+", "8a"
    ]
}

st.title("Log a New Climb")

# Authenticate with Google Sheets
@st.cache_resource
def get_google_sheet_client():
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        return gc
    except Exception as e:
        st.error(f"Error authenticating with Google Sheets: {e}")
        st.stop()

gc = get_google_sheet_client()
worksheet = gc.open("Climbing Points Data").worksheet("Climbs")

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
        session_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        records_to_add = []
        for climb in st.session_state.current_session_climbs:
            # --- 2. ADD THE USER ID WHEN SAVING DATA ---
            row = [climb["Discipline"], climb["Grade"], climb["Timestamp"], session_id, user_id]
            records_to_add.append(row)

        try:
            worksheet.append_rows(records_to_add)
            st.success("Session saved successfully! Well done! 🎉")
            st.balloons()
            st.session_state.current_session_climbs = []
            st.rerun()
        except Exception as e:
            st.error(f"Error saving session to Google Sheet: {e}")
else:
    st.info("Log a climb to start a new session.")

st.markdown("---")
st.header("Past Sessions")
try:
    data = worksheet.get_all_records()
    if not data:
        st.info("No past sessions found.")
    else:
        df = pd.DataFrame(data)

        # Check if the necessary columns exist
        if 'SessionID' in df.columns and 'User' in df.columns:
            # --- 3. FILTER DATA TO SHOW ONLY THE CURRENT USER'S SESSIONS ---
            user_df = df[df['User'] == user_id]

            if not user_df.empty:
                sessions_df = user_df.dropna(subset=['SessionID'])
                sessions_df = sessions_df[sessions_df['SessionID'] != '']

                if not sessions_df.empty:
                    grouped = sessions_df.groupby('SessionID')
                    sorted_sessions = sorted(grouped, key=lambda x: pd.to_datetime(x[0]), reverse=True)

                    for session_id, session_df in sorted_sessions:
                        with st.expander(f"Session from {session_id}"):
                            st.dataframe(session_df[['Discipline', 'Grade', 'Timestamp']].reset_index(drop=True))
                else:
                    st.info("No completed sessions found yet. Finish a session to see it here.")
            else:
                 st.info("You haven't logged any sessions yet. Go send something!")
        else:
            st.warning("Action Required: Please ensure 'SessionID' and 'User' columns exist in your Google Sheet.")

except Exception as e:
    st.error(f"An error occurred while displaying past sessions: {e}")