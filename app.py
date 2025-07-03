import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
from urllib.parse import urlparse

# Groq API setup
openai.api_key = st.secrets["GROQ_API_KEY"]
openai.api_base = "https://api.groq.com/openai/v1"

st.title("📰 Advanced Tech Newsletter Generator")
st.write("Paste your article URLs (one per line), then click Generate.")

urls_input = st.text_area("Input URLs", height=150)
submit = st.button("Generate")

@st.cache_data(show_spinner=False)
def fetch_article_content(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text() for p in paragraphs)
        return text.strip()
    except:
        return ""

def summarize_article(content):
    try:
        response = openai.ChatCompletion.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "user", "content": f"Summarize this article in a short but informative way, suitable for a newsletter. Do not include any extra lines or intros."},
                {"role": "user", "content": content[:4000]}
            ]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Summary unavailable. Error: {e}"

def get_featured_image(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        meta = soup.find("meta", property="og:image")
        if meta and meta.get("content"):
            return meta["content"]
    except:
        pass
    return None

def extract_title(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        return soup.title.string.strip()
    except:
        return "Title Unavailable"

def search_related(topic, domain):
    try:
        search_query = f"site:{domain} {topic}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(f"https://www.google.com/search?q={search_query}", headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        links = []
        for g in soup.find_all("div", class_="tF2Cxc"):
            title_elem = g.find("h3")
            link_elem = g.find("a")
            if title_elem and link_elem:
                links.append((title_elem.get_text(), link_elem["href"]))
        return links[:3]
    except:
        return []

if submit and urls_input:
    urls = urls_input.strip().split("\n")

    st.markdown("### Intro")
    st.write("Hi there! This week’s newsletter covers key updates: " + ", ".join([extract_title(u) for u in urls]))

    for u in urls:
        with st.spinner(f"🔍 Fetching: {u}"):
            content = fetch_article_content(u)
            if not content:
                st.warning(f"Failed to process {u}: Empty content")
                continue
            title = extract_title(u)
            image = get_featured_image(u)
            summary = summarize_article(content)

            st.markdown(f"## {title}")
            if image:
                st.image(image, use_container_width=True)

            st.write(summary)
            st.markdown(f"[Continue Reading →]({u})")

            # Quick Reads
            related = search_related(title, urlparse(u).netloc)
            if related:
                st.markdown("**Quick Reads from this Article**")
                for rt, rl in related:
                    st.markdown(f"- [{rt}]({rl})")

            st.markdown("---")

    # Recommended Reads (placeholder logic: gather similar articles)
    st.markdown("### 📚 Recommended Reads")
    for u in urls:
        title = extract_title(u)
        domain = urlparse(u).netloc
        related = search_related(title, domain)
        for rt, rl in related:
            st.markdown(f"- [{rt}]({rl})")
