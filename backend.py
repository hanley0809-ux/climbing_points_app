# backend.py
import gspread
import pandas as pd
from datetime import datetime

# This function must be passed the secrets from Streamlit
def get_worksheet(secrets):
    gc = gspread.service_account_from_dict(secrets)
    worksheet = gc.open("Climbing Points Data").worksheet("Climbs")
    return worksheet

def get_all_climbs(worksheet):
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def save_new_session(worksheet, climbs_to_save):
    session_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records_to_add = []
    for climb in climbs_to_save:
        row = [climb["Discipline"], climb["Grade"], climb["Timestamp"], session_id]
        records_to_add.append(row)
    
    worksheet.append_rows(records_to_add)