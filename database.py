import gspread
from google.oauth2.service_account import Credentials
from datetime import date

# 1. 连接 Google Sheets
try:
    # 优先尝试 Cloud 模式 (Streamlit Secrets)
    import streamlit as st
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        client = gspread.authorize(creds)
    # 其次尝试本地模式
    elif os.path.exists('service_account.json'):
        client = gspread.service_account(filename='service_account.json')
    else:
        # Fallback / Error
        raise FileNotFoundError("找不到 service_account.json 也没有配置 Secrets")

    # Use the known SHEET_ID for reliability, or fallback to name
    SHEET_ID = "109FTKIWh5LhypHuiXa9MemBxieGG4ck4M7eiem2t5pw" 
    sheet = client.open_by_key(SHEET_ID).worksheet("Transactions")
except Exception as e:
    print(f"Connection Error: {e}")
    # Fallback attempt if user insists on "finance_data" name matching
    try:
        if 'client' in locals():
            sheet = client.open("finance_data").sheet1
    except:
        sheet = None

def add_transaction(date_str, item, amount, category, comment=""):
    """存账"""
    if not sheet: return "Error: No Sheet"
    try:
        sheet.append_row([date_str, item, amount, category, comment])
        return "Saved"
    except Exception as e:
        return f"Error: {e}"

def get_expenses_by_date(target_date_str):
    """🔥 核心升级: 可以查 任意一天 的账"""
    if not sheet: return 0, ["Error: No Sheet"]
    try:
        all_records = sheet.get_all_records()
        
        total = 0
        items = []
        
        for row in all_records:
            # 比对每一行的日期，是否等于我们要查的那天
            # row['Date'] might be int or string depending on format
            if str(row.get('Date', '')) == target_date_str:
                # 清洗数据，防止 RM 符号干扰
                clean_amount = str(row.get('Amount', 0)).replace('RM', '').replace(',', '').strip()
                if clean_amount:
                    val = float(clean_amount)
                    total += val
                    items.append(f"{row.get('Item', '?')} ({val})")
        
        return total, items
    except Exception as e:
        return 0, [f"查询出错: {e}"]
