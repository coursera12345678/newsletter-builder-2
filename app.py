import streamlit as st
import requests
from bs4 import BeautifulSoup
import os

# Load Groq API key
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-8b-8192"  # Working Groq model

def extract_article_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs)
        return text[:8000]  # limit to avoid token overflow
    except Exception as e:
        return f"⚠️ Error fetching article: {e}"

def get_groq_summary(text):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful newsletter assistant."},
            {"role": "user", "content": f"Summarize this article like it's a newsletter section. Make it clear and engaging: {text}"}
        ]
    }
    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Error generating summary: {e}"

# Streamlit UI
st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")
st.write("Paste article URLs below (one per line), then click Summarize.")

urls_input = st.text_area("Article URLs", height=200)
if st.button("Summarize"):
    urls = urls_input.strip().split("\n")
    st.subheader("📄 Newsletter Summaries")
    for i, url in enumerate(urls, start=1):
        st.write(f"🔍 Fetching: {url}")
        article_text = extract_article_text(url)
        st.write("✍️ Summarizing...")
        summary = get_groq_summary(article_text)
        st.markdown(f"### Article {i}\n{summary}")
