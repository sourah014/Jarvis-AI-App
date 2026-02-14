import os
import json
import time
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI # Naya import DeepSeek ke liye
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# --- CONFIGURATION ---
CHATS_DIR = "all_chats"
if not os.path.exists(CHATS_DIR):
    os.makedirs(CHATS_DIR)

# --- FUNCTIONS ---

def get_all_chat_sessions():
    if not os.path.exists(CHATS_DIR):
        return []
    files = [f for f in os.listdir(CHATS_DIR) if f.endswith(".json")]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(CHATS_DIR, x)), reverse=True)
    return files

def load_chat_session(filename):
    path = os.path.join(CHATS_DIR, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            messages = []
            for msg in data:
                if msg["type"] == "system":
                    messages.append(SystemMessage(content=msg["content"]))
                elif msg["type"] == "human":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["type"] == "ai":
                    messages.append(AIMessage(content=msg["content"]))
            return messages
    return None

def save_chat_session(filename, history):
    path = os.path.join(CHATS_DIR, filename)
    data = []
    for msg in history:
        m_type = "system" if isinstance(msg, SystemMessage) else "human" if isinstance(msg, HumanMessage) else "ai"
        data.append({"type": m_type, "content": msg.content})
    with open(path, "w") as f:
        json.dump(data, f)

# --- UPDATE: AB DEEPSEEK DIRECT CHALEGA ---
def get_llm(provider, api_key):
    """DeepSeek ke liye OpenAI library aur Groq ke liye Groq library use hogi"""
    if provider == "DeepSeek-R1 (Logic) 🧠":
        # DeepSeek ki official API key .env se uthayega
        ds_api_key = os.getenv("DEEPSEEK_API_KEY") 
        return ChatOpenAI(
            model='deepseek-reasoner', 
            openai_api_key=ds_api_key, 
            openai_api_base='https://api.deepseek.com',
            max_tokens=2048
        )
    elif provider == "Llama-3.3 (Fast) ⚡":
        # Groq waali API key use hogi
        return ChatGroq(groq_api_key=api_key, model_name="llama-3.3-70b-versatile")
    return None

def rename_chat_session(old_filename, first_message):
    clean_title = "".join(e for e in first_message[:25] if e.isalnum() or e.isspace())
    clean_title = clean_title.strip().replace(" ", "_")
    new_name = f"{clean_title}_{int(time.time())}.json"
    old_path = os.path.join(CHATS_DIR, old_filename)
    new_path = os.path.join(CHATS_DIR, new_name)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        return new_name
    return old_filename

def delete_chat_session(filename):
    path = os.path.join(CHATS_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False