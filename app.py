import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from groq import Groq
import re

st.set_page_config(page_title="Auto Newsletter Generator", layout="centered")
st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")

st.markdown("Paste article URLs below (one per line), then click **Generate Newsletter**.")

urls_input = st.text_area("Article URLs", height=200)
submit = st.button("Generate Newsletter")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def extract_article_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        html = requests.get(url, headers=headers).text
        soup = BeautifulSoup(html, 'html.parser')

        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()

        paragraphs = soup.find_all('p')
        text = "\n".join(p.get_text() for p in paragraphs if len(p.get_text()) > 50)
        return text.strip()
    except Exception as e:
        return ""

def extract_og_image(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        html = requests.get(url, headers=headers).text
        soup = BeautifulSoup(html, 'html.parser')
        og_image = soup.find("meta", property="og:image")
        if og_image:
            return og_image['content']
    except:
        pass
    return ""

def summarize_article(content):
    try:
        chat_completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "user", "content": f"Summarize this article in 3 crisp sentences:\n\n{content}"}
            ]
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return "Summary not available."

def extract_links(content):
    return re.findall(r'https?://\S+', content)

if submit and urls_input:
    urls = [url.strip() for url in urls_input.strip().splitlines() if url.strip()]
    main_article = urls[0] if urls else None
    other_articles = urls[1:] if len(urls) > 1 else []

    main_summary, other_summaries = "", []
    quick_reads, recommended_reads = set(), set()

    if main_article:
        st.markdown("🔍 Fetching main article...")
        content = extract_article_text(main_article)
        summary = summarize_article(content)
        image_url = extract_og_image(main_article)
        links = extract_links(content)
        main_summary = {
            "url": main_article,
            "summary": summary,
            "image": image_url,
            "title": "Main Story"
        }
        for link in links:
            if "youtube" in link or "tiktok" in link:
                quick_reads.add(link)
            else:
                recommended_reads.add(link)

    for url in other_articles:
        st.markdown(f"🔍 Fetching: {url}")
        content = extract_article_text(url)
        summary = summarize_article(content)
        image_url = extract_og_image(url)
        links = extract_links(content)
        other_summaries.append({
            "url": url,
            "summary": summary,
            "image": image_url,
            "title": urlparse(url).netloc.replace("www.", "")
        })
        for link in links:
            if "youtube" in link or "tiktok" in link:
                quick_reads.add(link)
            else:
                recommended_reads.add(link)

    st.markdown("## ✨ Newsletter Preview")
    st.markdown("""
        <div style='font-family:sans-serif; max-width:700px; margin:auto;'>
            <h1 style='text-align:center;'>Weekly Tech Digest</h1>
            <hr>
    """, unsafe_allow_html=True)

    if main_summary:
        st.markdown(f"""
            <h2>{main_summary['title']}</h2>
            <img src='{main_summary['image']}' alt='main image' style='width:100%; border-radius:10px;'>
            <p>{main_summary['summary']}</p>
            <a href='{main_summary['url']}' style='color:#007BFF;'>Continue Reading</a>
            <hr>
        """, unsafe_allow_html=True)

    if other_summaries:
        st.markdown("<h3>Other Top Stories</h3>", unsafe_allow_html=True)
        for art in other_summaries:
            st.markdown(f"""
                <h4>{art['title']}</h4>
                <img src='{art['image']}' alt='image' style='width:100%; border-radius:10px;'>
                <p>{art['summary']}</p>
                <a href='{art['url']}' style='color:#007BFF;'>Continue Reading</a>
            """, unsafe_allow_html=True)

    if quick_reads:
        st.markdown("<hr><h3>Quick Reads</h3><ul>" + ''.join(f"<li><a href='{q}' target='_blank'>{q}</a></li>" for q in quick_reads) + "</ul>", unsafe_allow_html=True)

    if recommended_reads:
        st.markdown("<h3>Recommended Reads</h3><ul>" + ''.join(f"<li><a href='{r}' target='_blank'>{r}</a></li>" for r in recommended_reads) + "</ul></div>", unsafe_allow_html=True)
