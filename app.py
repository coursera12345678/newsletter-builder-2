import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Groq API Setup
groq_api_key = st.secrets["GROQ_API_KEY"]
groq_model = "llama3-70b-8192"
groq_url = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {groq_api_key}",
    "Content-Type": "application/json"
}

# Functions

def fetch_article_content(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        title_tag = soup.find('meta', property='og:title')
        title = title_tag['content'] if title_tag else soup.title.string.strip()

        image_tag = soup.find('meta', property='og:image')
        image_url = image_tag['content'] if image_tag else ""

        paragraphs = soup.find_all('p')
        content = " ".join(p.get_text() for p in paragraphs if p.get_text())

        links = [
            (a.get_text(strip=True), urljoin(url, a['href']))
            for a in soup.find_all('a', href=True)
            if a.get_text(strip=True) and a['href'].startswith("http")
        ]

        return title, image_url, content, links
    except Exception as e:
        st.warning(f"Failed to process {url}: {e}")
        return None, None, None, []

def generate_summary(text):
    try:
        payload = {
            "model": groq_model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Summarize this article clearly and concisely. Keep it under 6 sentences.\n{text}"}
            ]
        }
        res = requests.post(groq_url, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        st.warning(f"Failed to generate summary: {e}")
        return "Summary not available."

# Streamlit App
st.title("\U0001F4F0 Auto Newsletter Generator (Groq + Streamlit)")
st.markdown("Paste article URLs below (one per line), then click **Generate Newsletter**.")

urls_input = st.text_area("Article URLs", height=150)
generate = st.button("Generate Newsletter")

if generate:
    urls = [url.strip() for url in urls_input.strip().split("\n") if url.strip()]

    st.markdown("### :sparkles: Newsletter Preview:")
    st.markdown("<div style='font-family:sans-serif; max-width:700px; margin:auto;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;'>Weekly Tech Digest</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='border-top:3px solid #ccc;'>", unsafe_allow_html=True)

    for url in urls:
        title, image_url, content, links = fetch_article_content(url)
        if not title:
            continue

        summary = generate_summary(content[:3000])  # LLM input limit safeguard

        st.markdown(f"<h2>{title}</h2>", unsafe_allow_html=True)

        if image_url:
            st.markdown(f"<img src='{image_url}' style='width:100%; border-radius:10px;'>", unsafe_allow_html=True)

        st.markdown(f"<p>{summary}</p>", unsafe_allow_html=True)

        st.markdown(f"<a href='{url}' target='_blank' style='color:#007BFF;'>Continue Reading</a>", unsafe_allow_html=True)

        # Quick Reads section
        if links:
            st.markdown("<h4 style='margin-top:1.5rem;'>Quick Reads from this article:</h4><ul>", unsafe_allow_html=True)
            for text, link in links[:5]:
                st.markdown(f"<li><a href='{link}' target='_blank'>{text}</a></li>", unsafe_allow_html=True)
            st.markdown("</ul>", unsafe_allow_html=True)

        # Section break
        st.markdown("""
            <div style='margin:2rem 0; height:3px; background-color:#f0f0f0;'></div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
