import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
import uuid
import extra_streamlit_components as stx

# Add a message to show the app has started
st.info("🚀 App starting up...")

# Initialize the cookie manager directly
cookie_manager = stx.CookieManager()
st.info("✅ Cookie manager initialized.")

# Get or create the unique user ID
USER_ID_COOKIE = "climbing_app_user_id"
user_id = cookie_manager.get(cookie=USER_ID_COOKIE)
if not user_id:
    user_id = str(uuid.uuid4())
    cookie_manager.set(USER_ID_COOKIE, user_id, expires_at=datetime(year=2035, month=1, day=1))
    st.rerun()

st.info(f"✅ User ID identified: {user_id}")

# Initialize Session State
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

st.title("Log a New Climb")

# Authenticate with Google Sheets
@st.cache_resource
def get_google_sheet_client():
    st.info("⚙️ Authenticating with Google Sheets...")
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        st.info("✅ Google Sheets authentication successful.")
        return gc
    except Exception as e:
        st.error(f"Error during Google Sheets authentication: {e}")
        st.stop()

gc = get_google_sheet_client()

try:
    st.info("📖 Opening spreadsheet 'Climbing Points Data'...")
    worksheet = gc.open("Climbing Points Data").worksheet("Climbs")
    st.info("✅ Spreadsheet and worksheet opened successfully.")
except Exception as e:
    st.error(f"Could not open the spreadsheet or worksheet. Please check names and sharing settings. Error: {e}")
    st.stop()

# NEW CACHED FUNCTION FOR FETCHING DATA
@st.cache_data(ttl="10m")
def get_all_data():
    st.info("📥 Fetching all records from the worksheet...")
    try:
        data = worksheet.get_all_records()
        st.info("✅ Records fetched successfully.")
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to fetch data from Google Sheet: {e}")
        return pd.DataFrame()

# --- From here on, the rest of your app will run ---

# Dropdowns for logging a new climb
discipline = st.selectbox("Discipline", options=list(grade_scales.keys()))
grade = st.selectbox("Grade", options=grade_scales[discipline])

# (The rest of your form and session logic is unchanged)
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

if df.empty and 'User' not in df.columns: # Check if dataframe is truly empty vs. just no user data yet
    st.info("No past sessions found.")
else:
    if 'SessionID' in df.columns and 'User' in df.columns:
        user_df = df[df['User'] == user_id]

        if not user_df.empty:
            sessions_df = user_df.dropna(subset=['SessionID'])
            sessions_df = sessions_df[sessions_df['SessionID'] != '']

            if not sessions_df.empty:
                grouped = sessions_df.groupby('SessionID')
                sorted_sessions = sorted(grouped, key=lambda x: pd.to_datetime(x[0]), reverse=True)

                for session_id, session_df_group in sorted_sessions:
                    with st.expander(f"Session from {session_id}"):
                        st.dataframe(session_df_group[['Discipline', 'Grade', 'Timestamp']].reset_index(drop=True))
            else:
                st.info("No completed sessions found yet. Finish a session to see it here.")
        else:
             st.info("You haven't logged any sessions yet. Go send something!")
    else:
        st.warning("Action Required: Please ensure 'SessionID' and 'User' columns exist in your Google Sheet.")