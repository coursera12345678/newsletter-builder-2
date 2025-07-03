import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="Auto Newsletter Generator", layout="centered")
st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")

st.markdown("""
Paste article URLs below (one per line), then click **Summarize** to generate a professional HTML newsletter. It will include:
- A main article
- Sub-articles
- Quick Reads
- Recommended Reads
""")

urls_input = st.text_area("✍️ Article URLs", height=200)
submit = st.button("Summarize")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def extract_article_data(url):
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.title.string.strip() if soup.title else "No Title"

        desc_tag = soup.find("meta", attrs={"name": "description"})
        summary = desc_tag["content"] if desc_tag and "content" in desc_tag.attrs else "Summary not available."

        img_tag = soup.find("meta", property="og:image")
        image_url = img_tag["content"] if img_tag and "content" in img_tag.attrs else "https://via.placeholder.com/600x300?text=No+Image"

        all_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith("http") and url not in a['href']]

        return {
            "url": url,
            "title": title,
            "summary": summary,
            "image_url": image_url,
            "links": all_links
        }
    except Exception as e:
        return {
            "url": url,
            "title": "Error fetching article",
            "summary": str(e),
            "image_url": "https://via.placeholder.com/600x300?text=Error",
            "links": []
        }

if submit and urls_input:
    urls = [url.strip() for url in urls_input.strip().split("\n") if url.strip()]
    st.subheader("📄 Newsletter Preview (HTML)")

    articles = [extract_article_data(url) for url in urls]

    main_article = articles[0]
    sub_articles = articles[1:]

    quick_reads = []
    recommended_reads = []
    for a in articles:
        for link in a['links'][:2]:
            if len(quick_reads) < 3:
                quick_reads.append(link)
            elif len(recommended_reads) < 3:
                recommended_reads.append(link)

    html = f"""
    <div style='font-family:sans-serif; max-width:600px; margin:auto;'>
        <h1 style='text-align:center;'>Weekly Tech Digest</h1>
        <hr>
        <h2>{main_article['title']}</h2>
        <img src='{main_article['image_url']}' alt='main image' style='width:100%; border-radius:10px;'>
        <p>{main_article['summary']}</p>
        <a href='{main_article['url']}' style='color:#007BFF;'>Continue Reading</a>
        <hr>
        <h3>Other Top Stories</h3>
    """

    for sub in sub_articles:
        html += f"""
            <h4>{sub['title']}</h4>
            <img src='{sub['image_url']}' alt='image' style='width:100%; border-radius:10px;'>
            <p>{sub['summary']}</p>
            <a href='{sub['url']}' style='color:#007BFF;'>Continue Reading</a>
        """

    html += "<hr><h3>Quick Reads</h3><ul>"
    for link in quick_reads:
        html += f"<li><a href='{link}' target='_blank'>{link}</a></li>"
    html += "</ul><h3>Recommended Reads</h3><ul>"
    for link in recommended_reads:
        html += f"<li><a href='{link}' target='_blank'>{link}</a></li>"
    html += "</ul></div>"

    st.code(html, language="html")
    st.markdown("---")
    st.markdown("✅ Copy and paste the above HTML into your email tool (e.g., MailerLite, Mailchimp).")
