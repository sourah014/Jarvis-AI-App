import streamlit as st
import os
import time
import json
import base64
import requests  # <-- Hum ab khud request bhejenge
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import backend 
import uuid

# 1. Env Load
load_dotenv()
# --- SESSION PERSISTENCE LOGIC (Refresh Fix) ---
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

# --- MAINTENANCE MODE ---
if os.getenv("MAINTENANCE_MODE", "False").lower() == "true":
    st.title("🚧 App under Maintenance")
    st.stop()

# Page Setup
st.set_page_config(page_title="Jarvis Pro", page_icon="🤖", layout="wide")

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

# --- GOOGLE AUTH CONFIG (Manual Mode) ---
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# REDIRECT_URI = "http://localhost:8503"  # <--- Check your Browser URL! Agar 8501 hai toh yahan change karo.
# --- SMART REDIRECT URI (Auto-Detect) ---
# Agar Streamlit Cloud par "Secrets" set hain, toh wahan se URL lega.
# Agar nahi, toh Localhost manega.
try:
    if "REDIRECT_URI" in st.secrets:
        REDIRECT_URI = st.secrets["REDIRECT_URI"]
    else:
        REDIRECT_URI = "http://localhost:8503"
except FileNotFoundError:
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
    
    # 1. Check: Kya URL mein 'code' aaya hai? (Matlab Google se wapas aaye ho?)
    query_params = st.query_params
    auth_code = query_params.get("code")

    if auth_code:
        st.info("🔄 Connecting to Google... (Do not refresh)")
        
        # 2. Token Exchange (Manual Request)
        try:
            payload = {
                "code": auth_code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            }
            
            # Seedha Google ko POST request bhejo
            token_response = requests.post(TOKEN_URL, data=payload)
            
            if token_response.status_code == 200:
                # Success! Token mil gaya
                tokens = token_response.json()
                access_token = tokens["access_token"]
                
                # 3. User Info Nikalo
                user_info = requests.get(
                    USER_INFO_URL, 
                    headers={"Authorization": f"Bearer {access_token}"}
                ).json()
                
                email = user_info.get("email")
                
                if email:
                    # Login Complete!
                    st.session_state.user_email = email
                    st.session_state.token = tokens
                    new_session_id = str(uuid.uuid4())
                    save_session_to_file(new_session_id, {"email": email, "token": tokens})
                    st.query_params["session"] = new_session_id
                    # # URL saaf karo taaki code reuse na ho
                    # st.query_params.clear()
                    st.rerun()
                
                else:
                    st.error("❌ Email nahi mila. Try again.")
            else:
                # Agar Google ne mana kiya (e.g. URI Mismatch)
                error_details = token_response.json()
                st.error(f"⚠️ Google Error: {error_details.get('error_description')}")
                st.write(f"Check REDIRECT_URI config. Code expects: `{REDIRECT_URI}`")
                st.stop()
                
        except Exception as e:
            st.error(f"Connection Error: {e}")
            st.stop()
            
    else:
        # 3. Agar 'code' nahi hai, toh Login Link dikhao
        # Hum button ki jagah Link use karenge taaki koi script na atke
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
# APP CONTENT (SIRF LOGGED IN USER KE LIYE)
# =========================================================

user_email = st.session_state.user_email
username = user_email 

# Sidebar Features
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
    api_key = os.getenv("GROQ_API_KEY")

# Chat Interface
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