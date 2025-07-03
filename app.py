import streamlit as st
import requests
from urllib.parse import urlparse
from groq import Groq  # Ensure your Groq client is configured correctly

st.set_page_config(page_title="Tech Newsletter Generator", layout="wide")

st.title("📰 Advanced Tech Newsletter Generator")
st.markdown("Paste your article URLs (one per line), then click Generate.")

input_urls = st.text_area("Input URLs", height=200)

def fetch_article_data(url):
    try:
        # This should call your Groq LLM API for article processing
        response = Groq.chat.completions.create(
            model="llama3-70b-8192",  # Use supported Groq model
            messages=[
                {"role": "user", "content": f"Extract the headline, summary (6 lines max), and featured image from this article: {url}"}
            ]
        )
        result = response.choices[0].message.content
        return result
    except Exception as e:
        return None

def search_related_articles(topic, domain):
    try:
        prompt = f"""
        Give me 3 related articles on the topic: "{topic}" from {domain}. For each article, give:
        - Title
        - URL
        - One-line summary
        """
        response = Groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except:
        return "No related articles found."

def render_article(title, image, summary, url, related_articles):
    st.markdown(f"## {title}")
    if image:
        st.image(image, use_container_width=True)
    st.markdown(summary)
    st.markdown(f"[Continue Reading →]({url})")

    if related_articles:
        st.markdown("**Quick Reads from this article**")
        st.markdown(related_articles)
    st.markdown("---")

def fetch_intro(urls):
    topics = ["Microsoft cancels games", "Google Photos upgrades", "Apple's Invasion returns"]
    return "Hi there! This week’s newsletter covers key updates: " + ", ".join(topics) + "."

if st.button("Generate"):
    urls = [u.strip() for u in input_urls.splitlines() if u.strip()]

    if not urls:
        st.error("Please paste at least one article URL.")
    else:
        intro = fetch_intro(urls)
        st.markdown("## Intro")
        st.markdown(intro)

        for u in urls:
            st.markdown(f"🔍 Fetching: {u}")
            try:
                data = fetch_article_data(u)
                if not data:
                    st.error(f"Failed to process {u}")
                    continue

                # Basic parsing (replace with JSON parsing if returned in JSON)
                title = data.split("\n")[0].strip()
                image = ""  # extract actual image if included
                summary = "\n".join(data.split("\n")[1:]).strip()
                domain = urlparse(u).netloc

                related = search_related_articles(title, domain)

                render_article(title, image, summary, u, related)
            except Exception as e:
                st.error(f"Error with {u}: {e}")

        # Final section: Recommended Reads
        st.markdown("## 📚 Recommended Reads")
        rec_prompt = "Based on the topics covered in this newsletter, recommend 3 similar tech articles from The Verge. Include title, 1-line summary, and link."
        try:
            recs = Groq.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": rec_prompt}]
            )
            st.markdown(recs.choices[0].message.content)
        except:
            st.markdown("No recommended reads available.")
