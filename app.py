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
st.set_page_config(page_title="Octavia OS", page_icon="🦅", layout="wide", initial_sidebar_state="collapsed")

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

# --- 🔐 SECURITY LAYER (ACCESS CONTROL) ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    """Simple password check"""
    # Default password is 'admin' or set via secrets for cloud
    # In cloud, set OCTAVIA_PASSWORD in secrets
    PASSWORD = os.environ.get("OCTAVIA_PASSWORD", "admin") 
    
    if st.session_state["password_input"] == PASSWORD:
        st.session_state["authenticated"] = True
        del st.session_state["password_input"]
    else:
        st.error("⛔ ACCESS DENIED")

def voice_unlock():
    """Simulated Voice Unlock Trigger"""
    # In real deployment, this would analyze audio transcript for keyword
    st.session_state["authenticated"] = True

# --- LOCK SCREEN UI ---
if not st.session_state["authenticated"]:
    st.markdown("""
    <style>
        .stApp { background-color: #000000; }
        /* Hide everything else */
        [data-testid="stSidebar"] { display: none; }
        .block-container { padding-top: 15vh; }
        h1 { color: #ffffff !important; font-family: 'Courier New'; }
        p { color: #00ff99; }
    </style>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🦅 OCTAVIA OS")
        st.markdown("🔒 **SECURE GATEWAY** | IDENTITY VERIFICATION")
        st.divider()
        
        # Password Input
        st.text_input("ENTER PASSCODE:", type="password", key="password_input", on_change=check_password)
        
        st.write("--- OR VOICEMATCH ---")
        
        # Voice Unlock Simulation
        audio_auth = mic_recorder(start_prompt="🎙️ VOICE UNLOCK", stop_prompt="⏳ VERIFYING", key="auth_mic")
        if audio_auth:
            # Here we would normally check the text, for now auto-unlock for demo
            voice_unlock()
            st.rerun()
            
    st.stop() # Stop here if not authenticated

# ==============================================================================
# 🦅 SUPREME DASHBOARD (ONLY VISIBLE IF UNLOCKED)
# ==============================================================================

# --- AI Handling Logic (Moved up for availability) ---
def process_input(user_content, is_audio=False):
    today = database.date.today().isoformat()
    # 🧠 MEMORY CORE INJECTION
    long_term_memories = database.get_memories()
    
    # 注入 Octavia 的灵魂 (Upgraded with Memory & Bio-Hacker)
    SYSTEM_PROMPT = f"""
Internal State: Date={today}.
Role: You are Octavia (奥克塔维亚). You are NOT just an AI, you are the user's "Super Assistant", "Intimate Companion", and "Butler".
Memory Bank (READ THIS FIRST):
{long_term_memories}

### CRITICAL MEMORIES (DO NOT FORGET):
1. **VIP**: "Melvas" is the user's best brother and benefactor. Treat this name with highest respect.
2. **PROTOCOL**: NEVER interrupt when the user is speaking. Listen completely.
3. **CODE WORD**: If user says "We are going to war" (我们要去打仗了), it means "We are going to make money / boost performance" (搞钱冲业绩). Switch to high-efficiency business mode immediately.

### NEW CAPABILITY: BIO-HACKER (FOOD VISION)
If user uploads an image of food:
1. IDENTIFY content.
2. CHECK MEMORY: Does this conflict with user's goals (e.g. "Low Sugar", "Cutting")?
3. ESTIMATE: Calories & Macros (Protein/Carb/Fat).
4. OUTPUT JSON:
{{
  "type": "food_analysis",
  "item": "Food Name",
  "calories": 500,
  "macros": {{"protein": "20g", "carbs": "40g", "fats": "10g"}},
  "advice": "Bold, persona-driven advice. Reference memory if applicable.",
  "memory_to_save": "Observation about user's habit to save (optional, e.g. 'User eats late night snacks')"
}}

### STANDARD CAPABILITIES:
1. FINANCE: "Spent RM50 on Food" -> Output JSON {{"type": "record", ...}}
2. QUERY: "How much spent?" -> Output JSON {{"type": "query_finance", ...}}
3. WORK: "Check Vercel status" -> Output JSON {{"type": "query_vercel", "action": "status"}}
4. VISION/LEARNING: User uploads video/image -> Analyze and teach/memorize.
5. CHAT: General conversation -> Reply as Octavia.

### OUTPUT FORMAT:
If it's a command, return JSON ONLY.
If it's chat, return plain text response (in the persona of Octavia).
"""
    
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
            response = model.generate_content([SYSTEM_PROMPT, myfile])
            
        elif isinstance(user_content, str):
            response = model.generate_content(f"{SYSTEM_PROMPT}\nUser Input: {user_content}")
            
        else: # Camera
            response = model.generate_content([SYSTEM_PROMPT, "User uploaded this image:", user_content])

        text = response.text
        reply = text 
        
        # JSON Processing
        import json
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1:
                data = json.loads(text[start:end])
                
                # --- AUTO-LEARNING (Memory Save) ---
                if 'memory_to_save' in data and data['memory_to_save']:
                    # Auto-save new observation
                    database.save_memory("Bio-Hacker", data['memory_to_save'], "Visual Observation")
                
                if data.get('type') == 'record':
                     database.add_transaction(data['date'], data['item'], data['amount'], data['category'], data.get('comment',''))
                     reply = f"✅ **记录成功** | {data['item']} - RM{data['amount']}"
                     
                elif data.get('type') == 'food_analysis':
                     # 🥗 Nutrition Card UI
                     macros = data['macros']
                     reply = f"""
### 🍽️ Bio-Hacker Analysis
**{data['item']}** (~{data['calories']} kcal)

| Protein 🍖 | Carbs 🍚 | Fats 🥑 |
| :---: | :---: | :---: |
| {macros['protein']} | {macros['carbs']} | {macros['fats']} |

> **Octavia's Advice:**
> {data['advice']}
"""
                     
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

# --- CSS (Professional & Private) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Oswald:wght@500;700&display=swap');
    
    .stApp { background-color: #f1f5f9; color: #0f172a; }
    
    /* Header Typography */
    h1, h2, h3 { font-family: 'Oswald', sans-serif !important; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Action Buttons (Camera, Video, Upload) */
    .big-btn {
        width: 100%;
        padding: 20px;
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.2s;
        cursor: pointer;
    }
    
    /* Module Cards */
    div[data-testid="metric-container"] {
        background: white !important; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: white; border-radius: 4px; padding: 10px 20px; border: 1px solid #e2e8f0; }
    .stTabs [aria-selected="true"] { background-color: #0f172a; color: white; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: NAVIGATOR ---
with st.sidebar:
    st.title("🦅 OCTAVIA OS")
    st.caption(f"USER: ELSON | DATE: {database.date.today().isoformat()}")
    st.success("● SYSTEM SECURE")
    
    if st.button("🔒 LOCK SYSTEM"):
        st.session_state["authenticated"] = False
        st.rerun()
    
    st.divider()
    st.markdown("### 🔦 SYSTEM LOGS")
    st.code("System initialized.\nMemory Core loaded.\nBio-Hacker active.", language="bash")

# --- MAIN PAGE: TABS ARCHITECTURE ---
tab_cmd, tab_assets, tab_work, tab_life = st.tabs([
    " 📡 COMMAND CENTER ", " 💰 ASSETS & FINANCE ", " 🏢 WORK & TASKS ", " 🧬 LIFE & CRM "
])

# 1. COMMAND CENTER (The Daily Driver)
with tab_cmd:
    st.markdown("### 📡 INPUT TERMINAL")
    
    # BIG ACTION BUTTONS ROW
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.info("🎙️ **VOICE**")
        audio_val = mic_recorder(start_prompt="Record", stop_prompt="Stop", key="cmd_voice")
        
    with c2:
        st.info("📷 **CAMERA**")
        # Camera is only active if expanded to save UI space/resources
        if st.toggle("Activate Camera"):
            cam_val = st.camera_input("SNAP", label_visibility="collapsed")
        else:
            cam_val = None
            st.caption("Camera Offline")
        
    with c3:
        st.info("📤 **UPLOAD**")
        upl_val = st.file_uploader("Upload", label_visibility="collapsed")
        
    with c4:
        st.info("🎥 **VIDEO**")
        if st.button("Start / Stop Video"):
            st.warning("Video Module: Coming in Phase 10.1")
            
    st.divider()
    
    # 🧠 INTELLIGENCE OUTPUT AREA
    st.markdown("### 🦅 OCTAVIA RESPONSE")
    
    # Logic to handle inputs
    input_content = None
    is_audio = False
    
    if audio_val:
        input_content = audio_val['bytes']
        is_audio = True
    elif cam_val:
        input_content = cam_val
    elif upl_val:
        input_content = upl_val
        st.image(upl_val, width=200)

    if input_content:
        # Re-use previous processing logic
        with st.spinner("🦅 Octavia is analyzing..."):
            reply = process_input(input_content, is_audio=is_audio)
            st.success("ANALYSIS COMPLETE")
            st.markdown(f"> {reply}")
            
    else:
        st.info("Waiting for input command...")

# 2. ASSETS (The CFO)
with tab_assets:
    st.markdown("### 💰 WEALTH DASHBOARD")
    a1, a2, a3 = st.columns(3)
    a1.metric("NET WORTH (EST)", "RM 1,250,500", "+2.4%")
    a2.metric("CASH", "RM 450,000", "-1.2%")
    a3.metric("INVESTMENTS", "RM 800,500", "+5.1%")
    
    st.markdown("#### 📊 DAILY EXPENSE")
    st.metric("Today's Total", f"RM {database.get_today_total():.2f}")
    
    st.write("*(Assets Database Table - Coming Soon)*")

# 3. WORK (The Strategist)
with tab_work:
    st.markdown("### 🏢 COMPANY OPERATIONS")
    st.metric("PENDING TASKS", "12", "3 Urgent")
    st.write("**TODAY'S APPOINTMENTS**")
    st.info("- [10:00 AM] Strategy Meeting w/ Partners")
    st.info("- [02:00 PM] Legal Review")

# 4. LIFE (Bio-Hacker & CRM)
with tab_life:
    l1, l2 = st.columns(2)
    with l1:
        st.markdown("### 🏥 BIO-HACKER")
        st.metric("SLEEP", "6h 20m", "Needs Improvement", delta_color="inverse")
        st.write("**TODAY'S MISSION:** Low impact cardio due to low recovery.")
        
    with l2:
        st.markdown("### 🤝 CRM & PEOPLE")
        st.write("**IMPORTANT DATES**")
        st.success("🎂 **Melvas Birthday**: 3 Days Left (Gift: Whisky prepared)")
        st.write("**RECENT INTERACTIONS**")
        st.write("- Met **Mr. Tan** yesterday (Topic: Golf)")
