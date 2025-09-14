# backend.py
import gspread
import pandas as pd
from datetime import datetime

# --- Grade Order List (Hardest to Easiest) ---
# We define this once to determine the "hardest" climb
GRADE_ORDER = [
    "8a", "7c+", "7c", "7b+", "7b", "7a+", "7a", 
    "6c+", "6c", "6b+", "6b", "6a+", "6a", 
    "5c", "5b", "5a",
    "V10", "V9", "V8", "V7", "V6", "V5", 
    "V4", "V3", "V2", "V1", "V0"
]

def get_worksheet(secrets):
    """Connects to the Google Sheet and returns the worksheet object."""
    gc = gspread.service_account_from_dict(secrets)
    worksheet = gc.open("Climbing Points Data").worksheet("Climbs")
    return worksheet

def get_all_climbs(worksheet):
    """Fetches all climb records and returns them as a DataFrame."""
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    # Ensure Timestamp is a datetime object for filtering
    if 'Timestamp' in df.columns and not df.empty:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

def save_new_session(worksheet, climbs_to_save):
    """Saves a list of climbs as a new session to the Google Sheet."""
    session_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records_to_add = []
    for climb in climbs_to_save:
        row = [climb["Discipline"], climb["Grade"], climb["Timestamp"], session_id]
        records_to_add.append(row)
    
    worksheet.append_rows(records_to_add)

# --- NEW FUNCTION: Calculate Dashboard Stats ---
def get_dashboard_stats(df):
    """Processes the DataFrame to calculate stats for the dashboard."""
    if df.empty:
        return {"total_climbs_month": 0, "hardest_boulder": "N/A", "hardest_sport": "N/A"}

    # Calculate climbs this month
    now = datetime.now()
    climbs_this_month = df[df['Timestamp'].dt.month == now.month].shape[0]

    # Find hardest climbs
    def find_hardest(discipline):
        discipline_df = df[df['Discipline'] == discipline]
        if discipline_df.empty:
            return "N/A"
        # Create a categorical type with our custom order
        discipline_df['Grade'] = pd.Categorical(discipline_df['Grade'], categories=GRADE_ORDER, ordered=True)
        # Find the minimum grade, which is the "hardest" based on our list order
        return discipline_df['Grade'].min()

    hardest_boulder = find_hardest("Bouldering")
    hardest_sport = find_hardest("Sport Climbing")

    return {
        "total_climbs_month": climbs_this_month,
        "hardest_boulder": hardest_boulder,
        "hardest_sport": hardest_sport
    }

# --- NEW FUNCTION: Summarize a Session ---
def get_session_summary(session_df):
    """Processes a session's DataFrame to get summary stats."""
    total_climbs = len(session_df)
    
    # Find the hardest climb in this specific session
    session_df['Grade'] = pd.Categorical(session_df['Grade'], categories=GRADE_ORDER, ordered=True)
    hardest_climb = session_df['Grade'].min()
    
    return {
        "total_climbs": total_climbs,
        "hardest_climb": hardest_climb
    }