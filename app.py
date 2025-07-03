import streamlit as st
import requests

st.title("Groq API Key Test")

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "model": "mixtral-8x7b-32768",
    "messages": [
        {"role": "user", "content": "Say hi"}
    ]
}

try:
    res = requests.post(GROQ_URL, headers=headers, json=payload)
    res.raise_for_status()
    st.success(res.json()["choices"][0]["message"]["content"])
except Exception as e:
    st.error(f"❌ API failed: {e}")
