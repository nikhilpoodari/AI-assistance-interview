import streamlit as st
try:
    from streamlit_webrtc import webrtc_streamer
    from streamlit_webrtc import WebRtcMode
    _WEBRTC_AVAILABLE = True
except Exception:
    webrtc_streamer = None
    WebRtcMode = None
    _WEBRTC_AVAILABLE = False

def video_interview_ui(container):
    container.subheader("Candidate Recording")

    # If recording not started yet → show button
    if not st.session_state.get("video_started", False):
        if container.button("▶️ Start Recording"):
            st.session_state.video_started = True
            st.rerun()
        return None

    # Once started → show video recorder in RIGHT column
    stopped_now = False
    with container:
        if _WEBRTC_AVAILABLE:
            ctx = webrtc_streamer(
                key="interview_whole",
                mode=WebRtcMode.SENDRECV if WebRtcMode else None,
                media_stream_constraints={"video": True, "audio": True},
                async_processing=True
            )
            is_playing = bool(getattr(getattr(ctx, "state", None), "playing", False)) if ctx else False
            was_playing = st.session_state.get("webrtc_was_playing", False)
            if was_playing and not is_playing:
                stopped_now = True
            st.session_state.webrtc_was_playing = is_playing
            container.info("📹 Recording in progress… Answer confidently!" if is_playing else "🛑 Recording stopped.")
        else:
            container.warning("WebRTC components are unavailable. Please install dependencies or use a supported browser.")
            container.markdown("If recording isn't needed, you can still proceed with the interview questions.")

    return {"active": True, "stopped": stopped_now}
