import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ========== CONFIG ==========
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or "sk-REPLACE"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# ========== FUNCTIONS ==========
def fetch_article_content(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.string if soup.title else "No title found"
        image = soup.find("meta", property="og:image")
        image_url = image["content"] if image and image.get("content") else ""

        paragraphs = soup.find_all('p')
        text = " ".join(p.get_text() for p in paragraphs[:10])

        links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
        links = list(set([link for link in links if link.startswith("http") and url not in link]))

        return title.strip(), text.strip(), image_url, links
    except Exception as e:
        return "", "Failed to fetch article", "", []

def summarize_article_groq(content):
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a world-class tech newsletter editor."},
            {"role": "user", "content": f"Summarize this article in 3 crisp sentences:
\n\n{content}\n\nUse a conversational but professional tone."}
        ]
    }
    response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
    return response.json()['choices'][0]['message']['content'].strip()

# ========== STREAMLIT UI ==========
st.set_page_config(page_title="Tech Newsletter Generator", layout="centered")
st.title("📰 Weekly Tech Newsletter Generator")
st.markdown("Paste article URLs below (one per line). We'll summarize, extract links, and show the full newsletter preview — clean and styled.")

urls_input = st.text_area("Article URLs", height=150)
if st.button("Generate Newsletter") and urls_input:
    urls = [url.strip() for url in urls_input.splitlines() if url.strip()]
    newsletter_data = []
    quick_reads = set()
    rec_reads = set()

    with st.spinner("Summarizing and compiling newsletter..."):
        for url in urls:
            title, content, image_url, article_links = fetch_article_content(url)
            summary = summarize_article_groq(content)
            newsletter_data.append({
                "title": title,
                "summary": summary,
                "image_url": image_url,
                "url": url
            })
            # Assume first 2 links are Quick Reads, rest are Recs
            quick_reads.update(article_links[:2])
            rec_reads.update(article_links[2:5])

    # ========== DISPLAY NEWSLETTER ==========
    st.markdown("---")
    st.subheader("📬 Your Weekly Tech Digest")

    featured = newsletter_data[0]
    st.markdown(f"### {featured['title']}")
    if featured['image_url']:
        st.image(featured['image_url'], use_column_width=True)
    st.markdown(featured['summary'])
    st.markdown(f"[Continue Reading]({featured['url']})", unsafe_allow_html=True)

    if len(newsletter_data) > 1:
        st.markdown("---")
        st.subheader("📰 Other Top Stories")
        for story in newsletter_data[1:]:
            st.markdown(f"**{story['title']}**")
            if story['image_url']:
                st.image(story['image_url'], use_column_width=True)
            st.markdown(story['summary'])
            st.markdown(f"[Continue Reading]({story['url']})", unsafe_allow_html=True)

    if quick_reads:
        st.markdown("---")
        st.subheader("⚡ Quick Reads")
        for link in quick_reads:
            st.markdown(f"- [{link}]({link})")

    if rec_reads:
        st.markdown("---")
        st.subheader("📚 Recommended Reads")
        for link in rec_reads:
            st.markdown(f"- [{link}]({link})")
