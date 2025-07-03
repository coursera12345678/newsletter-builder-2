import streamlit as st
import requests
from bs4 import BeautifulSoup

# Load API key from Streamlit secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Set page config
st.set_page_config(page_title="📰 Auto Newsletter Generator (Groq + Streamlit)")

st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")
st.write("Paste article URLs below (one per line), then click Summarize.")

# Input URLs
url_input = st.text_area("Article URLs", height=200)
urls = [url.strip() for url in url_input.split("\n") if url.strip()]

# Helper: extract article text using BeautifulSoup
def extract_text_bs4(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        # Try to get <article> content, fallback to all <p>
        article_tag = soup.find("article")
        if article_tag:
            paragraphs = article_tag.find_all("p")
        else:
            paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs)
        return text[:5000]  # trim to prevent token overflow
    except Exception as e:
        return f"Error fetching article: {e}"

# Helper: summarize using Groq API
def summarize_with_groq(text, style="main"):
    if style == "main":
        prompt = "Summarize this article as a **main newsletter story**. Include a title and a bold intro paragraph."
    elif style == "sub":
        prompt = "Summarize this article as a **sub-story** for a newsletter. Be brief but engaging."
    elif style == "quick":
        prompt = "Give a short 1-sentence news summary and the article title."
    elif style == "recommended":
        prompt = "Give a catchy headline and a short teaser to recommend this article."
    else:
        prompt = "Summarize this article for a newsletter."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-70b-8192",  # updated model
        "messages": [
            {"role": "system", "content": "You are a helpful newsletter assistant."},
            {"role": "user", "content": f"{prompt}\n\n{text}"}
        ]
    }

    try:
        res = requests.post(GROQ_URL, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Error generating summary: {e}"

# Main action
if st.button("Summarize") and urls:
    st.markdown("## 📄 Newsletter Summaries")
    summaries = []

    for idx, url in enumerate(urls):
        st.markdown(f"🔍 **Fetching:** {url}")
        with st.spinner("✍️ Summarizing..."):
            raw_text = extract_text_bs4(url)
            if not raw_text or raw_text.startswith("Error"):
                summaries.append((url, "⚠️ Failed to fetch content.", "quick"))
                continue

            if idx == 0:
                summary = summarize_with_groq(raw_text, style="main")
                summaries.append((url, summary, "main"))
            elif idx == 1:
                summary = summarize_with_groq(raw_text, style="sub")
                summaries.append((url, summary, "sub"))
            else:
                quick = summarize_with_groq(raw_text, style="quick")
                summaries.append((url, quick, "quick"))

    # Render HTML email preview
    st.markdown("---")
    st.markdown("### ✨ Newsletter Preview (HTML):")

    html = """<div style="font-family:Arial,sans-serif; max-width:600px; margin:auto;">"""
    for url, summary, style in summaries:
        if style == "main":
            html += f"<h2>{summary.splitlines()[0]}</h2>"
            html += f"<p>{''.join(summary.splitlines()[1:])}</p>"
        elif style == "sub":
            html += f'<div class="subheadline">Other Top Stories</div><p>{summary}</p>'
        elif style == "quick":
            html += f'<li><a href="{url}" target="_blank">{summary}</a></li>'
    html += """<div class="subheadline">Quick Reads</div><ul>"""
    for url, summary, style in summaries:
        if style == "quick":
            html += f'<li><a href="{url}" target="_blank">{summary}</a></li>'
    html += "</ul></div>"

    st.markdown(html, unsafe_allow_html=True)
