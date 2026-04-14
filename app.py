import streamlit as st
import whisper
import srt
from datetime import timedelta
import tempfile
import re

st.set_page_config(page_title="AI Subtitle Sync Tool", layout="centered")

st.title("🎬 AI Subtitle Sync Tool")

# ✅ Load Whisper model once
@st.cache_resource
def load_model():
    return whisper.load_model("tiny")


# ✅ Arabic cleaning
def clean_arabic_text(text):
    text = text.strip()

    # Remove dot and comma at end
    text = re.sub(r'[.,،]+$', '', text)

    # Convert names → (Name)
    text = re.sub(r'^([^\s:]+):', r'(\1)', text)

    return text


# ✅ Convert text → SRT
def text_to_srt(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    subs = []

    for i, line in enumerate(lines):
        subs.append(
            srt.Subtitle(
                index=i + 1,
                start=timedelta(seconds=i * 2),
                end=timedelta(seconds=(i + 1) * 2),
                content=line
            )
        )

    return subs


# 🎧 Upload audio
audio_file = st.file_uploader("🎧 Upload Audio/Video", type=["mp4", "mp3", "wav"])

st.divider()

# 📝 Choose input method
input_mode = st.radio(
    "Choose subtitle input:",
    ["Upload SRT/TXT file", "Paste text directly"]
)

subtitle_file = None
text_input = None

if input_mode == "Upload SRT/TXT file":
    subtitle_file = st.file_uploader("📄 Upload SRT or TXT", type=["srt", "txt"])
else:
    text_input = st.text_area("✍️ Paste your Arabic text here:", height=200)

st.divider()

# 🚀 Sync button
if st.button("🚀 Sync Subtitles"):

    if not audio_file:
        st.error("Please upload audio/video")
    elif not subtitle_file and not text_input:
        st.error("Please provide subtitles (file or text)")
    else:

        st.write("Preparing files...")

        # Save audio
        with tempfile.NamedTemporaryFile(delete=False) as tmp_audio:
            tmp_audio.write(audio_file.read())
            audio_path = tmp_audio.name

        # Load model
        model = load_model()

        # Transcribe
        with st.spinner("Transcribing audio... ⏳"):
            result = model.transcribe(audio_path)

        segments = result["segments"]

        # 🔹 Load subtitles
        if subtitle_file:
            content = subtitle_file.read().decode("utf-8")

            if subtitle_file.name.endswith(".srt"):
                subs = list(srt.parse(content))
            else:
                subs = text_to_srt(content)

        else:
            subs = text_to_srt(text_input)

        # 🔹 Process subtitles
        for i, sub in enumerate(subs):

            # Clean Arabic
            sub.content = clean_arabic_text(sub.content)

            # Sync timing
            if i < len(segments):
                sub.start = timedelta(seconds=segments[i]["start"])
                sub.end = timedelta(seconds=segments[i]["end"])

        # Output SRT
        output = srt.compose(subs)

        st.success("✅ Done!")
        st.download_button("⬇️ Download SRT", output, file_name="synced.srt")
