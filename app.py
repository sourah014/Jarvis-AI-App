import streamlit as st
import os
import time
import json
import base64
import requests
import uuid
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import backend 

# 1. Env Load
load_dotenv()

# --- MAINTENANCE MODE ---
if os.getenv("MAINTENANCE_MODE", "False").lower() == "true":
    st.title("🚧 App under Maintenance")
    st.stop()

# Page Setup
st.set_page_config(page_title="Jarvis Pro", page_icon="🤖", layout="wide")

# ==========================================
# --- SESSION PERSISTENCE LOGIC ---
# ==========================================
SESSION_FILE = "active_sessions.json"

def save_session_to_file(session_id, user_data):
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            sessions = json.load(f)
    else:
        sessions = {}
    sessions[session_id] = user_data
    with open(SESSION_FILE, "w") as f:
        json.dump(sessions, f)

def get_session_from_file(session_id):
    if not os.path.exists(SESSION_FILE):
        return None
    with open(SESSION_FILE, "r") as f:
        sessions = json.load(f)
    return sessions.get(session_id)

def logout_session(session_id):
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            sessions = json.load(f)
        if session_id in sessions:
            del sessions[session_id]
            with open(SESSION_FILE, "w") as f:
                json.dump(sessions, f)

# --- SESSION STATE INITIALIZATION ---
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# --- AUTO-LOGIN CHECK ---
query_params = st.query_params
current_session_id = query_params.get("session")

if current_session_id and not st.session_state.user_email:
    user_data = get_session_from_file(current_session_id)
    if user_data:
        st.session_state.user_email = user_data["email"]
        st.session_state.token = user_data["token"]

# --- GOOGLE AUTH CONFIG (SAFE MODE) ---
# Yahan maine try-except lagaya hai taaki Localhost par crash na ho
try:
    CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
except Exception:
    # Agar Secrets nahi mile (Localhost), toh .env se uthao
    CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# --- SMART REDIRECT URI ---
try:
    REDIRECT_URI = st.secrets["REDIRECT_URI"]
except Exception:
    # Agar Secrets nahi mile (Localhost), toh Localhost use karo
    REDIRECT_URI = "http://localhost:8503"

# Google Endpoints
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USER_INFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

# --- SIDEBAR (Logout) ---
with st.sidebar:
    if st.session_state.user_email:
        st.write(f"👤 **{st.session_state.user_email}**")
        if st.button("🔒 Logout", type="primary"):
            if 'current_session_id' in locals() and current_session_id:
                logout_session(current_session_id)
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()

# --- MANUAL LOGIN FLOW ---
if not st.session_state.user_email:
    st.title("🤖 Jarvis AI - Secure Access")
    
    # ================= DEBUGGING BOX (START) =================
    # Ye box sirf tab dikhega jab zaroorat ho, Live par check karne ke liye
    if "localhost" not in REDIRECT_URI: 
        st.error("🛑 DEBUG MODE (LIVE)")
        st.code(f"REDIRECT_URI = {REDIRECT_URI}")
        st.info("Agar 403 aa raha hai, toh Google Cloud me 'Testing' mode on karo.")
    # =========================================================

    query_params = st.query_params
    auth_code = query_params.get("code")

    if auth_code:
        st.info("🔄 Connecting to Google... (Do not refresh)")
        try:
            payload = {
                "code": auth_code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            }
            token_response = requests.post(TOKEN_URL, data=payload)
            
            if token_response.status_code == 200:
                tokens = token_response.json()
                access_token = tokens["access_token"]
                user_info = requests.get(USER_INFO_URL, headers={"Authorization": f"Bearer {access_token}"}).json()
                email = user_info.get("email")
                
                if email:
                    st.session_state.user_email = email
                    st.session_state.token = tokens
                    new_session_id = str(uuid.uuid4())
                    save_session_to_file(new_session_id, {"email": email, "token": tokens})
                    st.query_params["session"] = new_session_id
                    st.rerun()
                else:
                    st.error("❌ Email nahi mila.")
            else:
                st.error("⚠️ Login Failed.")
                st.write("Google Error Response:", token_response.json())
                st.write(f"Code sent Redirect URI: `{REDIRECT_URI}`")
                st.stop()
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()
    else:
        auth_link = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=openid%20email%20profile&access_type=offline&prompt=consent"
        
        st.markdown(f'''
            <a href="{auth_link}" target="_self">
                <button style="
                    background-color: #4285F4; 
                    color: white; 
                    padding: 12px 24px; 
                    border: none; 
                    border-radius: 4px; 
                    font-size: 16px; 
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 10px;">
                    <img src="https://www.google.com/favicon.ico" width="20"/>
                    Login with Google
                </button>
            </a>
            ''', unsafe_allow_html=True)
            
    st.stop()

# =========================================================
# APP CONTENT (LOGGED IN USER ONLY)
# =========================================================

user_email = st.session_state.user_email
username = user_email 

with st.sidebar:
    st.markdown("---")
    st.title("🤖 Jarvis AI")
    
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_chat = f"Chat_{int(time.time())}.json"
        st.session_state.chat_history = [SystemMessage(content="You are Jarvis.")]
        st.rerun()

    st.subheader("📜 Your Chats")
    
    sessions = backend.get_all_chat_sessions(username)
    if not sessions:
        st.info("No chats yet.")
        
    for s in sessions:
        display_name = s.replace(".json", "")
        if "_" in display_name:
            parts = display_name.split("_")
            if parts[-1].isdigit(): display_name = " ".join(parts[:-1])
        
        col1, col2 = st.columns([0.80, 0.20])
        with col1:
            if st.button(display_name[:15], key=f"load_{s}", use_container_width=True):
                st.session_state.current_chat = s
                st.session_state.chat_history = backend.load_chat_session(username, s)
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{s}"):
                backend.delete_chat_session(username, s)
                st.rerun()

    st.markdown("---")
    provider = st.radio("Model:", ("Llama-3.3 (Fast) ⚡", "DeepSeek-R1 (Groq) 🧠"))
    
    # Safe API Key Load
    try:
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
        else:
            api_key = os.getenv("GROQ_API_KEY")
    except Exception:
        api_key = os.getenv("GROQ_API_KEY")

if "current_chat" not in st.session_state:
    st.session_state.current_chat = f"Chat_{int(time.time())}.json"
    st.session_state.chat_history = [SystemMessage(content="You are Jarvis.")]

st.title(f"Jarvis 🧠 | {user_email}")

for msg in st.session_state.chat_history:
    if not isinstance(msg, SystemMessage):
        with st.chat_message("user" if isinstance(msg, HumanMessage) else "assistant"):
            st.markdown(msg.content)

if prompt := st.chat_input("Ask Jarvis anything..."):
    st.session_state.chat_history.append(HumanMessage(content=prompt))
    with st.chat_message("user"): st.markdown(prompt)
    
    llm = backend.get_llm(provider, api_key)
    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                print("Invoking LLM with history:", st.session_state.chat_history)
                response = llm.invoke(st.session_state.chat_history)
                ai_msg = response.content
                st.markdown(ai_msg)
        
        st.session_state.chat_history.append(AIMessage(content=ai_msg))
        
        backend.save_chat_session(username, st.session_state.current_chat, st.session_state.chat_history)
        
        if "Chat_" in st.session_state.current_chat:
            new_name = backend.rename_chat_session(username, st.session_state.current_chat, prompt)
            st.session_state.current_chat = new_name
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")