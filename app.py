import streamlit as st
import requests
from newspaper import Article
from bs4 import BeautifulSoup

# -- Config --
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# -- Function to extract article content --
def extract_article_content(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.title, article.text
    except Exception as e:
        return "", f"⚠️ Error extracting article: {e}"

# -- Function to summarize with Groq --
def summarize_with_groq(text):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful newsletter assistant."},
            {"role": "user", "content": f"Summarize this article like it's a newsletter section. Make it clear and engaging: {text}"}
        ]
    }
    try:
        res = requests.post(GROQ_URL, headers=headers, json=payload)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Error generating summary: {e}"

# -- UI --
st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")
st.markdown("Paste article URLs below (one per line), then click Summarize.")

urls_input = st.text_area("Article URLs", height=200)
if st.button("Summarize") and urls_input:
    urls = [u.strip() for u in urls_input.split("\n") if u.strip()]
    summaries = []

    for idx, url in enumerate(urls):
        st.write(f"\n\n🔍 Fetching: {url}")
        title, content = extract_article_content(url)
        if content.startswith("⚠️"):
            summaries.append({"title": "Error", "summary": content, "url": url})
            continue

        st.write("✍️ Summarizing...")
        summary = summarize_with_groq(content)
        summaries.append({"title": title, "summary": summary, "url": url})

    # -- Render Newsletter Format --
    st.markdown("---")
    st.markdown("## 🗞️ Your Newsletter Preview")

    # MAIN ARTICLE
    main_title = summaries[0]["title"]
    main_summary = summaries[0]["summary"]
    main_url = summaries[0]["url"]

    st.markdown(f"""
    <h1 style="font-size: 28px;">{main_title}</h1>
    <p style="font-size: 18px;">{main_summary}</p>
    <p><a href="{main_url}" target="_blank">Read more →</a></p>
    """, unsafe_allow_html=True)

    # SUB-ARTICLES
    st.markdown('<div class="subheadline" style="font-size: 22px; margin-top: 2em;">Other Top Stories</div>', unsafe_allow_html=True)
    for item in summaries[1:]:
        st.markdown(f"""
        <p><b>{item["title"]}</b><br>{item["summary"]}<br>
        <a href="{item["url"]}" target="_blank">Read more →</a></p>
        """, unsafe_allow_html=True)

    # QUICK READS
    st.markdown('<div class="subheadline" style="font-size: 22px; margin-top: 2em;">Quick Reads</div><ul>', unsafe_allow_html=True)
    for item in summaries:
        st.markdown(f"""<li><a href="{item["url"]}" target="_blank">{item["title"]}</a></li>""", unsafe_allow_html=True)
    st.markdown('</ul>', unsafe_allow_html=True)

    # RECOMMENDED READS
    st.markdown('<div class="subheadline" style="font-size: 22px; margin-top: 2em;">Recommended Reads</div><ul>', unsafe_allow_html=True)
    for item in summaries:
        st.markdown(f"""<li><a href="{item["url"]}" target="_blank">{item["title"]}</a></li>""", unsafe_allow_html=True)
    st.markdown('</ul>', unsafe_allow_html=True)
