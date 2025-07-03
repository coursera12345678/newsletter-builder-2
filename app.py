import streamlit as st
import requests
from urllib.parse import urlparse
from groq import Groq

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
BRAVE_API_KEY = st.secrets["BRAVE_API_KEY"]

def get_root_domain(url):
    netloc = urlparse(url).netloc
    parts = netloc.split('.')
    return '.'.join(parts[-2:]) if len(parts) >= 2 else netloc

def brave_search(query, domain, max_results=3):
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
    params = {"q": f"site:{domain} {query}", "count": max_results}
    resp = requests.get(url, headers=headers, params=params)
    results = []
    if resp.status_code == 200:
        data = resp.json()
        for item in data.get("web", {}).get("results", []):
            results.append((item["title"], item["url"]))
    return results

def summarize_text(text, title):
    prompt = f"Summarize the following article titled '{title}' in 5 concise sentences:\n\n{text}"
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip()

st.title("📰 Newsletter Generator with Groq + Brave Search")

urls_input = st.text_area("Paste article URLs (one per line)")
if st.button("Generate"):
    urls = [u.strip() for u in urls_input.split("\n") if u.strip()]
    all_used_urls = set(urls)

    for url in urls:
        st.markdown(f"### Processing: {url}")
        domain = get_root_domain(url)
        try:
            res = requests.get(url, timeout=10)
            # Extract article text (simple approach)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(res.text, "html.parser")
            paragraphs = soup.find_all("p")
            content = "\n".join(p.text for p in paragraphs)[:4000]
            title = soup.title.string.strip() if soup.title else url

            summary = summarize_text(content, title)
            st.markdown(f"**Summary:** {summary}")

            # Get related links from Brave Search
            related = brave_search(title, domain, max_results=3)
            st.markdown("**Quick Reads:**")
            for t, l in related:
                if l not in all_used_urls:
                    st.markdown(f"- [{t}]({l})")
                    all_used_urls.add(l)

        except Exception as e:
            st.error(f"Failed to process {url}: {e}")
