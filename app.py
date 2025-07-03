import requests
import streamlit as st
from urllib.parse import urlparse
import re

GNEWS_API_KEY = "YOUR_GNEWS_API_KEY" 

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

# Example usage in your Streamlit app:
def show_quick_and_recommended(main_url, main_title, all_used_urls):
    domain = get_root_domain(main_url)
    keywords = extract_keywords(main_title)
    # Quick Reads: related by keywords, from same site, not main article
    quick_links = gnews_search(keywords, domain, exclude_urls=all_used_urls | {main_url}, max_results=3)
    for _, url in quick_links:
        all_used_urls.add(url)
    # Recommended Reads: latest from same site, not already used
    recommended_links = gnews_latest(domain, exclude_urls=all_used_urls | {main_url}, max_results=3)
    for _, url in recommended_links:
        all_used_urls.add(url)
    # Format as Markdown
    quick_md = "\n".join([f"- [{t}]({l})" for t, l in quick_links]) if quick_links else "(No related articles found.)"
    recommended_md = "\n".join([f"- [{t}]({l})" for t, l in recommended_links]) if recommended_links else "(No more articles found.)"
    return quick_md, recommended_md

# Example for a single article:
main_url = "https://www.theverge.com/news/696877/xbox-perfect-dark-everwild-cancelled-the-initiative-layoffs"
main_title = "Microsoft cancels its Perfect Dark and Everwild Xbox games | The Verge"
all_used_urls = set([main_url])
quick_md, recommended_md = show_quick_and_recommended(main_url, main_title, all_used_urls)

st.markdown("**Quick Reads from this article:**")
st.markdown(quick_md)
st.markdown("**Recommended Reads:**")
st.markdown(recommended_md)
