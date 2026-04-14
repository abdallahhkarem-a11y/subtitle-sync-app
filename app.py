import streamlit as st
import whisper
import srt
from datetime import timedelta
import tempfile
import re

st.title("AI Subtitle Sync Tool")

# ✅ Load Whisper model once
@st.cache_resource
def load_model():
    return whisper.load_model("tiny")


# ✅ Arabic cleaning
def clean_arabic_text(text):
    text = text.strip()

    # Remove dot and comma at end
    text = re.sub(r'[.,،]+$', '', text)

    # Names → (Name)
    text = re.sub(r'^([^\s:]+):', r'(\1)', text)

    return text


# ✅ Convert TXT → SRT
def text_to_srt(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    subs = []

    for i, line in enumerate(lines):
        subs.append(
            srt.Subtitle(
                index=i+1,
                start=timedelta(seconds=i * 2),
                end=timedelta(seconds=(i + 1) * 2),
                content=line
            )
        )

    return subs


# Upload inputs
audio_file = st.file_uploader("Upload Audio/Video", type=["mp4", "mp3", "wav"])
subtitle_file = st.file_uploader("Upload SRT or TXT", type=["srt", "txt"])


if st.button("Sync Subtitles"):
    if audio_file and subtitle_file:

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

        # Read subtitle input
        content = subtitle_file.read().decode("utf-8")

        if subtitle_file.name.endswith(".srt"):
            subs = list(srt.parse(content))
        else:
            subs = text_to_srt(content)

        # Process subtitles
        for i, sub in enumerate(subs):

            # Clean Arabic
            sub.content = clean_arabic_text(sub.content)

            # Sync timing
            if i < len(segments):
                sub.start = timedelta(seconds=segments[i]["start"])
                sub.end = timedelta(seconds=segments[i]["end"])

        # Output
        output = srt.compose(subs)

        st.success("Done ✅")
        st.download_button("Download SRT", output, file_name="synced.srt")

    else:
        st.error("Upload audio AND subtitle file")
