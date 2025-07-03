import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
import re

st.set_page_config(page_title="📰 Auto Newsletter Generator")
st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")
st.write("Paste article URLs below (one per line), then click Summarize.")

# Input box
urls_input = st.text_area("Article URLs", height=200)

# API Key
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

def extract_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")

        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs)
        title_tag = soup.find("title")
        title = title_tag.get_text().strip() if title_tag else "Untitled"
        return title, text.strip()
    except:
        return None, None

def extract_image(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image["content"]:
            return og_image["content"]
    except:
        pass
    return None

def summarize_with_groq(content, style):
    if style == "main":
        prompt = "Write a bold headline and 3-line intro for a newsletter's main story."
    elif style == "sub":
        prompt = "Write a short 2-3 line summary of this article for the 'Other Top Stories' section."
    elif style == "quick":
        prompt = "Give a short one-line news summary."
    elif style == "recommended":
        prompt = "Write a teaser line recommending this article to curious readers."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [
            {"role": "system", "content": "You are a helpful newsletter editor."},
            {"role": "user", "content": prompt + "\n\n" + content}
        ],
        "model": "mixtral-8x7b-32768"
    }
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
    return res.json()["choices"][0]["message"]["content"].strip()

if st.button("Summarize"):
    urls = [url.strip() for url in urls_input.splitlines() if url.strip()]

    main_story = {}
    other_stories = []
    quick_reads = []
    recommended_reads = []

    for i, url in enumerate(urls):
        st.write(f"\U0001F50D Fetching: {url}")
        title, text = extract_text(url)
        image = extract_image(url)
        if not text:
            continue

        if i == 0:
            summary = summarize_with_groq(text, "main")
            main_story = {"title": title, "summary": summary, "image": image, "url": url}
        elif i == 1:
            summary = summarize_with_groq(text, "sub")
            other_stories.append({"title": title, "summary": summary, "url": url})
        else:
            quick = summarize_with_groq(text, "quick")
            rec = summarize_with_groq(text, "recommended")
            quick_reads.append({"title": title, "summary": quick, "url": url})
            recommended_reads.append({"summary": rec, "url": url})

    # Construct HTML output
    html = '<div style="font-family:sans-serif; max-width:600px; margin:auto;">
'
    
    if main_story:
        html += f"<h1>{main_story['title']}</h1>"
        if main_story.get("image"):
            html += f'<img src="{main_story['image']}" alt="Main image" style="width:100%; border-radius:8px; margin:10px 0;" />'
        html += f"<p>{main_story['summary']}</p>"

    if other_stories:
        html += "<h3>Other Top Stories</h3>"
        for story in other_stories:
            html += f"<p><strong>{story['title']}</strong><br>{story['summary']}</p>"

    if quick_reads:
        html += "<h3>Quick Reads</h3><ul>"
        for qr in quick_reads:
            html += f'<li><a href="{qr["url"]}">{qr["title"]}</a> — {qr["summary"]}</li>'
        html += "</ul>"

    if recommended_reads:
        html += "<h3>Recommended Reads</h3><ul>"
        for rec in recommended_reads:
            html += f'<li><a href="{rec["url"]}">{rec["summary"]}</a></li>'
        html += "</ul>"

    html += "</div>"
    
    st.markdown("""---\n### ✨ Newsletter Preview (HTML):""")
    st.markdown(html, unsafe_allow_html=True)
