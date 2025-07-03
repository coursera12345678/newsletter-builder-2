import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
import time

# --- Config
GROQ_KEY = st.secrets["GROQ_API_KEY"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-70b-8192"

HEADERS = {
    "Authorization": f"Bearer {GROQ_KEY}",
    "Content-Type": "application/json",
}

# --- Functions

def fetch_article(url):
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    title = (soup.find("meta", property="og:title") or soup.title).get("content", "") if soup.title else "No title"
    img = soup.find("meta", property="og:image")
    img_url = img["content"] if img else ""
    paragraphs = soup.find_all("p")
    text = " ".join(p.get_text() for p in paragraphs[:10])
    return title.strip(), img_url, text

def summarize(text):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a crisp newsletter writer."},
            {"role": "user", "content": f"Summarize this article clearly:\n\n{text}"}
        ]
    }
    res = requests.post(GROQ_URL, headers=HEADERS, json=payload).json()
    return res.get("choices", [{}])[0].get("message", {}).get("content", "Summary unavailable.")

def search_related(query, site, n=3):
    # Scrap Google search results page
    url = f"https://www.google.com/search?q=site%3A{site}+{quote(query)}&num={n}"
    r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
    links = re.findall(r"/url\?q=(https://[^&]+)&", r.text)
    summaries = []
    for link in links[:n]:
        title, img, text = fetch_article(link)
        summaries.append({"title": title, "url": link})
        time.sleep(1)
    return summaries

# --- UI

st.title("📰 Advanced Tech Newsletter Generator")
st.write("Paste your article URLs (one per line), then click **Generate**.")

urls = st.text_area("Input URLs", height=150)
if st.button("Generate"):
    url_list = [u.strip() for u in urls.splitlines() if u.strip()]
    st.markdown("### Intro")
    intro = ("Hi there! This week’s newsletter covers key updates: "
             + "; ".join([fetch_article(u)[0] for u in url_list]))
    st.info(intro)

    for u in url_list:
        title, img_url, text = fetch_article(u)
        summary = summarize(text[:3000])
        st.subheader(title)
        if img_url: st.image(img_url, use_column_width=True)
        st.write(summary)
        st.markdown(f"[Continue Reading →]({u})")

        # Quick Reads
        related = search_related(title, urlparse(u).netloc)
        if related:
            st.markdown("**Quick Reads (from publisher):**")
            for r in related:
                st.markdown(f"- [{r['title']}]({r['url']})")
        st.markdown("---")

    # Recommended reads across the web
    st.subheader("📚 Recommended Reads")
    recs = []
    for kw in ["AI tech", "cloud infrastructure", "app UX"]:
        recs += search_related(kw, "theverge.com", n=2)
    rec_seen = set()
    for r in recs:
        if r["url"] not in rec_seen:
            st.markdown(f"- [{r['title']}]({r['url']})")
            rec_seen.add(r["url"])
