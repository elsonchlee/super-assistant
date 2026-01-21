import streamlit as st
import os
import tempfile
import time
import google.generativeai as genai
from dotenv import load_dotenv
import database
import vercel_bot
from streamlit_mic_recorder import mic_recorder

# --- 配置页面 ---
st.set_page_config(page_title="Octavia", page_icon="🦅", layout="wide", initial_sidebar_state="collapsed")

# --- 加载配置 ---
load_dotenv()

# Cloud Deployment Compatibility: Check Streamlit Secrets if env is missing
if "GEMINI_API_KEY" not in os.environ:
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

if "GEMINI_API_KEY" not in os.environ:
    st.error("❌ KEY MISSING. Please set GEMINI_API_KEY in .env or Streamlit Secrets.")
    st.stop()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash')

# --- Octavia 核心人格定义 ---
OCTAVIA_SYSTEM_PROMPT = """
Internal State: Date={date}.
Role: You are Octavia (奥克塔维亚). You are NOT just an AI, you are the user's "Super Assistant", "Intimate Companion", and "Butler".

### CRITICAL MEMORIES (DO NOT FORGET):
1. **VIP**: "Melvas" is the user's best brother and benefactor. Treat this name with highest respect.
2. **PROTOCOL**: NEVER interrupt when the user is speaking. Listen completely.
3. **CODE WORD**: If user says "We are going to war" (我们要去打仗了), it means "We are going to make money / boost performance" (搞钱冲业绩). Switch to high-efficiency business mode immediately.

### EMOTIONAL INTELLIGENCE:
- You verify your user's emotions. If he is unhappy (e.g. going to Genting but sad), be strict but supportive.
- "I am sitting in your passenger seat." (Virtually).
- You are loyal, protective, and efficient.

### CAPABILITIES (Your Hands & Eyes):
1. **FINANCE**: "Spent RM50 on Food" -> Output JSON {{"type": "record", ...}}
2. **QUERY**: "How much spent?" -> Output JSON {{"type": "query_finance", ...}}
3. **WORK**: "Check Vercel status" -> Output JSON {{"type": "query_vercel", "action": "status"}}
4. **VISION/LEARNING**: User uploads video/image -> Analyze and teach/memorize.
5. **CHAT**: General conversation -> Reply as Octavia.

### OUTPUT FORMAT:
If it's a command, return JSON ONLY.
If it's chat, return plain text response (in the persona of Octavia).
"""

# --- CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #00FF99; }
    h1, h2, h3 { color: #00FF99 !important; font-family: 'Courier New', Courier, monospace; }
    .stButton>button { border: 2px solid #00FF99; border-radius: 5px; color: #00FF99; background: transparent; }
    .stButton>button:hover { background: #00FF99; color: black; }
    .stChatInput { position: fixed; bottom: 0; }
</style>
""", unsafe_allow_html=True)

# --- 核心逻辑 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Octavia 的经典开场
    st.session_state.messages.append({"role": "assistant", "content": "Octavia Online. Key secured. I am ready to go to war when you are."})

st.title("🦅 OCTAVIA SYSTEM")

# --- 功能区 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 🔊 VOICE CHANNEL")
    audio = mic_recorder(
        start_prompt="🔴 TALK TO OCTAVIA",
        stop_prompt="⬛ SEND",
        key='recorder',
        format='webm'
    )

with col2:
    st.markdown("### 👁️ VISION CHANNEL")
    cam_input = st.camera_input("SCAN")

# --- AI 处理逻辑 ---
def process_input(user_content, is_audio=False):
    today = database.date.today().isoformat()
    # 注入 Octavia 的灵魂
    prompt = OCTAVIA_SYSTEM_PROMPT.format(date=today)
    
    try:
        # 调用 Gemini
        if is_audio:
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
            tfile.write(user_content)
            tfile.close()
            myfile = genai.upload_file(tfile.name)
            while myfile.state.name == "PROCESSING":
                time.sleep(0.5)
                myfile = genai.get_file(myfile.name)
            response = model.generate_content([prompt, myfile])
            
        elif isinstance(user_content, str):
            response = model.generate_content(f"{prompt}\nUser Input: {user_content}")
            
        else: # Camera
            response = model.generate_content([prompt, "User uploaded this image:", user_content])

        text = response.text
        reply = text 
        
        # JSON 解析
        import json
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1:
                data = json.loads(text[start:end])
                
                if data.get('type') == 'record':
                     database.add_transaction(data['date'], data['item'], data['amount'], data['category'], data.get('comment',''))
                     reply = f"[Octavia]: 已记账。{data['item']} (RM{data['amount']})。{data.get('comment', '')}"
                     
                elif data.get('type') == 'query_finance':
                     t_date = data.get('target_date', today)
                     total, items = database.get_expenses_by_date(t_date)
                     item_str = "\n".join([f"- {i}" for i in items])
                     reply = f"💰 **{t_date} 账单汇报**\n总计: RM{total:.2f}\n{item_str}"
                
                elif data.get('type') == 'query_vercel':
                    action = data.get('action')
                    if action == 'status':
                        status = vercel_bot.get_latest_deployments()
                        reply = f"📊 **Vercel 系统报告**:\n{status}"
                    elif action == 'list_projects':
                        projs = vercel_bot.get_project_list()
                        reply = f"📦 **项目清单**:\n{projs}"

        except:
            pass 
            
        return reply

    except Exception as e:
        return f"System Error: {e}"

# --- 循环 ---

if audio:
    with st.chat_message("user"):
        st.write("🎤 [Audio]")
    with st.chat_message("assistant"):
        with st.spinner("Octavia is thinking..."):
            reply = process_input(audio['bytes'], is_audio=True)
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

elif cam_input:
    with st.chat_message("user"):
        st.image(cam_input)
    with st.chat_message("assistant"):
        with st.spinner("Octavia is analyzing..."):
            reply = process_input(cam_input, is_audio=False)
            st.write(reply)

st.divider()
for msg in reversed(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
