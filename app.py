import streamlit as st
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re
from groq import Groq

# Load API keys from .streamlit/secrets.toml
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
    return keywords[:max_keywords] if keywords else words[:max_keywords]

def get_synonyms(keywords):
    prompt = (
        f"For each of these keywords: {', '.join(keywords)}, "
        "give 2 synonyms or related words (comma-separated, no explanations, just the list)."
    )
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        response = completion.choices[0].message.content.strip()
        synonym_list = []
        for line in response.split("\n"):
            if ":" in line:
                syns = line.split(":")[1]
            else:
                syns = line
            for s in syns.split(","):
                word = s.strip()
                if word and word not in synonym_list:
                    synonym_list.append(word)
        return synonym_list
    except Exception:
        return []

def brave_search(query, domain=None, exclude_urls=None, max_results=10):
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
    if domain:
        params = {"q": f"site:{domain} {query}", "count": max_results}
    else:
        params = {"q": query, "count": max_results}
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
        text = "\n".join([p.get_text() for p in paragraphs]).strip()
        return text[:4000] if text else ""
    except:
        return ""

def summarize_article(content, title):
    # Always provide *some* context to the LLM
    if not content:
        content = f"This article is titled: {title}."
    prompt = f"Summarize the following article titled '{title}' in 5 concise, engaging sentences. Do not start with 'Here is a summary...':\n{content}"
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        summary = completion.choices[0].message.content.strip()
        if not summary or summary.lower().startswith("summary unavailable"):
            return "Summary unavailable."
        return summary
    except Exception:
        return "Summary unavailable."

def generate_intro(titles):
    joined_titles = "; ".join(titles)
    prompt = (
        f"Write a short, friendly, and energetic newsletter intro (2-3 sentences) "
        f"welcoming readers and mentioning these topics: {joined_titles}. "
        "Do not use a list. Make it inviting and concise."
    )
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        return (
            f"Welcome to this week's newsletter! Today, we're covering: {joined_titles}. "
            "Dive in below for all the details!"
        )

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
    article_data = []

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
        article_data.append({
            "url": u,
            "title": title,
            "image_url": image_url,
            "summary": summary,
            "domain": domain,
            "keywords": keywords
        })

    # Generate and display the intro in small paragraph text
    intro_text = generate_intro(headlines)
    st.markdown(f'<p style="font-size:0.95em;">{intro_text}</p>', unsafe_allow_html=True)
    st.markdown("---")

    # For deduplication
    quick_used_urls = set()

    for data in article_data:
        u = data["url"]
        title = data["title"]
        image_url = data["image_url"]
        summary = data["summary"]
        domain = data["domain"]
        keywords = data["keywords"]

        # Quick Reads: related by keywords, from same site, not main article
        quick_links = brave_search(" ".join(keywords), domain, exclude_urls=quick_used_urls | {u}, max_results=8)
        quick_links = quick_links[:3]
        for link in quick_links:
            quick_used_urls.add(link["url"])

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

    # After all quick links, update all_used_urls to prevent overlap with recommendations
    all_used_urls.update(quick_used_urls)

    # Recommended Reads: escalate aggressively
    from collections import Counter
    most_common_domain = Counter(domains).most_common(1)[0][0] if domains else None
    recommended_links = []

    # 1. Try recent from same domain
    recommended_links += brave_search("", most_common_domain, exclude_urls=all_used_urls, max_results=20)

    # 2. If not enough, try synonyms of all main keywords
    if len(recommended_links) < 3:
        all_keywords = []
        for data in article_data:
            all_keywords += data["keywords"]
        synonyms = get_synonyms(all_keywords)
        for syn in synonyms:
            if len(recommended_links) >= 9:
                break
            recommended_links += brave_search(syn, most_common_domain, exclude_urls=all_used_urls | {l['url'] for l in recommended_links}, max_results=4)

    # 3. If STILL not enough, drop domain restriction for latest tech news
    if len(recommended_links) < 3:
        recommended_links += brave_search("technology", None, exclude_urls=all_used_urls | {l['url'] for l in recommended_links}, max_results=20)

    # 4. As a last resort, just fetch any recent articles
    if len(recommended_links) < 3:
        recommended_links += brave_search("", None, exclude_urls=all_used_urls | {l['url'] for l in recommended_links}, max_results=20)

    # Deduplicate and keep only 3
    seen = set()
    final_recommended = []
    for link in recommended_links:
        if link["url"] not in seen and link["url"] not in all_used_urls:
            final_recommended.append(link)
            seen.add(link["url"])
        if len(final_recommended) == 3:
            break

    st.markdown("### 🔗 Recommended Reads")
    if final_recommended:
        for link in final_recommended:
            st.markdown(f"- [{link['title']}]({link['url']})")
    else:
        st.markdown("_No more articles found._")
