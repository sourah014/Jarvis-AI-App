import os
import json
from langchain_groq import ChatGroq

# --- LLM INITIALIZATION ---
def get_llm(provider, api_key):
    # Agar API Key function call mein nahi aayi, toh environment se uthao
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")

    if "DeepSeek" in provider:
        # NOTE: Groq ne DeepSeek-R1 ko hata diya hai.
        # Hum iski jagah 'llama-3.3-70b-versatile' use kar rahe hain
        # jo abhi Groq par sabse smart model hai.
        return ChatGroq(
            model="llama-3.3-70b-versatile", 
            api_key=api_key, 
            temperature=0.6 # Thoda creative for "Reasoning" feel
        )
    else:
        # Llama 3.3 (Fast mode)
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=api_key,
            temperature=0.7
        )

# --- FILE OPERATIONS (Baki sab same hai) ---

def save_chat_session(username, filename, messages):
    user_folder = os.path.join("all_chats", username)
    os.makedirs(user_folder, exist_ok=True)
    filepath = os.path.join(user_folder, filename)
    
    data = []
    for msg in messages:
        role = "user"
        if msg.type == "ai": role = "assistant"
        elif msg.type == "system": role = "system"
        data.append({"role": role, "content": msg.content})
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def load_chat_session(username, filename):
    filepath = os.path.join("all_chats", username, filename)
    if not os.path.exists(filepath):
        return []

    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    with open(filepath, "r") as f:
        data = json.load(f)
        
    messages = []
    for msg in data:
        if msg["role"] == "user": messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant": messages.append(AIMessage(content=msg["content"]))
        elif msg["role"] == "system": messages.append(SystemMessage(content=msg["content"]))
    return messages

def get_all_chat_sessions(username):
    user_folder = os.path.join("all_chats", username)
    if not os.path.exists(user_folder):
        return []
    files = [f for f in os.listdir(user_folder) if f.endswith(".json")]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(user_folder, x)), reverse=True)
    return files

def delete_chat_session(username, filename):
    filepath = os.path.join("all_chats", username, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

def rename_chat_session(username, filename, first_message):
    user_folder = os.path.join("all_chats", username)
    new_title = " ".join(first_message.split()[:5])
    safe_title = "".join([c for c in new_title if c.isalnum() or c in (' ', '-', '_')]).strip().replace(" ", "_")
    new_filename = f"{safe_title}.json"
    old_path = os.path.join(user_folder, filename)
    new_path = os.path.join(user_folder, new_filename)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        return new_filename
    return filename