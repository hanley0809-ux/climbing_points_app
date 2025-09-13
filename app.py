import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# Set page title and theme
st.set_page_config(
    page_title="🧗 Climbing Points",
    layout="centered",
    initial_sidebar_state="auto"
)

# Custom Theming
st.markdown(
    """
    <style>
    .reportview-container {
        background: #F8F8F8;
    }
    .css-1d391kg e16zmk1e3 {
        background-color: #F8F8F8;
    }
    .stSelectbox > label {
        color: #F5A623;
    }
    .stButton > button {
        background-color: #F5A623;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #E08E0B;
    }
    h1 {
        color: #F5A623;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Log a New Climb")

# Authenticate with Google Sheets
@st.cache_resource
def get_google_sheet_client():
    try:
        # Load service account credentials from Streamlit secrets
        gcp_service_account_info = st.secrets["gcp_service_account"]
        # Comment out the deployment line
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])

        # Add the local testing line
        # gc = gspread.service_account(filename="google_credentials.json")
        return gc
    except Exception as e:
        st.error(f"Error authenticating with Google Sheets. Make sure your `secrets.toml` is configured correctly: {e}")
        st.stop()

gc = get_google_sheet_client()

try:
    spreadsheet = gc.open("Climbing Points Data")
    worksheet = spreadsheet.worksheet("Climbs")
except gspread.exceptions.SpreadsheetNotFound:
    st.error("Google Sheet 'Climbing Points Data' not found. Please create it with a worksheet named 'Climbs'.")
    st.stop()
except gspread.exceptions.WorksheetNotFound:
    st.error("Worksheet 'Climbs' not found in 'Climbing Points Data'. Please create it.")
    st.stop
except Exception as e:
    st.error(f"Error accessing Google Sheet or Worksheet: {e}")
    st.stop()


# Form for input
with st.form("climb_log_form"):
    discipline = st.selectbox(
        "Discipline",
        ("Bouldering", "Sport Climbing"),
        key="discipline_select"
    )

    grade_options = []
    if discipline == "Bouldering":
        grade_options = [f"V{i}" for i in range(11)]
    else:  # Sport Climbing
        grade_options = [f"{i}A" for i in range(5, 8)] + [f"{i}B" for i in range(5, 8)] + [f"{i}C" for i in range(5, 8)]
        # Filter out invalid grades like 5D, 5E, etc. and keep 5A to 7C
        grade_options = [g for g in grade_options if g[0].isdigit() and int(g[0]) <= 7 and g[1] in ['A', 'B', 'C']]
        grade_options = sorted(list(set(grade_options)), key=lambda x: (int(x[0]), x[1]))


    grade = st.selectbox(
        "Grade",
        grade_options,
        key="grade_select"
    )

    submitted = st.form_submit_button("🚀 Send It!")

    if submitted:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_row = [discipline, grade, timestamp]
            worksheet.append_row(new_row)
            st.success("Climb logged successfully! Keep crushing it! 🎉")
            st.balloons()
        except Exception as e:
            st.error(f"Error appending row to Google Sheet: {e}")

st.markdown("---")
st.subheader("Recent Climbs")
try:
    # Fetch all records to display them
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)

    if not df.empty:
        # Ensure 'Timestamp' column exists and is parsed as datetime
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df = df.sort_values(by='Timestamp', ascending=False)
        st.dataframe(df)
    else:
        st.info("No climbs logged yet. Go send something!")
except Exception as e:
    st.error(f"Error retrieving data from Google Sheet: {e}")