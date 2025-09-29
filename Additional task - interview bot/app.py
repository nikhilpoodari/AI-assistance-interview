import streamlit as st
import time
import base64
import tempfile
from gtts import gTTS
from modules.auth import create_user, verify_user

from modules.resume_parser import parse_resume
from modules.question_generator import generate_questions
from modules.faq_bot import faq_chatbot
from modules.video_recorder import video_interview_ui

st.set_page_config(layout="wide", page_title="Interview Bot", page_icon="🤖")

# -------------------- Theming & Global Styles --------------------
st.markdown(
    """
    <style>
      .main {
        background: radial-gradient(1200px 800px at 10% 10%, rgba(76,175,80,0.08), transparent 40%),
                    radial-gradient(1200px 800px at 90% 20%, rgba(33,150,243,0.08), transparent 40%);
      }
      .app-card {
        background: rgba(255,255,255,0.75);
        border: 1px solid rgba(0,0,0,0.06);
        border-radius: 14px;
        padding: 18px 18px 8px 18px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        backdrop-filter: blur(6px);
      }
      .timer {
        font-weight: 700; font-size: 18px;
        background: #111; color: #fff; display: inline-block; padding: 6px 12px; border-radius: 10px;
      }
      /* Sidebar enhancements */
      section[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #1f2937, #111827);
        border: 1px solid rgba(255,255,255,0.08);
      }
      section[data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #10b981, #059669);
        box-shadow: 0 8px 18px rgba(16,185,129,.35);
      }
      section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2, 
      section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: #e5e7eb;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- Initialize Session --------------------
if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "timer" not in st.session_state:
    st.session_state.timer = 60
if "video_started" not in st.session_state:
    st.session_state.video_started = False
if "last_spoken_index" not in st.session_state:
    st.session_state.last_spoken_index = -1
if "waiting_for_audio" not in st.session_state:
    st.session_state.waiting_for_audio = False
if "page" not in st.session_state:
    st.session_state.page = "Upload Resume"
if "started" not in st.session_state:
    st.session_state.started = False
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "login_prompt" not in st.session_state:
    st.session_state.login_prompt = False

# Title/caption visible only after successful login
if st.session_state.get("authenticated", False):
    st.title("🤖 Interview Bot")
    st.caption("AI-powered resume-based interview practice with video recording and HR FAQ bot")

# -------------------- Landing Page (shown until Start Now) --------------------
if not st.session_state.started:
    # Hide sidebar visually on landing
    st.markdown(
        """
        <style>
          section[data-testid="stSidebar"] {display: none;} 
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header: logo left, Sign Up right
    c1, c2 = st.columns([3,1])
    with c1:
        st.markdown("### interview.co")
    with c2:
        if st.button("Sign Up", key="landing_signup"):
            st.session_state.started = True
            st.session_state.page = "Sign Up"
            st.rerun()

    st.markdown("---")
    hc1, hc2 = st.columns([1.2,1])
    with hc1:
        st.markdown("## Mock Interviews to Mastery. Prepare, practice and own the real one.")
        st.write("AI-based practice to help you be ready for the real interview.")
        if st.button("Start Now!", type="primary"):
            st.session_state.started = True
            st.session_state.page = "Sign Up"
            st.session_state.login_prompt = True
            st.rerun()
    with hc2:
        st.image("https://images.unsplash.com/photo-1522199710521-72d69614c702?q=80&w=1200&auto=format&fit=crop", use_column_width=True)

    st.stop()

# -------------------- Custom Sidebar Menu --------------------
sidebar_style = """
    <style>
        .stButton > button {
            width: 100%;
            background-color: #262730;
            color: white;
            padding: 10px;
            border-radius: 10px;
            text-align: left;
            font-size: 16px;
            transition: all 0.3s ease-in-out;
            border: none;
            margin-bottom: 10px;
        }
        .stButton > button:hover {
            background-color: #4CAF50;
            transform: scale(1.05);
            box-shadow: 0px 0px 10px rgba(76, 175, 80, 0.8);
        }
        .active-btn {
            background-color: #4CAF50 !important;
            font-weight: bold;
        }
    </style>
"""
st.markdown(sidebar_style, unsafe_allow_html=True)

if st.session_state.started and st.session_state.authenticated:
    with st.sidebar:
        st.markdown("## Explore")

        if st.button("📄 Upload Resume", key="resume_btn"):
            st.session_state.page = "Upload Resume"
        if st.button("🎥 Interview", key="interview_btn"):
            st.session_state.page = "Interview"
        if st.button("💬 FAQ Bot", key="faq_btn"):
            st.session_state.page = "FAQ Bot"

# Highlight active page
active_page = st.session_state.page
js_highlight = f"""
    <script>
    var buttons = window.parent.document.querySelectorAll('.stButton > button');
    buttons.forEach(btn => {{
        if(btn.innerText.includes("{active_page.split()[0]}")) {{
            btn.classList.add("active-btn");
        }}
    }});
    </script>
"""
if st.session_state.started and st.session_state.authenticated:
    st.markdown(js_highlight, unsafe_allow_html=True)

# -------------------- Helper: Speak Question --------------------
def speak_text(text):
    tts = gTTS(text=text, lang="en")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tts.save(tmp.name)
        audio_file = tmp.name

    with open(audio_file, "rb") as f:
        audio_bytes = f.read()
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    return audio_html

# -------------------- Resume Upload --------------------
if st.session_state.page == "Upload Resume":
    st.header("📄 Upload Resume")
    with st.container():
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"])
        if uploaded_file:
            resume_text = parse_resume(uploaded_file)
            st.session_state.resume_text = resume_text
            st.success("Resume uploaded & parsed successfully!")
            st.text_area("Extracted Resume Text", resume_text, height=260)

            col_a, col_b = st.columns([1,1])
            with col_a:
                if st.button("✨ Generate Questions"):
                    with st.spinner("Generating interview questions..."):
                        st.session_state.questions = generate_questions(resume_text)
                        st.session_state.current_index = 0
                        st.session_state.timer = 60
                        st.session_state.video_started = False
                        st.session_state.last_spoken_index = -1
                        st.session_state.waiting_for_audio = True
                    st.success("Interview setup completed! Open the Interview tab.")
            with col_b:
                st.metric("Questions ready", len(st.session_state.questions))
        else:
            st.info("Upload your resume to generate personalized interview questions.")
        st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Interview --------------------
elif st.session_state.page == "Interview":
    st.header("🎥 AI Interview")

    if not st.session_state.questions:
        st.warning("⚠️ Please upload a resume and start interview first.")
    else:
        col1, col2 = st.columns([1.2, 1])
        # Top-right Skip button
        with col1:
            top_right = st.container()
            with top_right:
                st.markdown(
                    "<div style='display:flex; justify-content:flex-end; margin-top:-24px;'>" 
                    "<span></span></div>",
                    unsafe_allow_html=True,
                )
                if st.button("⏭️ Skip Interview", key="skip_top_right"):
                    st.session_state.page = "FAQ Bot"
                    st.session_state.questions = []
                    st.session_state.current_index = 0
                    st.session_state.timer = 60
                    st.session_state.video_started = False
                    st.session_state.last_spoken_index = -1
                    st.session_state.waiting_for_audio = False
                    st.rerun()

        rec_info = video_interview_ui(col2)

        if rec_info and rec_info.get("active"):
            with col1:
                st.subheader(f"Question {st.session_state.current_index + 1}")
                current_q = st.session_state.questions[st.session_state.current_index]
                st.write(current_q)

                # --- Speak question when waiting_for_audio is True ---
                if st.session_state.waiting_for_audio:
                    audio_html = speak_text(current_q)
                    st.markdown(audio_html, unsafe_allow_html=True)
                    st.info("🔊 AI is reading the question… Please listen.")
                    st.session_state.waiting_for_audio = False
                    st.session_state.last_spoken_index = st.session_state.current_index
                    st.stop()

                # If recording just stopped, move to next question immediately
                if rec_info.get("stopped"):
                    if st.session_state.current_index < len(st.session_state.questions) - 1:
                        st.session_state.current_index += 1
                        st.session_state.timer = 60
                        st.session_state.waiting_for_audio = True
                        st.rerun()
                    else:
                        st.success("✅ You have completed all questions!")

                # --- Timer logic (after question audio finishes) ---
                timer_placeholder = st.empty()
                if st.session_state.timer > 0:
                    timer_placeholder.markdown(f"<span class='timer'>⏰ {st.session_state.timer}s</span>", unsafe_allow_html=True)
                    st.session_state.timer -= 1
                    time.sleep(1)
                    st.rerun()
                else:
                    timer_placeholder.markdown("⏰ Time's up!")

                # Navigation buttons
                progress = (st.session_state.current_index + 1) / max(1, len(st.session_state.questions))
                st.progress(progress)

                # Action buttons row
                c1, c2, c3 = st.columns([1,1,1])
                if c1.button("➡️ Next"):
                    if st.session_state.current_index < len(st.session_state.questions) - 1:
                        st.session_state.current_index += 1
                        st.session_state.timer = 60
                        st.session_state.waiting_for_audio = True   # ✅ each new Q will be spoken
                        st.rerun()
                    else:
                        st.success("✅ You have completed all questions!")
                if c2.button("⏭️ Skip Interview"):
                    st.session_state.page = "FAQ Bot"
                    st.session_state.questions = []
                    st.session_state.current_index = 0
                    st.session_state.timer = 60
                    st.session_state.video_started = False
                    st.session_state.last_spoken_index = -1
                    st.session_state.waiting_for_audio = False
                    st.rerun()
                if c3.button("🏁 Finish Test"):
                    st.success("🎉 Interview finished! Redirecting to FAQ Bot…")
                    st.session_state.questions = []
                    st.session_state.current_index = 0
                    st.session_state.timer = 60
                    st.session_state.resume_text = ""
                    st.session_state.video_started = False
                    st.session_state.last_spoken_index = -1
                    st.session_state.waiting_for_audio = False
                    st.session_state.page = "FAQ Bot"
                    st.rerun()

# -------------------- FAQ Bot --------------------
elif st.session_state.page == "FAQ Bot":
    st.header("💬 HR FAQ Chatbot")
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    faq_chatbot()
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Auth: Sign Up --------------------
elif st.session_state.page == "Sign Up":
    # Hide sidebar for auth pages
    st.markdown(
        """
        <style>
          section[data-testid=\"stSidebar\"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### interview.co")
    left, right = st.columns([1,1])
    with right:
        st.subheader("Create an Account")
        with st.form("signup_form"):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            pw = st.text_input("Password", type="password")
            pw2 = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Sign Up")
        if submitted:
            if pw != pw2:
                st.error("Passwords do not match.")
            elif not full_name or not email or not pw:
                st.error("All fields are required.")
            else:
                ok = create_user(full_name, email, pw)
                if ok:
                    st.success("Account created! Redirecting to login…")
                    st.session_state.page = "Login"
                    st.rerun()
                else:
                    st.error("Email already registered. Try logging in.")
        st.markdown(
            """
            <div style="margin-top: 18px; font-size: 16px;">
                Already have an account?
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Login", key="goto_login_link"):
            st.session_state.page = "Login"
            st.rerun()
          
    with left:
        st.image("https://images.unsplash.com/photo-1551836022-4c4c79ecde51?q=80&w=900&auto=format&fit=crop", use_column_width=True)

# -------------------- Auth: Login --------------------
elif st.session_state.page == "Login":
    # Hide sidebar for auth pages
    st.markdown(
        """
        <style>
          section[data-testid=\"stSidebar\"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### interview.co")
    left, right = st.columns([1,1])
    with right:
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email Address")
            pw = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
        if submitted:
            if verify_user(email, pw):
                st.success("Login successful. Redirecting…")
                st.session_state.authenticated = True
                st.session_state.page = "Upload Resume"
                st.rerun()
            else:
                st.error("Invalid credentials.")
    with left:
        st.image("https://images.unsplash.com/photo-1515187029135-18ee286d815b?q=80&w=900&auto=format&fit=crop", use_column_width=True)
