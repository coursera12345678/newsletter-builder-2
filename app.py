import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from groq import Groq
import re

# Initialize Groq client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def fetch_article_content(url):
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = soup.find_all("p")
        return "\n".join(p.text for p in paragraphs)
    except Exception as e:
        return f"Failed to fetch article: {e}"

def summarize_article(content, title):
    prompt = f"""
    Summarize the following article titled '{title}' in a concise and engaging tone. Do not start with 'Here is a summary...'. Limit it to about 5-6 crisp sentences:
    {content}
    """
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Summary failed: {e}"

def extract_image(soup):
    og_img = soup.find("meta", property="og:image")
    return og_img["content"] if og_img else None

def validate_url(url):
    try:
        res = requests.head(url, allow_redirects=True, timeout=5)
        return res.status_code == 200
    except:
        return False

def filter_valid_links(markdown_links):
    pattern = r"\[([^\]]+)\]\((https?://[^\)]+)\)"
    matches = re.findall(pattern, markdown_links)
    valid_links = [
        f"[{title}]({url})"
        for title, url in matches if validate_url(url)
    ]
    return "<br>".join(valid_links) if valid_links else "(No valid links found.)"

def search_related_articles(query, domain="www.theverge.com"):
    search_prompt = f"""
    Find 2 recent articles from {domain} that are related to this topic: '{query}'. For each, return a title and a URL. Avoid TikTok, YouTube or social links.
    Format: [Title](URL)
    """
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": search_prompt}]
        )
        raw_links = completion.choices[0].message.content.strip()
        return filter_valid_links(raw_links)
    except Exception as e:
        return f"(Failed to load related reads: {e})"

def generate_intro(headlines):
    joined = ", ".join(headlines)
    return f"Hi there! This week’s newsletter covers: {joined}. Dive in below!"

st.set_page_config(page_title="📰 Advanced Tech Newsletter Generator")
st.title("📰 Advanced Tech Newsletter Generator")

st.markdown("Paste your article URLs (one per line), then click Generate.")
urls_input = st.text_area("Input URLs")
submit = st.button("Generate Newsletter")

if submit:
    urls = [u.strip() for u in urls_input.split("\n") if u.strip()]
    headlines = []
    sections = []

    for u in urls:
        try:
            st.markdown(f"🔍 Fetching: {u}")
            res = requests.get(u)
            soup = BeautifulSoup(res.text, "html.parser")
            title = soup.find("title").text.strip()
            content = "\n".join(p.text for p in soup.find_all("p"))
            summary = summarize_article(content, title)
            image_url = extract_image(soup)
            related = search_related_articles(title, urlparse(u).netloc)

            headlines.append(title)

            section = f"""
            <h2>{title}</h2>
            <img src="{image_url}" style="width:100%; border-radius: 12px;"/>
            <p>{summary}</p>
            <p><a href="{u}" target="_blank"><b>Continue Reading →</b></a></p>
            <div style="margin-top:10px; padding:10px; background-color:#f0f4f8; border-left:4px solid #1e88e5;">
                <b>Quick Reads from this article:</b><br>
                {related}
            </div>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
            """
            sections.append(section)

        except Exception as e:
            st.error(f"Failed to process {u}: {e}")

    if sections:
        intro = generate_intro(headlines)
        st.markdown("## ✨ Newsletter Preview:")
        st.markdown(f"<p>{intro}</p>", unsafe_allow_html=True)
        for s in sections:
            st.markdown(s, unsafe_allow_html=True)

        # Final recommended section
        try:
            final_summ = search_related_articles(
                f"{', '.join(headlines)}",
                domain="www.theverge.com"
            )
            st.markdown("<h3>🔗 Recommended Reads</h3>", unsafe_allow_html=True)
            st.markdown(final_summ, unsafe_allow_html=True)
        except:
            pass

