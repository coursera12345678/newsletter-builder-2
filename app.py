import streamlit as st
import requests
from bs4 import BeautifulSoup

# Load Groq API key
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-8b-8192"  # Working Groq model

# ----------- Functions -----------

def extract_article_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs)
        return text[:8000]  # truncate to stay safe
    except Exception as e:
        return f"⚠️ Error fetching article: {e}"

def get_groq_summary(text, prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful newsletter assistant."},
            {"role": "user", "content": prompt + "\n\n" + text}
        ]
    }
    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Error: {e}"

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
            prompt = "Summarize this as a main newsletter story. Make it engaging, with a short headline and a paragraph summary."
            summary = get_groq_summary(article_text, prompt)
            sections["main_story"] = summary

        elif idx < 3:
            prompt = "Summarize this as a short sub-story for a newsletter. Include a headline and a short paragraph."
            summary = get_groq_summary(article_text, prompt)
            sections["other_stories"].append(summary)

        elif idx < 6:
            prompt = "Summarize this article in one catchy sentence for a quick read section."
            summary = get_groq_summary(article_text, prompt)
            sections["quick_reads"].append(f"- {summary}")

        else:
            sections["recommended_reads"].append(f"- [{url}]({url})")

    return sections

def render_newsletter(sections):
    st.markdown("## 🗞️ Your Auto-Generated Newsletter", unsafe_allow_html=True)

    st.markdown("### 📰 Main Story")
    st.markdown(sections["main_story"])

    st.markdown("### 📚 Other Stories")
    for story in sections["other_stories"]:
        st.markdown(story)

    st.markdown("### ⚡ Quick Reads")
    for quick in sections["quick_reads"]:
        st.markdown(quick)

    st.markdown("### ✨ Recommended Reads")
    for rec in sections["recommended_reads"]:
        st.markdown(rec)
    
    st.markdown("---")
    st.markdown("*Generated with ❤️ using Groq + Streamlit.*")

# ----------- Streamlit UI -----------

st.title("📰 Auto Newsletter Generator (Groq + Streamlit)")
st.write("Paste article URLs below (one per line). First one will be treated as the **Main Story**.")

urls_input = st.text_area("Article URLs", height=200)
if st.button("Generate Newsletter"):
    urls = [url.strip() for url in urls_input.strip().split("\n") if url.strip()]
    if len(urls) < 1:
        st.warning("Please enter at least one article URL.")
    else:
        with st.spinner("Generating newsletter..."):
            sections = generate_newsletter(urls)
            render_newsletter(sections)
