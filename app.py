import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
import json

# Load API key from secrets
groq_api_key = st.secrets["GROQ_API_KEY"]
groq_api_url = "https://api.groq.com/openai/v1/chat/completions"

def fetch_article_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ' '.join(p.get_text() for p in paragraphs)
        return text.strip()
    except Exception as e:
        return f"Error fetching article: {e}"

def summarize_with_groq(text, prompt):
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        "temperature": 0.7
    }
    try:
        res = requests.post(groq_api_url, headers=headers, data=json.dumps(body))
        res.raise_for_status()
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {e}"

def format_newsletter(main_article, sub_articles, quick_reads, recommended_reads):
    html = f"""
    <div style="font-family:sans-serif; max-width:600px; margin:auto;">
      <h1 style="color:#333;">📰 Weekly Tech Digest</h1>

      <h2 style="color:#444;">{main_article['title']}</h2>
      <p>{main_article['summary']}</p>

      <h3 style="margin-top:2em; color:#666;">Other Top Stories</h3>
      {''.join(f'<p><b>{a["title"]}</b><br>{a["summary"]}</p>' for a in sub_articles)}

      <h3 style="margin-top:2em; color:#666;">Quick Reads</h3>
      <ul>
        {''.join(f'<li><a href="{r["url"]}" target="_blank">{r["title"]}</a></li>' for r in quick_reads)}
      </ul>

      <h3 style="margin-top:2em; color:#666;">Recommended Reads</h3>
      <ul>
        {''.join(f'<li><a href="{r["url"]}" target="_blank">{r["title"]}</a></li>' for r in recommended_reads)}
      </ul>
    </div>
    """
    return html

st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")
st.markdown("Paste article URLs below (one per line), then click Summarize.")

urls_input = st.text_area("Article URLs", height=200)

if st.button("Summarize"):
    urls = [url.strip() for url in urls_input.splitlines() if url.strip()]
    if not urls:
        st.warning("Please enter at least one URL.")
    else:
        summaries = []
        quick_reads = []
        recommended_reads = []

        for i, url in enumerate(urls):
            st.write(f"🔍 Fetching: {url}")
            article_text = fetch_article_text(url)

            if "Error" in article_text:
                st.error(article_text)
                continue

            prompt = """
            You are a newsletter editor. Summarize the following news article in 2-3 crisp, engaging sentences suitable for a tech-savvy audience. Include key takeaways, and maintain a friendly, concise tone. If it's the first article, treat it as the main headline.
            """
            summary = summarize_with_groq(article_text, prompt)

            # Create fallback title if Groq failed
            try:
                title = article_text.split('.')[0][:100] + '...'
            except:
                title = "Untitled Article"

            summaries.append({
                "title": f"Article {i+1}" if not summary else title,
                "summary": summary,
                "url": url
            })

        if summaries:
            main_article = summaries[0]
            sub_articles = summaries[1:3]
            quick_reads = summaries[3:5] if len(summaries) > 3 else []
            recommended_reads = summaries[5:] if len(summaries) > 5 else []

            newsletter_html = format_newsletter(main_article, sub_articles, quick_reads, recommended_reads)
            st.markdown("""### 📄 Newsletter Preview (HTML):""")
            st.components.v1.html(newsletter_html, height=800, scrolling=True)

            with st.expander("📋 View Raw HTML"):
                st.code(newsletter_html, language='html')
