import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# Load API key
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_MODEL = "llama3-8b-8192"

st.set_page_config(page_title="📰 Auto Newsletter Generator", layout="centered")
st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")

st.markdown("Paste article URLs below (one per line), then click **Generate Newsletter**.")

urls_input = st.text_area("Article URLs", height=200)
generate = st.button("Generate Newsletter")

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

def fetch_article_data(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        title = soup.find("title").text.strip() if soup.find("title") else "Untitled"
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs[:10])

        image_tag = soup.find("meta", property="og:image") or soup.find("img")
        image_url = image_tag["content"] if image_tag and image_tag.has_attr("content") else ""
        if not image_url and image_tag and image_tag.has_attr("src"):
            image_url = urljoin(url, image_tag["src"])

        # Extract internal links
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "http" in href and not href.startswith("#") and url not in href:
                links.append(href)
        links = list(set(links))[:5]

        return title, text, image_url, links
    except Exception as e:
        return "Error", "", "", []

def summarize_text(title, content):
    prompt = f"Summarize the following article titled '{title}' in 3-4 lines:\n\n{content}"
    data = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
    return res.json()['choices'][0]['message']['content'].strip()

if generate:
    urls = [url.strip() for url in urls_input.split("\n") if url.strip()]
    summaries = []
    quick_reads = set()
    recommended_reads = set()

    for idx, url in enumerate(urls):
        with st.spinner(f"🔍 Fetching: {url}"):
            title, content, image_url, links = fetch_article_data(url)
            summary = summarize_text(title, content)

            summaries.append({
                "title": title,
                "summary": summary,
                "image_url": image_url,
                "url": url
            })

            for link in links:
                if "youtube" in link or "trailer" in link:
                    recommended_reads.add(link)
                else:
                    quick_reads.add(link)

    # Render newsletter HTML
    html = '<div style="font-family:sans-serif; max-width:600px; margin:auto;">'
    html += '<h1 style="text-align:center; color:#333;">Weekly Tech Digest</h1>'

    # Main story
    main = summaries[0]
    html += f"""
        <div style="margin-bottom:30px;">
            <img src="{main['image_url']}" alt="Main Image" style="width:100%; border-radius:10px;">
            <h2 style="color:#2c3e50;">{main['title']}</h2>
            <p style="color:#555;">{main['summary']}</p>
            <a href="{main['url']}" style="color:#1e90ff; text-decoration:none;">Continue Reading →</a>
        </div>
    """

    # Other stories
    html += '<h3 style="border-top:1px solid #ccc; padding-top:20px; color:#2c3e50;">Top Stories</h3>'
    for story in summaries[1:]:
        html += f"""
            <div style="margin-bottom:20px;">
                <img src="{story['image_url']}" alt="Story Image" style="width:100%; border-radius:10px;">
                <h4 style="color:#2c3e50;">{story['title']}</h4>
                <p style="color:#555;">{story['summary']}</p>
                <a href="{story['url']}" style="color:#1e90ff; text-decoration:none;">Continue Reading →</a>
            </div>
        """

    # Quick Reads
    html += '<h3 style="margin-top:30px; color:#2c3e50;">Quick Reads</h3><ul>'
    for link in quick_reads:
        html += f'<li><a href="{link}" target="_blank" style="color:#1e90ff;">{link}</a></li>'
    html += '</ul>'

    # Recommended Reads
    html += '<h3 style="margin-top:30px; color:#2c3e50;">Recommended Reads</h3><ul>'
    for link in recommended_reads:
        html += f'<li><a href="{link}" target="_blank" style="color:#1e90ff;">{link}</a></li>'
    html += '</ul>'

    html += '</div>'

    st.markdown("### ✨ Newsletter Preview (HTML):", unsafe_allow_html=True)
    st.components.v1.html(html, height=900, scrolling=True)
