import streamlit as st
import os
from functools import lru_cache
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_groq import ChatGroq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv


@lru_cache(maxsize=1)
def _load_tfidf_index():
    # Always resolve absolute path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    faq_path = os.path.join(base_dir, "..", "data", "hr_faq.txt")

    if not os.path.exists(faq_path):
        return None

    # Load HR FAQ text file
    loader = TextLoader(faq_path, encoding="utf-8")
    docs = loader.load()

    # Split into chunks
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    texts = [c.page_content for c in chunks]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(texts)
    return {"texts": texts, "vectorizer": vectorizer, "matrix": matrix}


def load_faq_bot():
    # Ensure .env is loaded so GROQ_API_KEY is available
    load_dotenv()
    tfidf = _load_tfidf_index()
    if tfidf is None:
        st.error("⚠️ Missing FAQ data file at `data/hr_faq.txt`. Please add it and reload.")
        return None

    # Validate Groq API key from environment
    if not os.getenv("GROQ_API_KEY"):
        st.error("GROQ_API_KEY is not set. Please add it to your .env file.")
        return None

    llm = ChatGroq(model="openai/gpt-oss-20b")
    return {"llm": llm, "tfidf": tfidf}


qa_ctx = None


def faq_chatbot():
    global qa_ctx
    if qa_ctx is None:
        with st.spinner("Loading FAQ bot..."):
            qa_ctx = load_faq_bot()
        if qa_ctx is None:
            return

    user_q = st.text_input("Ask me an HR question:")
    if st.button("Submit") and user_q:
        try:
            with st.spinner("Thinking..."):
                texts = qa_ctx["tfidf"]["texts"]
                vectorizer = qa_ctx["tfidf"]["vectorizer"]
                matrix = qa_ctx["tfidf"]["matrix"]
                q_vec = vectorizer.transform([user_q])
                sims = cosine_similarity(q_vec, matrix).flatten()
                top_idx = sims.argsort()[::-1][:5]
                context = "\n\n".join(texts[i] for i in top_idx if sims[i] > 0)
                prompt = (
                    "You are an HR FAQ assistant. Answer the user's question strictly using the provided FAQ context. "
                    "If the answer is not in the context, say you don't know. Be concise.\n\n"
                    f"Context:\n{context}\n\nQuestion: {user_q}\nAnswer:"
                )
                ai = qa_ctx["llm"].invoke(prompt)
                answer = getattr(ai, "content", None) or str(ai)
            if not answer.strip():
                st.info("I couldn't find an answer in the FAQ. Try rephrasing your question.")
            else:
                st.write("**Answer:**", answer)
        except Exception as e:
            st.error(f"Unexpected error: {e}")
