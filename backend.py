import os
import json
import time
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# --- CONFIGURATION ---
CHATS_DIR = "all_chats"  # Wo folder jahan saari chats save hongi
if not os.path.exists(CHATS_DIR):
    os.makedirs(CHATS_DIR) # Agar folder nahi hai toh bana do

# --- FUNCTIONS ---

def get_all_chat_sessions():
    """Saari saved JSON files ki list laata hai, latest waali sabse upar"""
    if not os.path.exists(CHATS_DIR):
        return []
    files = [f for f in os.listdir(CHATS_DIR) if f.endswith(".json")]
    # File ki timing check karke sort karta hai (Newest First)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(CHATS_DIR, x)), reverse=True)
    return files

def load_chat_session(filename):
    """Specific chat file ko kholkar uske messages ko LangChain format mein badalta hai"""
    path = os.path.join(CHATS_DIR, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            messages = []
            for msg in data:
                # Type ke hisaab se message object banana
                if msg["type"] == "system":
                    messages.append(SystemMessage(content=msg["content"]))
                elif msg["type"] == "human":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["type"] == "ai":
                    messages.append(AIMessage(content=msg["content"]))
            return messages
    return None

def save_chat_session(filename, history):
    """Current chat history ko JSON format mein save karta hai"""
    path = os.path.join(CHATS_DIR, filename)
    data = []
    for msg in history:
        # Objects ko text format mein badalna taaki JSON mein save ho sake
        m_type = "system" if isinstance(msg, SystemMessage) else "human" if isinstance(msg, HumanMessage) else "ai"
        data.append({"type": m_type, "content": msg.content})
    
    with open(path, "w") as f:
        json.dump(data, f)

def get_llm(provider, api_key):
    """User ki choice ke hisaab se Groq AI model initialize karta hai"""
    if provider == "DeepSeek-R1 (Logic) 🧠":
        return ChatGroq(groq_api_key=api_key, model_name="llama-3.3-70b-versatile")
    elif provider == "Llama-3.3 (Fast) ⚡":
        return ChatGroq(groq_api_key=api_key, model_name="llama-3.1-8b-instant")
    return None

def rename_chat_session(old_filename, first_message):
    """Pehle user message se title banakar file rename karta hai"""
    # Sirf letters/space rakho, faltu symbols hata do
    clean_title = "".join(e for e in first_message[:25] if e.isalnum() or e.isspace())
    clean_title = clean_title.strip().replace(" ", "_")
    
    # Naya naam: Topic_Timestamp.json
    new_name = f"{clean_title}_{int(time.time())}.json"
    
    old_path = os.path.join(CHATS_DIR, old_filename)
    new_path = os.path.join(CHATS_DIR, new_name)
    
    if os.path.exists(old_path):
        os.rename(old_path, new_path) # File ka naam badalna
        return new_name
    return old_filename

def delete_chat_session(filename):
    """Specific chat file ko permanently delete karta hai"""
    path = os.path.join(CHATS_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False