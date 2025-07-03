import streamlit as st
import requests
from bs4 import BeautifulSoup

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]  # Ensure you set this in Streamlit secrets

st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")
st.markdown("Paste article URLs below (one per line), then click Generate Newsletter.")

urls_input = st.text_area("Article URLs", height=150)

if st.button("Generate Newsletter"):
    urls = [url.strip() for url in urls_input.strip().split("\n") if url.strip()]
    summaries = []
    quick_reads = []
    recommended_reads = []

    for url in urls:
        st.write(f"🔍 Fetching: {url}")

        try:
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            title_tag = soup.find("meta", property="og:title") or soup.find("title")
            image_tag = soup.find("meta", property="og:image")

            title = title_tag["content"] if title_tag and title_tag.has_attr("content") else (title_tag.text if title_tag else "No title")
            image = image_tag["content"] if image_tag and image_tag.has_attr("content") else ""

            paragraphs = soup.find_all("p")
            text_content = " ".join(p.get_text() for p in paragraphs[:10])

            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Summarize this article in 3 crisp sentences:\n{text_content}"}
                ]
            }

            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
            res_json = response.json()

            if "choices" in res_json:
                summary = res_json["choices"][0]["message"]["content"].strip()
            else:
                st.error(f"Failed to generate summary for {url}: {res_json}")
                continue

            links = [a["href"] for a in soup.find_all("a", href=True) if a["href"].startswith("http")]
            quick_reads.extend(links[:3])
            recommended_reads.extend(links[3:6])

            summaries.append({
                "title": title,
                "image": image,
                "summary": summary,
                "url": url
            })

        except Exception as e:
            st.error(f"Failed to process {url}: {e}")

    if summaries:
        st.markdown("---")
        st.markdown("## ✨ Newsletter Preview")
        st.markdown("<div style='font-family:sans-serif; max-width:700px; margin:auto;'>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;'>Weekly Tech Digest</h1><hr>", unsafe_allow_html=True)

        st.markdown("<h2>📰 Top Stories</h2>", unsafe_allow_html=True)
        for article in summaries:
            st.markdown(f"""
                <div style='margin-bottom:30px;'>
                    <h3>{article['title']}</h3>
                    <img src='{article['image']}' alt='Image' style='width:100%; border-radius:10px;'>
                    <p>{article['summary']}</p>
                    <a href='{article['url']}' style='color:#007BFF;'>Continue Reading</a>
                </div>
            """, unsafe_allow_html=True)

        if quick_reads:
            st.markdown("<hr><h3>⚡ Quick Reads</h3><ul>", unsafe_allow_html=True)
            for link in quick_reads:
                st.markdown(f"<li><a href='{link}' target='_blank'>{link}</a></li>", unsafe_allow_html=True)
            st.markdown("</ul>", unsafe_allow_html=True)

        if recommended_reads:
            st.markdown("<hr><h3>📚 Recommended Reads</h3><ul>", unsafe_allow_html=True)
            for link in recommended_reads:
                st.markdown(f"<li><a href='{link}' target='_blank'>{link}</a></li>", unsafe_allow_html=True)
            st.markdown("</ul>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
