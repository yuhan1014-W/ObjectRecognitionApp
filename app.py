# pyright: reportMissingImports=false
import io
import os

import requests
import streamlit as st
from gtts import gTTS
from gtts.tts import gTTSError
from PIL import Image


st.set_page_config(page_title="SnapIt | Visual Dictionary", page_icon="🌍", layout="centered")
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(ellipse at 8% 0%, rgba(133, 220, 199, .20), transparent 34rem),
            #f6f8f6;
    }
    .block-container {
        max-width: 850px;
        padding-top: 3rem;
        padding-bottom: 4rem;
    }
    .hero {
        padding: 1.6rem 0 1.2rem;
    }
    .eyebrow {
        color: #16836e;
        font-size: .78rem;
        font-weight: 700;
        letter-spacing: .14em;
        text-transform: uppercase;
    }
    .hero h1 {
        color: #172c29;
        font-size: clamp(2.5rem, 8vw, 4.3rem);
        letter-spacing: -.055em;
        line-height: 1;
        margin: .65rem 0;
    }
    .hero p {
        color: #5e706b;
        font-size: 1.08rem;
        max-width: 38rem;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, .82);
        border-color: #e2eae6;
        border-radius: 20px;
    }
    [data-testid="stAudio"] {
        min-width: 130px;
    }
    </style>
    <div class="hero">
      <div class="eyebrow">A little more curious</div>
      <h1>SnapIt</h1>
      <p>Point your camera at something new. Get its name, meaning, and story in two languages.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container(border=True):
    st.markdown("#### 1. Choose a language")
    target_language = st.selectbox(
        "Translate the results into",
        ["Chinese", "Korean", "Spanish", "French", "Japanese", "German", "Italian"],
        label_visibility="collapsed",
    )

    st.markdown("#### 2. Add a photo")
    input_option = st.radio(
        "Choose how to add your photo",
        ["📷 Take a photo", "🖼️ Upload an image"],
        horizontal=True,
        label_visibility="collapsed",
    )

    uploaded_file = None
    if input_option == "📷 Take a photo":
        uploaded_file = st.camera_input("Take a picture of an object")
    else:
        uploaded_file = st.file_uploader(
            "Choose an image from your device",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed",
        )

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Your image", use_container_width=True)

    if uploaded_file is not None and st.button(
        "✨ Discover this object",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner("Looking closely…"):
            try:
                image = Image.open(uploaded_file)
                image.thumbnail((1024, 1024))
                image = image.convert("RGB")

                image_buffer = io.BytesIO()
                image.save(image_buffer, format="JPEG", quality=85)
                files = {
                    "image": (
                        "upload.jpg",
                        image_buffer.getvalue(),
                        "image/jpeg",
                    )
                }
                response = requests.post(
                    os.environ.get(
                        "SNAPIT_API_URL",
                        "https://snapit-pcai.onrender.com/analyze",
                    ),
                    files=files,
                    data={"language": target_language},
                    timeout=120,
                )

                if response.ok:
                    result = response.json()
                    if not isinstance(result, dict):
                        st.error("The analysis service returned an unexpected response.")
                    else:
                        st.session_state["last_result"] = result
                        st.session_state["last_language"] = target_language
                else:
                    try:
                        error = response.json().get("error", "Unknown error")
                    except requests.exceptions.JSONDecodeError:
                        error = response.text or "Unknown error"
                    if isinstance(error, dict):
                        error = error.get("message", error)
                    st.error(f"Analysis failed: {error}")
            except requests.exceptions.Timeout:
                st.error("The analysis request timed out. Please try again.")
            except requests.exceptions.ConnectionError as exc:
                st.error(f"Could not connect to the analysis service: {exc}")
            except requests.exceptions.RequestException as exc:
                st.error(f"Could not complete the analysis request: {exc}")
            except (OSError, ValueError) as exc:
                st.error(f"Could not read this image: {exc}")

if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    result_language = st.session_state.get("last_language", target_language)
    language_codes = {
        "Chinese": "zh-CN",
        "Korean": "ko",
        "Spanish": "es",
        "French": "fr",
        "Japanese": "ja",
        "German": "de",
        "Italian": "it",
    }

    st.markdown("")
    st.markdown("### Your discovery")
    st.caption(f"English · {result_language}")

    with st.container(border=True):
        english_column, translated_column = st.columns([4, 1])
        with english_column:
            st.markdown("**🇺🇸 English name**")
            st.subheader(result.get("english_name", "N/A"))
        with translated_column:
            try:
                audio = io.BytesIO()
                gTTS(text=result.get("english_name", ""), lang="en").write_to_fp(audio)
                st.audio(audio.getvalue(), format="audio/mp3")
            except (gTTSError, OSError, RuntimeError, ValueError) as exc:
                st.caption(f"English audio unavailable: {exc}")

        st.divider()
        translated_name_column, translated_audio_column = st.columns([4, 1])
        with translated_name_column:
            st.markdown(f"**🌍 {result_language} name**")
            st.subheader(result.get("translated_name", "N/A"))
        with translated_audio_column:
            try:
                audio = io.BytesIO()
                gTTS(
                    text=result.get("translated_name", ""),
                    lang=language_codes.get(result_language, "es"),
                ).write_to_fp(audio)
                st.audio(audio.getvalue(), format="audio/mp3")
            except (gTTSError, OSError, RuntimeError, ValueError) as exc:
                st.caption(f"Translated audio unavailable: {exc}")

    definition_column, background_column = st.columns(2)
    with definition_column:
        with st.container(border=True):
            st.markdown("#### 📖 What it is")
            st.markdown("**English**")
            st.write(result.get("english_definition", "N/A"))
            st.markdown(f"**{result_language}**")
            st.write(result.get("translated_definition", "N/A"))

    with background_column:
        with st.container(border=True):
            st.markdown("#### 💡 Good to know")
            st.markdown("**English**")
            st.write(result.get("english_background", "N/A"))
            st.markdown(f"**{result_language}**")
            st.write(result.get("translated_background", "N/A"))

    if st.button("↻ Scan another object", use_container_width=True):
        del st.session_state["last_result"]
        st.session_state.pop("last_language", None)
        st.rerun()
