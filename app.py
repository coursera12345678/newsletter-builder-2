import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json

# Groq API config
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# Helper to fetch and clean article content
def fetch_article(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("title").text.strip()
        text_blocks = soup.find_all(["p"])
        text = " ".join([p.text for p in text_blocks])
        text = re.sub(r'\s+', ' ', text)
        image_tag = soup.find("meta", property="og:image")
        image_url = image_tag["content"] if image_tag else ""
        return title, text[:4000], image_url
    except Exception as e:
        return None, None, None

# LLM summarizer
def summarize_article(title, text):
    prompt = f"""Summarize this article in 3 crisp sentences:
Title: {title}
Text: {text}

Extract 3 quick reads and 3 recommended reads (if available). Provide clean markdown-like output with sections:
1. Summary
2. Quick Reads
3. Recommended Reads
Do not include any intro or outro text."""
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    res = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
    return res.json()["choices"][0]["message"]["content"]

# Renderer
def render_newsletter(sections):
    st.markdown("""
        <style>
        .newsletter {font-family:sans-serif; max-width:700px; margin:auto; padding:20px; line-height:1.6;}
        .newsletter h1 {text-align:center; font-size:2em; margin-bottom:1em;}
        .newsletter h2 {margin-top:2em; font-size:1.4em;}
        .newsletter img {width:100%; border-radius:12px; margin:1em 0;}
        .newsletter a {color:#007BFF; text-decoration:none;}
        .newsletter hr {margin:2em 0;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='newsletter'>", unsafe_allow_html=True)
    st.markdown("<h1>Weekly Tech Digest</h1>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    for sec in sections:
        st.markdown(f"<h2>{sec['title']}</h2>", unsafe_allow_html=True)
        if sec['image']:
            st.markdown(f"<img src='{sec['image']}' alt='image'>", unsafe_allow_html=True)
        st.markdown(f"<p>{sec['summary']}</p>", unsafe_allow_html=True)
        st.markdown(f"<a href='{sec['url']}' target='_blank'>Continue Reading</a>", unsafe_allow_html=True)
        if sec['quick_reads']:
            st.markdown("<h3>Quick Reads</h3><ul>" + ''.join([f"<li><a href='{qr}' target='_blank'>{qr}</a></li>" for qr in sec['quick_reads']]) + "</ul>", unsafe_allow_html=True)
        if sec['recommended']:
            st.markdown("<h3>Recommended Reads</h3><ul>" + ''.join([f"<li><a href='{rr}' target='_blank'>{rr}</a></li>" for rr in sec['recommended']]) + "</ul>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Streamlit UI
st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")
st.write("Paste article URLs below (one per line), then click Generate.")

urls_input = st.text_area("Article URLs", height=200)
if st.button("Generate Newsletter"):
    urls = [u.strip() for u in urls_input.strip().split("\n") if u.strip()]
    output_sections = []
    for url in urls:
        st.write(f"🔍 Fetching: {url}")
        title, text, image = fetch_article(url)
        if not title or not text:
            st.warning(f"Could not process {url}")
            continue
        summary_data = summarize_article(title, text)

        # Parse LLM output (basic regex fallback)
        summary = re.search(r"Summary\s*[:\-\n]+(.*?)\n(?:Quick Reads|$)", summary_data, re.S)
        quick = re.findall(r"Quick Reads\s*[:\-\n]+(.*?)\n(?:Recommended Reads|$)", summary_data, re.S)
        recs = re.findall(r"Recommended Reads\s*[:\-\n]+(.*?)$", summary_data, re.S)

        quick_links = re.findall(r"https?://\S+", quick[0]) if quick else []
        rec_links = re.findall(r"https?://\S+", recs[0]) if recs else []

        output_sections.append({
            "title": title,
            "url": url,
            "image": image,
            "summary": summary.group(1).strip() if summary else "",
            "quick_reads": quick_links,
            "recommended": rec_links
        })

    render_newsletter(output_sections)
