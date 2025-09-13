import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# --- 1. Initialize Session State ---
# This creates a temporary list to hold climbs for the current session.
# It persists across reruns but is cleared when the session is finished.
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

try:
    spreadsheet = gc.open("Climbing Points Data")
    worksheet = spreadsheet.worksheet("Climbs")
except Exception as e:
    st.error(f"Error accessing Google Sheet: {e}")
    st.stop()


# Dropdowns for logging a new climb
discipline = st.selectbox("Discipline", options=list(grade_scales.keys()))
grade = st.selectbox("Grade", options=grade_scales[discipline])

# --- 2. Update the Form Logic ---
# The "Send It!" button now adds the climb to the temporary session list.
with st.form("add_climb_form"):
    submitted = st.form_submit_button("🚀 Add Climb to Session")
    if submitted:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Create a dictionary for the climb
        new_climb = {"Discipline": discipline, "Grade": grade, "Timestamp": timestamp}
        # Add the new climb to our session state list
        st.session_state.current_session_climbs.append(new_climb)
        st.success(f"Added {grade} to current session!")

st.markdown("---")

# --- 3. Display Current Session and Add "Finish Session" Button ---
st.header("Current Session")
if st.session_state.current_session_climbs:
    # Display the climbs you've logged so far in this session
    current_df = pd.DataFrame(st.session_state.current_session_climbs)
    st.dataframe(current_df)

    # The button to save the session to Google Sheets
    if st.button("✅ Finish and Save Session"):
        session_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        records_to_add = []
        for climb in st.session_state.current_session_climbs:
            # Prepare row with the new SessionID
            row = [climb["Discipline"], climb["Grade"], climb["Timestamp"], session_id]
            records_to_add.append(row)

        try:
            # Append all rows at once for efficiency
            worksheet.append_rows(records_to_add)
            st.success("Session saved successfully! Well done! 🎉")
            st.balloons()
            # Clear the session state for the next session
            st.session_state.current_session_climbs = []
            st.rerun() # Rerun the app to refresh the display
        except Exception as e:
            st.error(f"Error saving session to Google Sheet: {e}")
else:
    st.info("Log a climb to start a new session.")


st.markdown("---")

# --- 4. Display Past Sessions ---
st.header("Past Sessions")
try:
    data = worksheet.get_all_records()
    if not data:
        st.info("No past sessions found.")
    else:
        df = pd.DataFrame(data)
        # Group climbs by the SessionID
        grouped = df.groupby('SessionID')
        # Sort sessions by date (newest first)
        sorted_sessions = sorted(grouped, key=lambda x: pd.to_datetime(x[0]), reverse=True)

        for session_id, session_df in sorted_sessions:
            # Use an expander for each session
            with st.expander(f"Session from {session_id}"):
                st.dataframe(session_df[['Discipline', 'Grade', 'Timestamp']].reset_index(drop=True))

except Exception as e:
    st.error(f"Error retrieving past sessions from Google Sheet: {e}")