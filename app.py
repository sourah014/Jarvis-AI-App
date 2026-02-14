import streamlit as st
import os
import time
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import backend # Hamara logic file

load_dotenv()

# --- MAINTENANCE MODE CHECK ---
# Environment variable se check karega ki app maintenance mein hai ya nahi
is_maintenance = os.getenv("MAINTENANCE_MODE", "False").lower() == "true"

if is_maintenance:
    st.title("🚧 App under Maintenance")
    st.subheader("Bhai, hum kuch naya update kar rahe hain!")
    st.info("Jarvis thodi der mein wapas aayega. Tab tak chai pi lo! ☕")
    st.stop() # Ye niche ka saara code block kar dega

# Page setting
st.set_page_config(page_title="Jarvis Pro", page_icon="🤖", layout="wide")

# --- SIDEBAR: NEW CHAT & HISTORY ---
with st.sidebar:
    st.title("🤖 Jarvis AI")
    
    # Nayi Chat shuru karne ka button
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_chat = f"Chat_{int(time.time())}.json"
        st.session_state.chat_history = [SystemMessage(content="You are Jarvis, a helpful AI.")]
        st.rerun()

    st.markdown("---")
    st.subheader("📜 Recent Chats")
    
    # Saari purani chats ki list
    sessions = backend.get_all_chat_sessions()
    
    for s in sessions:
        # Display name ko saaf karna (Numbers hatao)
        display_name = s.replace(".json", "")
        if "_" in display_name:
            parts = display_name.split("_")
            if parts[-1].isdigit():
                display_name = " ".join(parts[:-1])
            else:
                display_name = display_name.replace("_", " ")
        else:
            display_name = display_name.replace("_", " ")

        if len(display_name) > 20:
            display_name = display_name[:18] + "..."

        # --- DELETE LOGIC STARTS HERE ---
        # Do columns banaye: ek chat load ke liye, ek delete ke liye
        col1, col2 = st.columns([0.85, 0.15])
        
        with col1:
            # Chat load karne ka button
            if st.button(display_name, key=f"load_{s}", use_container_width=True):
                st.session_state.current_chat = s
                st.session_state.chat_history = backend.load_chat_session(s)
                st.rerun()
        
        with col2:
            # Delete karne ka button (Chhota 🗑️ icon)
            if st.button("🗑️", key=f"del_{s}", help="Delete this chat"):
                backend.delete_chat_session(s)
                # Agar wahi chat delete ki jo khuli hui hai, toh reset kar do
                if st.session_state.get('current_chat') == s:
                    st.session_state.current_chat = f"Chat_{int(time.time())}.json"
                    st.session_state.chat_history = [SystemMessage(content="You are Jarvis.")]
                st.rerun()
        # --------------------------------

    st.markdown("---")
    provider = st.radio("Model:", ("DeepSeek-R1 (Logic) 🧠", "Llama-3.3 (Fast) ⚡"))
    api_key = os.getenv("GROQ_API_KEY")

# --- MAIN CHAT LOGIC ---

if "current_chat" not in st.session_state:
    st.session_state.current_chat = f"Chat_{int(time.time())}.json"
    st.session_state.chat_history = [SystemMessage(content="You are Jarvis, a helpful AI.")]

st.title(f"Jarvis AI - {provider}")

# History dikhao
for message in st.session_state.chat_history:
    if not isinstance(message, SystemMessage):
        role = "user" if isinstance(message, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(message.content)

# User Input
user_input = st.chat_input("Ask Jarvis anything...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append(HumanMessage(content=user_input))
    
    llm = backend.get_llm(provider, api_key)
    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = llm.invoke(st.session_state.chat_history)
                ai_msg = response.content
                st.markdown(ai_msg)
        
        st.session_state.chat_history.append(AIMessage(content=ai_msg))

        # Smart Rename Logic
        if "Chat_" in st.session_state.current_chat:
            backend.save_chat_session(st.session_state.current_chat, st.session_state.chat_history)
            new_name = backend.rename_chat_session(st.session_state.current_chat, user_input)
            st.session_state.current_chat = new_name
        else:
            backend.save_chat_session(st.session_state.current_chat, st.session_state.chat_history)
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Error: {e}")