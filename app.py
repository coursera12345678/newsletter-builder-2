import streamlit as st
import requests
from bs4 import BeautifulSoup

# Load Groq API key from secrets
API_KEY = st.secrets["GROQ_API_KEY"]
API_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def get_article_text(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all('p')
        text = ' '.join(p.get_text() for p in paragraphs)
        return text[:2000]  # truncate to 2000 chars
    except Exception:
        return None

def get_groq_summary(article_text):
    payload = {
        "model": "mixtral-8x7b-32768",  # Groq's fast Mixtral model
        "messages": [
            {
                "role": "user",
                "content": f"Summarize this article in 3–4 lines like it's a newsletter. Make it crisp, clear, and engaging:\n\n{article_text}"
            }
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Error generating summary: {e}"

def main():
    st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")
    st.write("Paste article URLs below (one per line), then click **Summarize**.")

    urls_input = st.text_area("Article URLs", height=150)

    if st.button("Summarize"):
        if not urls_input.strip():
            st.error("Please enter at least one URL.")
            return

        urls = [url.strip() for url in urls_input.splitlines() if url.strip()]
        summaries = []

        for url in urls:
            st.write(f"🔍 Fetching: {url}")
            article = get_article_text(url)
            if not article:
                st.warning(f"⚠️ Could not fetch or parse: {url}")
                summaries.append("⚠️ Failed to fetch content.")
                continue

            st.write("✍️ Summarizing...")
            summary = get_groq_summary(article)
            summaries.append(summary)

        st.header("📄 Newsletter Summaries")
        for i, summary in enumerate(summaries, start=1):
            st.subheader(f"Article {i}")
            st.write(summary)

if __name__ == "__main__":
    main()
