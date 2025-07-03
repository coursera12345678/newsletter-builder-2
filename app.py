import streamlit as st
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re
from groq import Groq

BRAVE_API_KEY = st.secrets["BRAVE_API_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

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

def brave_search(query, domain, exclude_urls=None, max_results=10):
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
    params = {"q": f"site:{domain} {query}", "count": max_results}
    resp = requests.get(url, headers=headers, params=params)
    results = []
    if resp.status_code == 200:
        data = resp.json()
        for item in data.get("web", {}).get("results", []):
            if exclude_urls and item["url"] in exclude_urls:
                continue
            results.append({
                "title": item["title"],
                "url": item["url"]
            })
    return results

def get_article_image(url):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img.get("content"):
            return og_img["content"]
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]
    except:
        pass
    return None

def get_article_text(url):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        paragraphs = soup.find_all("p")
        return "\n".join([p.get_text() for p in paragraphs])[:4000]
    except:
        return ""

def summarize_article(content, title):
    prompt = f"Summarize the following article titled '{title}' in 5 concise, engaging sentences. Do not start with 'Here is a summary...':\n{content}"
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return "Summary unavailable."

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

    for u in urls:
        try:
            resp = requests.get(u, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            title = soup.title.string.strip() if soup.title else u
            image_url = get_article_image(u)
            article_text = get_article_text(u)
            summary = summarize_article(article_text, title)
        except Exception:
            title = u
            image_url = None
            summary = "Summary unavailable."

        headlines.append(title)
        domain = get_root_domain(u)
        domains.append(domain)
        keywords = extract_keywords(title)

        # Quick Reads: related by keywords, from same site, not main article
        quick_links = brave_search(keywords, domain, exclude_urls=all_used_urls | {u}, max_results=6)
        quick_links = quick_links[:3]
        for link in quick_links:
            all_used_urls.add(link["url"])

        st.markdown(f"## {title}")
        if image_url:
            st.image(image_url, use_container_width=True)
        st.markdown(f"{summary}")
        st.markdown(f"[Continue Reading →]({u})")

        st.markdown("**Quick Reads from this article:**")
        if quick_links:
            for link in quick_links:
                st.markdown(f"- [{link['title']}]({link['url']})")
        else:
            st.markdown("_No related articles found._")

        st.markdown("---")

    # Recommended Reads: recent articles from the most common domain, not already used
    from collections import Counter
    most_common_domain = Counter(domains).most_common(1)[0][0] if domains else None
    recommended_links = brave_search("", most_common_domain, exclude_urls=all_used_urls, max_results=10)
    recommended_links = recommended_links[:3]
    st.markdown("### 🔗 Recommended Reads")
    if recommended_links:
        for link in recommended_links:
            st.markdown(f"- [{link['title']}]({link['url']})")
    else:
        st.markdown("_No more articles found._")
