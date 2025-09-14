import gspread
import pandas as pd
from datetime import datetime

GRADE_ORDER = [
    "8a", "7c+", "7c", "7b+", "7b", "7a+", "7a", "6c+", "6c", "6b+", "6b", "6a+", "6a", "5c", "5b", "5a",
    "V10", "V9", "V8", "V7", "V6", "V5", "V4", "V3", "V2", "V1", "V0",
    "Blue", "Green/Blue", "Green", "Yellow/Green", "Yellow", "Orange/Yellow", "Orange", "Red/Orange", "Red",
    "8", "7", "6", "5", "4", "3", "2", "1"
]

def get_worksheet(secrets):
    gc = gspread.service_account_from_dict(secrets)
    worksheet = gc.open("Climbing Points Data").worksheet("Climbs")
    return worksheet

def get_all_climbs(worksheet):
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    if 'Timestamp' in df.columns and not df.empty:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    if 'Date' in df.columns and not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
    return df

def save_new_session(worksheet, climbs_to_save, user_name, session_name=None):
    session_date = datetime.now().strftime("%Y-%m-%d")
    final_session_name = session_name if session_name else f"Session from {session_date}"
    records_to_add = []
    for climb in climbs_to_save:
        row = [climb["Discipline"], climb["Grade"], climb["Timestamp"], final_session_name, session_date, climb.get("Gym", ""), user_name]
        records_to_add.append(row)
    
    worksheet.append_rows(records_to_add)

def get_dashboard_stats(df):
    if df.empty:
        return {"total_climbs_month": 0, "hardest_boulder": "N/A", "hardest_sport": "N/A"}
    now = datetime.now()
    climbs_this_month = df[df['Timestamp'].dt.month == now.month].shape[0]

    def find_hardest(discipline):
        discipline_df = df[df['Discipline'] == discipline]
        if discipline_df.empty: return "N/A"
        discipline_df['Grade'] = pd.Categorical(discipline_df['Grade'], categories=GRADE_ORDER, ordered=True)
        return discipline_df['Grade'].min()

    hardest_boulder = find_hardest("Bouldering")
    hardest_sport = find_hardest("Sport Climbing")

    return {"total_climbs_month": climbs_this_month, "hardest_boulder": hardest_boulder, "hardest_sport": hardest_sport}

def get_session_summary(session_df):
    total_climbs = len(session_df)
    session_df['Grade'] = pd.Categorical(session_df['Grade'], categories=GRADE_ORDER, ordered=True)
    hardest_climb = session_df['Grade'].min()
    return {"total_climbs": total_climbs, "hardest_climb": hardest_climb}