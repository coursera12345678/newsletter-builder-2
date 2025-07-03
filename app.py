import streamlit as st
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import os
import re

# Load Groq API Key
API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-70b-8192"

# Helper function to extract links from within article HTML
def extract_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    return [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('http')]

# Groq call wrapper
def generate_summary(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    response = requests.post(GROQ_URL, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# HTML rendering helpers
def format_article_html(title, summary, link, image_url):
    return f"""
    <div style="margin-bottom: 30px;">
        <img src="{image_url}" alt="{title}" style="width:100%; border-radius: 8px;">
        <h2 style="margin: 10px 0 5px;">{title}</h2>
        <p style="margin: 0 0 10px;">{summary}</p>
        <a href="{link}" style="color: #3366cc; text-decoration: none;">Continue Reading →</a>
    </div>
    """

def format_list_section(title, links):
    if not links:
        return ""
    items = ''.join(f'<li><a href="{url}" style="color:#3366cc;">{url}</a></li>' for url in links)
    return f"""
    <h3 style="margin-top: 30px;">{title}</h3>
    <ul style="padding-left: 20px;">{items}</ul>
    """

# Streamlit App UI
st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")
st.write("Paste article URLs below (one per line), then click **Summarize**.")

urls_input = st.text_area("Article URLs", height=200)
if st.button("Summarize"):
    urls = [url.strip() for url in urls_input.splitlines() if url.strip()]
    if not urls:
        st.error("Please paste at least one valid URL.")
    else:
        newsletter_sections = []
        all_quick_reads = set()
        all_recommended_reads = set()

        for i, url in enumerate(urls):
            st.write(f"🔍 Fetching: {url}")
            try:
                article = Article(url)
                article.download()
                article.parse()
                article.nlp()

                title = article.title
                text = article.text
                image_url = article.top_image or "https://via.placeholder.com/600x300?text=No+Image"
                links_in_article = extract_links(article.html)

                # Summarize main content
                prompt = f"Summarize the following news article in 3-4 sentences in an informative but friendly tone:\n\n{text}"
                summary = generate_summary(prompt)

                # First article becomes main story
                if i == 0:
                    newsletter_sections.append(f"<h1 style='font-size:28px;'>Weekly Tech Digest</h1>")
                    newsletter_sections.append("<h2>Breaking News</h2>")
                elif i == 1:
                    newsletter_sections.append("<h2>Other Top Stories</h2>")

                newsletter_sections.append(format_article_html(title, summary, url, image_url))

                # Add links to Quick Reads / Recommended
                if links_in_article:
                    all_quick_reads.update(links_in_article[:2])
                    all_recommended_reads.update(links_in_article[2:4])

            except Exception as e:
                st.error(f"Error processing {url}: {e}")

        # Append Quick Reads & Recommended Reads
        newsletter_sections.append(format_list_section("Quick Reads", all_quick_reads))
        newsletter_sections.append(format_list_section("Recommended Reads", all_recommended_reads))

        final_html = f"""
        <div style="font-family: Arial, sans-serif; max-width:600px; margin:auto; padding:20px; line-height:1.6;">
            {''.join(newsletter_sections)}
        </div>
        """

        st.markdown("### ✨ Newsletter Preview (HTML):")
        st.code(final_html, language='html')
        st.components.v1.html(final_html, height=800, scrolling=True)
