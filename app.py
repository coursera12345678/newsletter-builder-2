import streamlit as st
import requests

st.set_page_config(page_title="Groq API Key Debugger")
st.title("✅ Groq API Key Test")

# Step 1: Read the API key
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    st.success("✅ API key loaded successfully.")
except Exception as e:
    st.error(f"❌ Could not load API key: {e}")
    st.stop()

# Step 2: Prepare the API call
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "model": "llama3-70b-8192",
    "messages": [
        {"role": "user", "content": "Say hi"}
    ]
}

# Step 3: Make the API call
if st.button("🔁 Test Groq API"):
    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        st.success("✅ Response received from Groq:")
        st.code(content)
    except Exception as e:
        st.error(f"❌ API request failed: {e}")
        st.json(response.json() if response.content else {"error": "No content"})
