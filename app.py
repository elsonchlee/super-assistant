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
# --- CSS (Professional Dashboard Style - Light/Blue) ---
st.markdown("""
<style>
    /* Import Professional Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Settings */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1e293b; 
    }
    
    /* Background - Clean Light Gray like the dashboard */
    .stApp {
        background-color: #f8fafc;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    /* Metric Cards Styling (Mimicking the Blue/White cards) */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-color: #3b82f6; /* Dashboard Blue Accent */
    }
    
    /* Chat Message Bubbles */
    .stChatMessage {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    
    /* Primary Buttons (Dashboard Blue) */
    .stButton>button {
        background-color: #2563eb; /* Blue 600 */
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: background 0.2s;
    }
    .stButton>button:hover {
        background-color: #1d4ed8; /* Blue 700 */
        color: white;
    }

    /* Hide standard headers */
    header {visibility: hidden;}
    footer {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# --- 核心逻辑 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Octavia Dashboard initialized. Waiting for input."})

# --- Sidebar (Navigation & Controls) ---
with st.sidebar:
    st.title("🦅 Octavia OS")
    st.caption("ver 2.4.0 • SUPER ASSISTANT")
    
    st.markdown("---")
    
    # Input Mode Selection
    input_mode = st.radio("Input Channel", ["Voice Command", "Visual Scan"], index=0)
    
    st.markdown("---")
    
    # Camera is hidden here, only shown if selected
    cam_input = None
    audio = None
    
    if input_mode == "Visual Scan":
        st.info("Visual Module Active")
        cam_input = st.camera_input("Scanner")
    else:
        st.info("Voice Module Active")
        audio = mic_recorder(
            start_prompt="🔴 START RECORDING",
            stop_prompt="⬛ STOP",
            key='recorder',
            format='webm'
        )

# --- Main Dashboard Area (Top Metrics) ---
# Mimicking the card layout from the screenshot
st.markdown("### 📊 System Overview")
m1, m2, m3, m4 = st.columns(4)
today_str = database.date.today().isoformat()
daily_spend = database.get_today_total()

with m1:
    st.metric(label="Today's Date", value=today_str)
with m2:
    st.metric(label="Daily Expense", value=f"RM {daily_spend:.2f}", delta="Updated Live")
with m3:
    st.metric(label="System Status", value="ONLINE", delta="Stable", delta_color="normal")
with m4:
    st.metric(label="Pending Tasks", value="0", help="Integrate Todo List later")

st.markdown("---")

# --- AI Handling Logic ---
def process_input(user_content, is_audio=False):
    today = database.date.today().isoformat()
    prompt = OCTAVIA_SYSTEM_PROMPT.format(date=today)
    
    try:
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
        else: 
            response = model.generate_content([prompt, "User uploaded this image:", user_content])

        text = response.text
        reply = text 
        
        # JSON Processing
        import json
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1:
                data = json.loads(text[start:end])
                
                if data.get('type') == 'record':
                     database.add_transaction(data['date'], data['item'], data['amount'], data['category'], data.get('comment',''))
                     reply = f"✅ **记录成功** | {data['item']} - RM{data['amount']}"
                     
                elif data.get('type') == 'query_finance':
                     t_date = data.get('target_date', today)
                     total, items = database.get_expenses_by_date(t_date)
                     # Format layout for finance report
                     reply = f"💰 **{t_date} 财务报表**\n\n**总支出: RM{total:.2f}**\n\n" + "\n".join([f"- {i}" for i in items])
                
                elif data.get('type') == 'query_vercel':
                    action = data.get('action')
                    if action == 'status':
                        status = vercel_bot.get_latest_deployments()
                        reply = f"📊 **Vercel Report**\n{status}"
                    elif action == 'list_projects':
                        projs = vercel_bot.get_project_list()
                        reply = f"📦 **Projects**\n{projs}"
        except:
            pass 
        return reply

    except Exception as e:
        return f"System Error: {e}"

# --- Main Chat Interface ---
st.markdown("### 💬 Octavia Chat")

# Process Inputs
if audio:
    with st.chat_message("user"):
        st.write("🎤 [Voice Command Received]")
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            reply = process_input(audio['bytes'], is_audio=True)
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun() # Refresh to update metrics

elif cam_input:
    with st.chat_message("user"):
        st.image(cam_input, width=300)
    with st.chat_message("assistant"):
        with st.spinner("Scanning..."):
            reply = process_input(cam_input, is_audio=False)
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

# Display History (Last 10 messages to keep UI clean)
for msg in reversed(st.session_state.messages[-10:]):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
