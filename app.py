import streamlit as st
import requests
from bs4 import BeautifulSoup
import os

# --- Configuration ---
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# --- Functions ---
def extract_article_text(url):
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text() for p in paragraphs])
        return text[:8000]  # Groq input size limit
    except:
        return ""

def get_groq_summary(text, prompt):
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful newsletter assistant."},
            {"role": "user", "content": f"{prompt}\n\n{text}"}
        ]
    }
    try:
        res = requests.post(GROQ_URL, headers=HEADERS, json=payload)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"⚠️ Error generating summary: {e}"

def generate_newsletter(urls):
    sections = {
        "main_story": "",
        "other_stories": [],
        "quick_reads": [],
        "recommended_reads": []
    }

    for idx, url in enumerate(urls):
        article_text = extract_article_text(url)

        if idx == 0:
            prompt = "Summarize this as a main newsletter story. Start with a short engaging headline, followed by a paragraph summary."
            summary = get_groq_summary(article_text, prompt)
            sections["main_story"] = summary

        elif idx < 3:
            prompt = "Summarize this as a short sub-story for a newsletter. Start with a short headline, followed by 2-3 lines of summary."
            summary = get_groq_summary(article_text, prompt)
            sections["other_stories"].append(summary)

        elif idx < 6:
            prompt = "Summarize this article in one catchy sentence for a quick read section."
            summary = get_groq_summary(article_text, prompt)
            sections["quick_reads"].append(f"- {summary} [Read more]({url})")

        else:
            sections["recommended_reads"].append(f"- [Read here]({url})")

    return sections

# --- Streamlit App ---
st.set_page_config(page_title="Auto Newsletter Generator", layout="wide")
st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")

urls_input = st.text_area("Paste article URLs below (one per line), then click Summarize.")

if st.button("Summarize"):
    urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
    if urls:
        with st.spinner("Generating newsletter..."):
            newsletter = generate_newsletter(urls)

        # --- Display Styled Output ---
        st.markdown("""
        <style>
            .main-headline { font-size: 28px; font-weight: bold; margin-bottom: 0.5em; color: #222; }
            .subheadline { font-size: 20px; font-weight: bold; margin-top: 1em; color: #444; }
            .paragraph { font-size: 16px; color: #333; line-height: 1.6; margin-bottom: 1em; }
            ul { padding-left: 1.2em; }
            li { margin-bottom: 0.5em; }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="main-headline">{newsletter['main_story'].splitlines()[0]}</div>
        <div class="paragraph">{' '.join(newsletter['main_story'].splitlines()[1:])}</div>

        <div class="subheadline">Other Top Stories</div>
        {''.join([f'<div class="paragraph">{story}</div>' for story in newsletter['other_stories']])}

        <div class="subheadline">Quick Reads</div>
        <ul>
        {''.join([f'<li>{qr}</li>' for qr in newsletter['quick_reads']])}
        </ul>

        <div class="subheadline">Recommended Reads</div>
        <ul>
        {''.join([f'<li>{rec}</li>' for rec in newsletter['recommended_reads']])}
        </ul>
        """, unsafe_allow_html=True)
    else:
        st.warning("Please enter at least one URL.")
