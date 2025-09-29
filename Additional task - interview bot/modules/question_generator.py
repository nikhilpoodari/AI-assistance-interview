import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=groq_api_key) if groq_api_key else None

def _fallback_questions(resume_text: str):
    base = [
        "Tell me about yourself and your professional background.",
        "What are your strengths relevant to this role?",
        "Describe a challenging situation and how you handled it.",
        "Why do you want to work with us?",
        "Where do you see yourself in the next few years?",
    ]
    # If resume hints at skills, bias a bit
    lower = (resume_text or "").lower()
    if any(k in lower for k in ["python", "ml", "machine learning", "data"]):
        base[1] = "What technical strengths would you bring to a data/ML team?"
        base[2] = "Describe a data/ML project you delivered and its impact."
    return base

def generate_questions(resume_text: str):
    if not resume_text:
        return _fallback_questions(resume_text)

    if client is None:
        return _fallback_questions(resume_text)

    prompt = f"""
    Based on the following resume, generate 5 concise HR-style interview questions.
    Return them as a simple numbered list (1., 2., 3., ...), no extra text.

    Resume:
    {resume_text}
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        questions = []
        for line in content.split("\n"):
            q = line.strip().lstrip("-•").lstrip("0123456789. ")
            if q:
                questions.append(q)
        if not questions:
            return _fallback_questions(resume_text)
        return questions[:5]
    except Exception:
        return _fallback_questions(resume_text)
