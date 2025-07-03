import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from groq import Groq

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

def get_root_domain(url):
    netloc = urlparse(url).netloc
    parts = netloc.split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    return netloc

def get_related_articles(query, domain, exclude_urls, count=2):
    api_key = st.secrets["NEWSAPI_KEY"]
    endpoint = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "domains": domain,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": 5,
        "apiKey": api_key
    }
    try:
        response = requests.get(endpoint, params=params, timeout=8)
        if response.status_code == 200:
            results = response.json().get("articles", [])
            links = []
            for item in results:
                if item['url'] not in exclude_urls:
                    links.append((item['title'], item['url']))
                if len(links) >= count:
                    break
            return links
        else:
            return []
    except Exception:
        return []

def get_latest_articles(domain, exclude_urls, count=3):
    api_key = st.secrets["NEWSAPI_KEY"]
    endpoint = "https://newsapi.org/v2/everything"
    params = {
        "domains": domain,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": max(10, count),
        "apiKey": api_key
    }
    try:
        response = requests.get(endpoint, params=params, timeout=8)
        if response.status_code == 200:
            results = response.json().get("articles", [])
            links = []
            for item in results:
                if item['url'] not in exclude_urls:
                    links.append((item['title'], item['url']))
                if len(links) >= count:
                    break
            return links
        else:
            return []
    except Exception:
        return []

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
    domains = []
    all_used_urls = set(urls)  # To avoid any repeats
    quick_links_per_article = []

    for u in urls:
        try:
            st.markdown(f"🔍 Fetching: {u}")
            res = requests.get(u)
            soup = BeautifulSoup(res.text, "html.parser")
            title = soup.find("title").text.strip()
            content = "\n".join(p.text for p in soup.find_all("p"))
            summary = summarize_article(content, title)
            image_url = extract_image(soup)
            domain = get_root_domain(u)
            domains.append(domain)

            # Related articles from same domain using title as query, excluding this article and any already used
            related_links = get_related_articles(title, domain, all_used_urls, count=2)
            # Add these quick links to the set of all used URLs
            for _, link_url in related_links:
                all_used_urls.add(link_url)
            quick_links_per_article.append(set(link_url for _, link_url in related_links))

            # Format quick links as Markdown
            if related_links:
                quick_links_md = "<br>".join(f"[{t}]({l})" for t, l in related_links)
            else:
                quick_links_md = "(No related articles found on this site.)"

            headlines.append(title)

            section = f"""
            <h2>{title}</h2>
            <img src="{image_url}" style="width:100%; border-radius: 12px;"/>
            <p>{summary}</p>
            <p><a href="{u}" target="_blank"><b>Continue Reading →</b></a></p>
            <div style="margin-top:10px; padding:10px; background-color:#f0f4f8; border-left:4px solid #1e88e5;">
                <b>Quick Reads from this article:</b><br>
                {quick_links_md}
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

        # Final recommended section: show latest stories from the most common domain, excluding all previously shown links
        try:
            from collections import Counter
            most_common_domain = Counter(domains).most_common(1)[0][0] if domains else None
            # Exclude all main articles and all quick links already shown
            exclude_urls = set(urls)
            for quick_set in quick_links_per_article:
                exclude_urls.update(quick_set)
            recommended_links = get_latest_articles(most_common_domain, exclude_urls, count=3)
            if recommended_links:
                st.markdown("<h3>🔗 Recommended Reads</h3>", unsafe_allow_html=True)
                st.markdown("<br>".join(f"[{t}]({l})" for t, l in recommended_links), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Failed to fetch recommended reads: {e}")
