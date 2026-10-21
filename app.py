import streamlit as st
import requests
from gtts import gTTS

st.set_page_config(page_title="SnapIt AI", page_icon="🌍", layout="centered")

st.title("SnapIt: Visual Dictionary")
st.write("Snap a photo with your camera or upload an image of an object to identify and learn more about it!")

# Target Language Selection
target_language = st.selectbox(
    "Select Target Language:",
    ["Chinese", "Korean", "Spanish", "French", "Japanese", "German", "Italian"]
)

st.markdown("---")

# Input Method Choice
input_option = st.radio(
    "Choose Input Method:", 
    ["📷 Use Built-in Camera", "🖼️ Upload from Device Library"],
    horizontal=True
)

uploaded_file = None

if "Camera" in input_option:
    uploaded_file = st.camera_input("Take a picture")
else:
    uploaded_file = st.file_uploader("Upload an image from your device:", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Selected Image Preview", width='stretch')

# Analyze Button & Backend Request
if uploaded_file is not None:
    if st.button("🚀 Analyze Object", type="primary", use_container_width=True):
        with st.spinner("Analyzing image with Gemini (this may take a few seconds)..."):
            try:
                url = "http://127.0.0.1:5000/analyze"
                files = {
                    "image": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type or "application/octet-stream",
                    )
                }
                data = {"language": target_language}

                response = requests.post(url, files=files, data=data, timeout=120)

                if response.status_code == 200:
                    # Expecting structured JSON back from server.py
                    result_json = response.json()
                    st.session_state['last_result'] = result_json
                else:
                    try:
                        error = response.json().get("error", "Unknown error")
                    except requests.exceptions.JSONDecodeError:
                        error = response.text or "Unknown error"
                    if isinstance(error, dict):
                        error = error.get("message", error)
                    st.error(f"Server error: {error}")

            except requests.exceptions.Timeout:
                st.error("The analysis request timed out. Please try again.")
            except requests.exceptions.ConnectionError as e:
                st.error(f"Could not connect to backend server: {e}")

# If we have a stored result, display it and provide a reset button
if 'last_result' in st.session_state:
    st.success("Analysis Complete!")
    st.markdown("### 📋 Results:")
    
    res = st.session_state['last_result']
    
    # Map target language to gTTS language codes
    lang_code_map = {
        "Chinese": "zh-CN", "Korean": "ko", "Spanish": "es", 
        "French": "fr", "Japanese": "ja", "German": "de", "Italian": "it"
    }
    selected_lang_code = lang_code_map.get(target_language, "es")

    st.markdown("---")

    # --- English Name & Audio Row ---
    eng_col1, eng_col2 = st.columns([4, 1])
    with eng_col1:
        st.markdown(f"**🇺🇸 English Name:** {res.get('english_name', 'N/A')}")
    with eng_col2:
        try:
            tts_eng = gTTS(text=res.get('english_name', ''), lang='en')
            audio_path_eng = "output_eng.mp3"
            tts_eng.save(audio_path_eng)
            st.audio(audio_path_eng, format="audio/mp3")
        except Exception:
            pass

    # --- Translated Name & Audio Row ---
    trans_col1, trans_col2 = st.columns([4, 1])
    with trans_col1:
        st.markdown(f"**🌍 {target_language} Name:** {res.get('translated_name', 'N/A')}")
    with trans_col2:
        try:
            tts_trans = gTTS(text=res.get('translated_name', ''), lang=selected_lang_code)
            audio_path_trans = "output_trans.mp3"
            tts_trans.save(audio_path_trans)
            st.audio(audio_path_trans, format="audio/mp3")
        except Exception:
            pass

    st.markdown("---")

    # --- Definitions Section ---
    st.markdown("#### 📖 Definitions")
    st.markdown(f"**English:** {res.get('english_definition', 'N/A')}")
    st.markdown(f"**{target_language}:** {res.get('translated_definition', 'N/A')}")

    st.markdown("---")

    # --- Background Info Section ---
    st.markdown("#### 💡 Learn more about it!")
    st.markdown(f"**English:** {res.get('english_background', 'N/A')}")
    st.markdown(f"**{target_language}:** {res.get('translated_background', 'N/A')}")

    st.markdown("---")
    
    # 🔄 Reset Button to take another photo
    if st.button("🔄 Scan Another Item", type="secondary", use_container_width=True):
        del st.session_state['last_result']
        st.rerun()