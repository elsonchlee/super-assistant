import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import os

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

def get_today_total():
    """快捷获取今日总额"""
    today = date.today().isoformat()
    total, _ = get_expenses_by_date(today)
    return total

# --- Memory Core (Long-Term Memory) ---
def get_memories():
    """读取所有记忆"""
    if not sheet: return "No Memory Bank available."
    try:
        # 尝试连接 Memory Sheet
        try:
            mem_sheet = client.open_by_key(SHEET_ID).worksheet("Memory")
        except:
            # 如果不存在，尝试创建（或返回空）
            try:
                mem_sheet = client.open_by_key(SHEET_ID).add_worksheet(title="Memory", rows=1000, cols=4)
                mem_sheet.append_row(["Date", "Category", "Observation", "Context"])
            except:
                return "Memory System Offline (Please create 'Memory' tab in Sheets)"
        
        records = mem_sheet.get_all_records()
        if not records:
            return "No memories yet."
            
        # 格式化记忆为文本
        memory_text = ""
        for r in records:
            memory_text += f"- [{r.get('Category')}] {r.get('Observation')} (Context: {r.get('Context')})\n"
        return memory_text

    except Exception as e:
        return f"Memory Error: {e}"

def save_memory(category, observation, context=""):
    """写入新记忆"""
    if not sheet: return "Error: No Sheet"
    try:
        mem_sheet = client.open_by_key(SHEET_ID).worksheet("Memory")
        today = date.today().isoformat()
        mem_sheet.append_row([today, category, observation, context])
        return True
    except:
        return False

# --- Assets Core (The CFO) ---
def get_assets():
    """获取资产列表"""
    if not sheet: return {"Cash": 0, "Investments": 0, "NetWorth": 0}
    try:
        try:
            asset_sheet = client.open_by_key(SHEET_ID).worksheet("Assets")
        except:
            asset_sheet = client.open_by_key(SHEET_ID).add_worksheet(title="Assets", rows=100, cols=3)
            asset_sheet.append_row(["Category", "Amount", "LastUpdated"])
            # Init default data
            asset_sheet.append_row(["Cash", "0", date.today().isoformat()])
            asset_sheet.append_row(["Investments", "0", date.today().isoformat()])

        records = asset_sheet.get_all_records()
        assets = {"Cash": 0, "Investments": 0, "NetWorth": 0}
        
        for r in records:
            cat = r.get("Category")
            amt = float(str(r.get("Amount")).replace(",",""))
            if cat in assets:
                assets[cat] = amt
            else:
                assets[cat] = amt # Dynamic categories
        
        assets["NetWorth"] = sum([v for k,v in assets.items() if k != "NetWorth"])
        return assets
    except Exception as e:
        return {"Error": str(e)}

def update_asset(category, amount):
    """更新资产余额"""
    if not sheet: return False
    try:
        ws = client.open_by_key(SHEET_ID).worksheet("Assets")
        cell = ws.find(category)
        if cell:
            ws.update_cell(cell.row, 2, amount)
            ws.update_cell(cell.row, 3, date.today().isoformat())
        else:
            ws.append_row([category, amount, date.today().isoformat()])
        return True
    except Exception as e:
        return False

# --- Tasks Core (The Strategist) ---
def get_tasks():
    """获取待办事项"""
    if not sheet: return []
    try:
        try:
            task_sheet = client.open_by_key(SHEET_ID).worksheet("Tasks")
        except:
            task_sheet = client.open_by_key(SHEET_ID).add_worksheet(title="Tasks", rows=1000, cols=4)
            task_sheet.append_row(["Date", "Task", "Status", "Priority"])
        
        records = task_sheet.get_all_records()
        pending = [r for r in records if r.get("Status") != "Done"]
        return pending
    except:
        return []

def add_task(task_name, priority="Normal"):
    if not sheet: return False
    try:
        ws = client.open_by_key(SHEET_ID).worksheet("Tasks")
        ws.append_row([date.today().isoformat(), task_name, "Pending", priority])
        return True
    except:
        return False
