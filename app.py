import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
import uuid
import extra_streamlit_components as stx

# Initialize the cookie manager directly
cookie_manager = stx.CookieManager()

# --- FIX: Add a session_state guard to prevent infinite rerun loops ---
# This flag will ensure we only try to set the cookie once per session.
if 'cookie_set_attempted' not in st.session_state:
    st.session_state.cookie_set_attempted = False

# Get or create the unique user ID
USER_ID_COOKIE = "climbing_app_user_id"
user_id = cookie_manager.get(cookie=USER_ID_COOKIE)

# Only try to set a new cookie if one doesn't exist AND we haven't tried already
if not user_id and not st.session_state.cookie_set_attempted:
    user_id = str(uuid.uuid4())
    cookie_manager.set(USER_ID_COOKIE, user_id, expires_at=datetime(year=2035, month=1, day=1))
    st.session_state.cookie_set_attempted = True # Set the flag
    st.rerun()

# Initialize Session State for climbs
if 'current_session_climbs' not in st.session_state:
    st.session_state.current_session_climbs = []

# Set page title and theme
st.set_page_config(page_title="🧗 Climbing Points", layout="centered")

# Custom Theming
st.markdown("""... your CSS styles ...""", unsafe_allow_html=True) # Keeping this brief

# Define grade scales
grade_scales = {
    "Bouldering": [f"V{i}" for i in range(11)],
    "Sport Climbing": ["5a", "5b", "5c", "6a", "6a+", "6b", "6b+", "6c", "6c+", "7a", "7a+", "7b", "7b+", "7c", "7c+", "8a"]
}

# Only proceed to render the full app if we have a user ID
if user_id:
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

    # CACHED FUNCTION FOR FETCHING DATA
    @st.cache_data(ttl="10m")
    def get_all_data():
        try:
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Failed to fetch data from Google Sheet: {e}")
            return pd.DataFrame()

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
                row = [climb["Discipline"], climb["Grade"], climb["Timestamp"], session_id, user_id]
                records_to_add.append(row)

            try:
                worksheet.append_rows(records_to_add)
                st.success("Session saved successfully! Well done! 🎉")
                st.balloons()
                st.session_state.current_session_climbs = []
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error saving session to Google Sheet: {e}")
    else:
        st.info("Log a climb to start a new session.")

    st.markdown("---")
    st.header("Past Sessions")

    df = get_all_data()

    if df.empty and 'User' not in df.columns:
        st.info("No past sessions found.")
    else:
        if 'SessionID' in df.columns and 'User' in df.columns:
            user_df = df[df['User'] == user_id]
            if not user_df.empty:
                # ... (rest of your display logic is unchanged)
                sessions_df = user_df.dropna(subset=['SessionID'])
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
                 st.info("You haven't logged any sessions yet.")
        else:
            st.warning("Action Required: Ensure 'SessionID' and 'User' columns exist in your Google Sheet.")
else:
    # This message will show if the cookie logic fails to produce an ID
    st.error("Could not initialize user session. Please ensure cookies are enabled in your browser and refresh the page.")