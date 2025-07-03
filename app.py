import streamlit as st
import requests
from bs4 import BeautifulSoup

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_article_text(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        return " ".join(p.get_text() for p in paragraphs)[:2000]
    except Exception:
        return None

def get_groq_summary(text):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mixtral-8x7b-32768",
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

def main():
    st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")
    st.write("Paste article URLs below (one per line), then click **Summarize**.")

    urls_text = st.text_area("Article URLs", height=150)

    if st.button("Summarize"):
        urls = [url.strip() for url in urls_text.split("\n") if url.strip()]
        if not urls:
            st.error("Please enter at least one URL.")
            return

        st.header("📄 Newsletter Summaries")
        for i, url in enumerate(urls, start=1):
            st.write(f"🔍 Fetching: {url}")
            article_text = get_article_text(url)
            if not article_text:
                st.warning("⚠️ Could not fetch article text.")
                continue

            st.write("✍️ Summarizing...")
            summary = get_groq_summary(article_text)
            st.subheader(f"Article {i}")
            st.write(summary)

if __name__ == "__main__":
    main()
