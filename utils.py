from datetime import datetime
from zoneinfo import ZoneInfo

def get_ist_date():
    ist = ZoneInfo("Asia/Kolkata")
    return datetime.now(ist)

def log_message(message):
    print(f"[{get_ist_date()}] {message}")
