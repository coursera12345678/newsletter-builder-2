import streamlit as st
import requests
from bs4 import BeautifulSoup

# Gemini API settings
API_KEY = st.secrets["GEMINI_API_KEY"]
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={API_KEY}"

def get_article_text(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all('p')
        text = ' '.join(p.get_text() for p in paragraphs)
        return text[:2000]  # Limit to avoid API token issues
    except Exception as e:
        return None

def get_gemini_summary(text):
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"Summarize this article like a newsletter section. Make it clear, engaging, and concise:\n\n{text}"
                    }
                ]
            }
        ]
    }
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"⚠️ Error generating summary: {e}"

def main():
    st.title("📰 Auto Newsletter Generator (Gemini + Streamlit)")
    st.write("Paste article URLs below (one per line), then click Summarize.")

    urls_text = st.text_area("Article URLs", height=150)

    if st.button("Summarize"):
        urls = [url.strip() for url in urls_text.split("\n") if url.strip()]
        if not urls:
            st.error("Please enter at least one valid URL.")
            return

        summaries = []
        for url in urls:
            st.write(f"🔍 Fetching: {url}")
            article = get_article_text(url)
            if not article:
                summaries.append(f"⚠️ Failed to fetch article: {url}")
                continue

            st.write("✍️ Summarizing...")
            summary = get_gemini_summary(article)
            summaries.append(summary)

        st.header("📄 Newsletter Summaries")
        for i, s in enumerate(summaries, 1):
            st.subheader(f"Article {i}")
            st.write(s)

if __name__ == "__main__":
    main()
