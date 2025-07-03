import streamlit as st
import requests
from urllib.parse import urlparse
import re

GNEWS_API_KEY = st.secrets["GNEWS_API_KEY"]

def get_root_domain(url):
    netloc = urlparse(url).netloc
    parts = netloc.split('.')
    return '.'.join(parts[-2:]) if len(parts) >= 2 else netloc

def extract_keywords(title, max_keywords=4):
    stopwords = set([
        "the", "and", "for", "but", "with", "from", "this", "that", "have", "has", "will", "are",
        "was", "its", "his", "her", "their", "our", "your", "about", "into", "over", "plus", "just",
        "more", "than", "now", "out", "new", "all", "can", "see", "get", "got", "off", "on", "in",
        "to", "of", "by", "as", "at", "is", "it", "be", "or", "an", "a", "so", "up", "back", "for",
        "not", "you", "we", "he", "she", "they", "his", "her", "our", "their", "your", "my", "me", "i"
    ])
    words = re.findall(r'\b\w+\b', title.lower())
    keywords = [w for w in words if w not in stopwords and len(w) > 3]
    keywords = sorted(keywords, key=len, reverse=True)
    return " ".join(keywords[:max_keywords]) if keywords else title

def gnews_search(query, domain, exclude_urls=None, max_results=5):
    url = f"https://gnews.io/api/v4/search"
    params = {
        "q": query,
        "token": GNEWS_API_KEY,
        "lang": "en",
        "max": max_results,
        "site": domain
    }
    resp = requests.get(url, params=params)
    results = []
    if resp.status_code == 200:
        data = resp.json()
        for article in data.get("articles", []):
            if exclude_urls and article["url"] in exclude_urls:
                continue
            results.append((article["title"], article["url"]))
    return results

def gnews_latest(domain, exclude_urls=None, max_results=5):
    url = f"https://gnews.io/api/v4/top-headlines"
    params = {
        "token": GNEWS_API_KEY,
        "lang": "en",
        "max": max_results,
        "site": domain
    }
    resp = requests.get(url, params=params)
    results = []
    if resp.status_code == 200:
        data = resp.json()
        for article in data.get("articles", []):
            if exclude_urls and article["url"] in exclude_urls:
                continue
            results.append((article["title"], article["url"]))
    return results

st.set_page_config(page_title="📰 Advanced Tech Newsletter Generator")
st.title("📰 Advanced Tech Newsletter Generator")

st.markdown("Paste your article URLs (one per line), then click Generate.")
urls_input = st.text_area("Input URLs")
submit = st.button("Generate Newsletter")

if submit:
    urls = [u.strip() for u in urls_input.split("\n") if u.strip()]
    all_used_urls = set(urls)
    domains = []
    headlines = []
    sections = []

    for u in urls:
        st.markdown(f"🔍 Fetching: {u}")
        try:
            # Fetch the article title
            resp = requests.get(u, timeout=10)
            title = re.search(r"<title>(.*?)</title>", resp.text, re.IGNORECASE)
            title = title.group(1).strip() if title else u
        except Exception:
            title = u
        headlines.append(title)
        domain = get_root_domain(u)
        domains.append(domain)
        keywords = extract_keywords(title)
        # Quick Reads: related by keywords, from same site, not main article
        quick_links = gnews_search(keywords, domain, exclude_urls=all_used_urls | {u}, max_results=3)
        for _, url in quick_links:
            all_used_urls.add(url)
        quick_md = "\n".join([f"- [{t}]({l})" for t, l in quick_links]) if quick_links else "(No related articles found.)"
        section = f"""
        <h2>{title}</h2>
        <p><a href="{u}" target="_blank"><b>Continue Reading →</b></a></p>
        <div style="margin-top:10px; padding:10px; background-color:#f0f4f8; border-left:4px solid #1e88e5;">
            <b>Quick Reads from this article:</b>
            <br>
            {quick_md}
        </div>
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        """
        sections.append(section)

    if sections:
        intro = f"Hi there! This week’s newsletter covers: {', '.join(headlines)}. Dive in below!"
        st.markdown("## ✨ Newsletter Preview:")
        st.markdown(f"<p>{intro}</p>", unsafe_allow_html=True)
        for s in sections:
            st.markdown(s, unsafe_allow_html=True)
            # Also render Quick Reads as Markdown for clickable links
            st.markdown(s.split("<br>")[-1], unsafe_allow_html=True)

        # Recommended Reads: latest from the most common domain, excluding all previously shown links
        from collections import Counter
        most_common_domain = Counter(domains).most_common(1)[0][0] if domains else None
        recommended_links = gnews_latest(most_common_domain, exclude_urls=all_used_urls, max_results=3)
        recommended_md = "\n".join([f"- [{t}]({l})" for t, l in recommended_links]) if recommended_links else "(No more articles found.)"
        st.markdown("<h3>🔗 Recommended Reads</h3>", unsafe_allow_html=True)
        st.markdown(recommended_md)
