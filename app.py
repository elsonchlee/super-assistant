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

# --- CSS (Premium Glassmorphism & Cyberpunk Style) ---
st.markdown("""
<style>
    /* Global Font & Reset */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Background - Deep Space Gradient */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0a0e17 0%, #04070a 90%);
        color: #e0e0e0;
    }

    /* Headers - Techy & Glowing */
    h1, h2, h3 {
        font-family: 'JetBrains Mono', monospace !important;
        background: linear-gradient(90deg, #00f2ff, #00ff99);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(0, 242, 255, 0.3);
        letter-spacing: -1px;
    }

    /* Glass Cards for Layout */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease;
    }
    .stChatMessage:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 242, 255, 0.2);
    }

    /* Buttons - Cyberpunk Style */
    .stButton>button {
        background: rgba(0, 242, 255, 0.05);
        border: 1px solid rgba(0, 242, 255, 0.2);
        color: #00f2ff;
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        font-weight: 600;
    }
    .stButton>button:hover {
        background: rgba(0, 242, 255, 0.15);
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.4);
        border-color: #00f2ff;
        color: white;
    }

    /* Camera Input - Hidden by Default Styling */
    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
    }
    
    /* Clean up top bar */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 核心逻辑 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Octavia 的经典开场
    st.session_state.messages.append({"role": "assistant", "content": "Octavia v2.0 Online. Systems Nominal. Ready for directive."})

# Modern Title Layout
c1, c2 = st.columns([0.8, 0.2])
with c1:
    st.title("🦅 OCTAVIA")
with c2:
    st.caption(f"SYSTEM DATE: {database.date.today().isoformat()}")

# --- 功能区 (Modern Layout) ---
col1, col2 = st.columns([1, 1])

with col1:
    # Voice Interface
    audio = mic_recorder(
        start_prompt="🔴 VOICE COMMAND",
        stop_prompt="⬛ PROCESSING",
        key='recorder',
        format='webm'
    )

with col2:
    # Hidden Vision System
    with st.expander("👁️ VISION SYSTEM (OFFLINE)", expanded=False):
        st.caption("Activate to allow Octavia to see.")
        cam_input = st.camera_input("SCANNING MODULE")

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
                     reply = f"✅ **TRANSACTION LOGGED**\n- Item: {data['item']}\n- Amount: RM{data['amount']}\n- Note: {data.get('comment', 'N/A')}"
                     
                elif data.get('type') == 'query_finance':
                     t_date = data.get('target_date', today)
                     total, items = database.get_expenses_by_date(t_date)
                     item_str = "\n".join([f"- {i}" for i in items])
                     reply = f"💰 **FINANCIAL REPORT ({t_date})**\nTotal Expenditure: **RM{total:.2f}**\n\n{item_str}"
                
                elif data.get('type') == 'query_vercel':
                    action = data.get('action')
                    if action == 'status':
                        status = vercel_bot.get_latest_deployments()
                        reply = f"📊 **SYSTEM DIAGNOSTICS**:\n{status}"
                    elif action == 'list_projects':
                        projs = vercel_bot.get_project_list()
                        reply = f"📦 **AVAILABLE MODULES**:\n{projs}"

        except:
            pass 
            
        return reply

    except Exception as e:
        return f"⚠️ SYSTEM ERROR: {e}"

# --- 循环 ---

if audio:
    with st.chat_message("user"):
        st.write("🎤 [Audio Encrypted]")
    with st.chat_message("assistant"):
        with st.spinner("Processing Signal..."):
            reply = process_input(audio['bytes'], is_audio=True)
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

elif cam_input:
    with st.chat_message("user"):
        st.image(cam_input)
    with st.chat_message("assistant"):
        with st.spinner("Analyzing Visual Data..."):
            reply = process_input(cam_input, is_audio=False)
            st.write(reply)

st.divider()
for msg in reversed(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
