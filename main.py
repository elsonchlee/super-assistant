import os
import json
import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import database

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

print("\n" + "="*50)
print("⏳ 时空穿梭版助手 (V4.0) 已就绪")
print("试试问: '昨天花了多少?' 或 '上周五吃了什么?'")
print("="*50 + "\n")

def extract_json(text):
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != -1:
            return json.loads(text[start:end])
    except:
        pass
    return None

while True:
    try:
        user_input = input("> ")
    except EOFError: break
    
    if user_input.lower() in ["quit", "exit"]: break
    if not user_input.strip(): continue

    try:
        print("🧠 正在计算时空坐标...")
        today = datetime.date.today().isoformat()
        
        # --- 核心升级：让 AI 负责推算日期 ---
        prompt = f"""
        Current Date: {today}
        User Input: "{user_input}"
        
        Task:
        1. If user wants to RECORD (spend money), output type="record".
        2. If user wants to QUERY (ask history), output type="query".
           CRITICAL: Convert words like "yesterday", "last friday", "今天" into actual date strings (YYYY-MM-DD).
        
        Output JSON ONLY:
        
        [CASE 1: RECORD]
        {{
            "type": "record",
            "date": "{today}",
            "item": "string", 
            "amount": number,
            "category": "Food/Transport/Shopping/Other",
            "comment": "Sarcastic remark in Chinese"
        }}

        [CASE 2: QUERY]
        {{
            "type": "query",
            "target_date": "YYYY-MM-DD" 
        }}
        """
        
        response = model.generate_content(prompt)
        data = extract_json(response.text)

        if not data:
            print("⚠️ 信号不好，再说一遍？")
            continue

        # --- 场景 1: 记账 ---
        if data.get('type') == 'record':
            # Basic validation
            if data.get('amount', 0) > 0:
                database.add_transaction(
                    data.get('date'), data.get('item'), data.get('amount'), 
                    data.get('category'), data.get('comment')
                )
                print(f"✅ 记账成功: {data.get('item')} (RM{data.get('amount')})")
                print(f"🦜 吐槽: {data.get('comment')}")

        # --- 场景 2: 查旧账 (Time Travel) ---
        elif data.get('type') == 'query':
            target_date = data.get('target_date')
            print(f"🔎 正在穿越回 {target_date} 查账...")
            
            total, items = database.get_expenses_by_date(target_date)
            
            print(f"\n📅 日期: {target_date}")
            print(f"💰 当天总支出: RM {total:.2f}")
            if items:
                print("🧾 消费明细:")
                for i in items:
                    print(f"   - {i}")
            else:
                print("   (那天好像没花钱，或者是没记账？)")
            print("-" * 30 + "\n")

    except Exception as e:
        print(f"❌ 系统短路: {e}")