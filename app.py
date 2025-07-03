import streamlit as st
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re
import time

st.set_page_config(page_title="📰 Advanced Tech Newsletter Generator", layout="centered")
st.title("📰 Advanced Tech Newsletter Generator")
st.caption("Paste your article URLs (one per line), then click Generate.")

urls_input = st.text_area("Input URLs", height=150)

if st.button("Generate Newsletter") and urls_input:
    urls = [url.strip() for url in urls_input.split("\n") if url.strip()]
    
    st.markdown("### Intro")
    st.write("Hi there! This week’s newsletter covers key updates: Microsoft cancels its Perfect Dark and Everwild Xbox games; Google Photos sees several app improvements; Apple’s alien thriller Invasion is back for season 3 in August")

    def fetch_article(url):
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(res.content, "html.parser")
            title = soup.title.string if soup.title else "No title"
            paragraphs = soup.find_all('p')
            text = " ".join(p.get_text() for p in paragraphs[:10])
            img_tag = soup.find("meta", property="og:image")
            img_url = img_tag["content"] if img_tag else ""
            return title, text, img_url
        except Exception as e:
            return "", "Failed to fetch article", ""

    def summarize(text):
        prompt = f"Please summarize the following article in 5-6 crisp, clear sentences:\n\n{text}" 
        try:
            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama3-8b-8192",
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            summary = res.json()['choices'][0]['message']['content']
            return summary.strip()
        except Exception as e:
            return "Summary unavailable."

    def search_related(topic, domain):
        try:
            query = f"site:{domain} {topic}"
            res = requests.get(f"https://ddg-webapp-aagd.vercel.app/search?q={query}")
            data = res.json()
            links = [(r['title'], r['href']) for r in data['results'] if domain in r['href']]
            return links[:3]
        except:
            return []

    def display_article(title, summary, image, link, related_articles):
        st.markdown(f"## {title}")
        if image:
            st.image(image, use_container_width=True)
        st.markdown(summary)
        st.markdown(f"[Continue Reading →]({link})")
        
        if related_articles:
            st.markdown("**Quick Reads from this article**")
            for r_title, r_link in related_articles:
                st.markdown(f"- [{r_title}]({r_link})")
        st.markdown("<hr style='border: 1px solid #ccc;'>", unsafe_allow_html=True)

    all_recommended = []

    for url in urls:
        st.markdown("\n")
        title, text, img = fetch_article(url)
        summary = summarize(text)
        related = search_related(title, urlparse(url).netloc)
        display_article(title, summary, img, url, related)
        all_recommended.extend(related)
        time.sleep(1)

    if all_recommended:
        st.markdown("## Recommended Reads")
        for r_title, r_link in all_recommended:
            st.markdown(f"- [{r_title}]({r_link})")
