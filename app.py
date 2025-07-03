import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

st.set_page_config(page_title="Auto Newsletter Generator", layout="centered")
st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")
st.markdown("Paste article URLs below (one per line), then click **Generate Newsletter**.")

# --- Input box
urls_input = st.text_area("Article URLs", height=200, placeholder="https://example.com/article1\nhttps://example.com/article2")

# --- Button to trigger processing
if st.button("Generate Newsletter"):
    urls = [url.strip() for url in urls_input.split("\n") if url.strip()]
    if not urls:
        st.warning("Please enter at least one valid URL.")
    else:
        newsletter_html = """
        <div style='font-family:sans-serif; max-width:600px; margin:auto;'>
            <h1 style='text-align:center;'>Weekly Tech Digest</h1>
            <hr>
        """

        quick_reads = set()
        recommended_reads = set()

        for i, url in enumerate(urls):
            try:
                st.markdown(f"🔍 Fetching: {url}")
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Title
                title_tag = soup.find('title')
                title = title_tag.get_text(strip=True) if title_tag else f"Article {i+1}"

                # Summary using Groq
                chat_url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer YOUR_GROQ_API_KEY",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {"role": "system", "content": "You are a tech newsletter assistant."},
                        {"role": "user", "content": f"Summarize this article in 3 crisp sentences:\n{response.text[:3000]}"}
                    ]
                }
                summary_resp = requests.post(chat_url, headers=headers, json=payload)
                summary_data = summary_resp.json()
                summary = summary_data["choices"][0]["message"]["content"].strip()

                # Main image
                img_tag = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'twitter:image'})
                img_url = img_tag['content'] if img_tag else ""

                # Extract internal links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if any(domain in href for domain in ["youtube.com", "tiktok.com"]):
                        quick_reads.add(href)
                    elif "theverge.com" in href or "techcrunch.com" in href:
                        recommended_reads.add(href)

                # Create article block
                newsletter_html += f"""
                    <h2>{title}</h2>
                    {'<img src="' + img_url + '" alt="image" style="width:100%; border-radius:10px;">' if img_url else ''}
                    <p>{summary}</p>
                    <a href='{url}' style='color:#007BFF;'>Continue Reading</a>
                    <hr>
                """

            except Exception as e:
                st.error(f"Failed to process {url}: {str(e)}")

        # Quick Reads section
        if quick_reads:
            newsletter_html += "<h3>Quick Reads</h3><ul>"
            for link in list(quick_reads)[:5]:
                newsletter_html += f"<li><a href='{link}' target='_blank'>{link}</a></li>"
            newsletter_html += "</ul>"

        # Recommended Reads section
        if recommended_reads:
            newsletter_html += "<h3>Recommended Reads</h3><ul>"
            for link in list(recommended_reads)[:5]:
                newsletter_html += f"<li><a href='{link}' target='_blank'>{link}</a></li>"
            newsletter_html += "</ul>"

        newsletter_html += "</div>"

        st.markdown("""
        ### ✨ Newsletter Preview:
        """, unsafe_allow_html=True)
        st.components.v1.html(newsletter_html, height=1200, scrolling=True)
