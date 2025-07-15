import streamlit as st
from pydantic import BaseModel
from typing import List, Dict
import requests
# from dotenv import load_dotenv
import os
import random
# import streamlit as st

# groq_api_key = st.secrets["GROQ_API_KEY"
# Load environment variables
# load_dotenv()

# --- FastAPI logic merged ---
# Global in-memory history store
message_history: List[Dict[str, str]] = []

class ChatRequest(BaseModel):
    message: str
    topic: str  # e.g., 'Science', 'Math', etc.

class ChatResponse(BaseModel):
    response: str

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
import streamlit as st

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "ilaama-3.3-70b-versatile"

def chat_with_groq(req: ChatRequest) -> Dict[str, str]:
    """
    Append to global history, build full context, send to Groq, update history, and return reply.
    """
    # Construct system prompt based on selected topic
    system_prompt = (
        f"You are an expert {req.topic.lower()} tutor. "
        f"Answer user queries with deep knowledge, clear explanations, and examples in the field of {req.topic}."
    )
    # Append user message
    message_history.append({"role": "user", "content": req.message})
    # Build payload messages
    messages = [{"role": "system", "content": system_prompt}] + message_history
    payload = {"model": GROQ_MODEL, "messages": messages}
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    res = requests.post(GROQ_API_URL, headers=headers, json=payload)
    if res.status_code != 200:
        return {"response": "⚠️ LLM request failed"}
    reply = res.json()["choices"][0]["message"]["content"]
    message_history.append({"role": "assistant", "content": reply})
    return {"response": reply}


def clear_history() -> None:
    """
    Clear the global message history by reinitializing the list.
    """
    global message_history
    message_history = []  # reinitialize history

# --- Streamlit interface ---
# 🎨 Streamlit page config
st.set_page_config(page_title="🤖 Bala's Chatbot", layout="wide")

# ---- Sidebar ----
st.sidebar.title("Settings")

topics = ["General", "Math", "Science", "Java", "Python", "History"]
selected_topic = st.sidebar.selectbox("Select Subject Topic:", topics)
custom_topic = st.sidebar.text_input("Or enter a custom topic:")
effective_topic = custom_topic.strip() or selected_topic

# Reset chat: clear server & local history
if st.sidebar.button("🔄 Reset Chat"):
    # Clear backend history
    clear_history()
    # Clear frontend history
    for key in ["messages", "tip_shown"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# Tip of the Day
tips = [
    "Practice coding every day for at least 30 minutes.",
    "Review your notes right before sleeping for better retention.",
    "Teach someone else a concept to strengthen your understanding.",
    "Use flashcards for quick revision sessions.",
    "Break study sessions into focused intervals with breaks."
]
if "tip_shown" not in st.session_state:
    st.session_state.tip_shown = True
    st.sidebar.info(f"💡 Tip of the Day:\n{random.choice(tips)}")

# ---- Main Chat ----
st.markdown("<h1 style='text-align: center;'>🤖 Study Buddy Chatbot</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input(f"Ask me anything about {effective_topic}...")

if user_input:
    st.session_state.messages.append({"role": "user", "text": user_input})
    # Call merged backend logic directly
    req = ChatRequest(message=user_input, topic=effective_topic)
    with st.spinner("Study Buddy is typing..."):
        try:
            result = chat_with_groq(req)
            bot_reply = result.get("response", "I need to learn more about that.")
        except Exception as e:
            bot_reply = f"⚠️ Request error: {e}"
    st.session_state.messages.append({"role": "assistant", "text": bot_reply})

for msg in st.session_state.messages:
    role = msg.get("role") if msg.get("role") in ["user", "assistant"] else "assistant"
    with st.chat_message(role):
        st.markdown(msg.get("text"))
