import streamlit as st
import whisper
import srt
from datetime import timedelta
import tempfile

st.title("AI Subtitle Sync Tool")

audio_file = st.file_uploader("Upload Audio/Video", type=["mp4", "mp3", "wav"])
srt_file = st.file_uploader("Upload Arabic SRT", type=["srt"])

if st.button("Sync Subtitles"):
    if audio_file and srt_file:
        st.write("Processing... please wait ⏳")

        # Save temp audio
        with tempfile.NamedTemporaryFile(delete=False) as tmp_audio:
            tmp_audio.write(audio_file.read())
            audio_path = tmp_audio.name

        # Save temp srt
        with tempfile.NamedTemporaryFile(delete=False) as tmp_srt:
            tmp_srt.write(srt_file.read())
            srt_path = tmp_srt.name

        # Load Whisper model
        @st.cache_resource
def load_model():
    return whisper.load_model("tiny")
        model = load_model()

with st.spinner("Processing... please wait ⏳"):
    result = model.transcribe(audio_path)

        # Read subtitles
        with open(srt_path, encoding="utf-8") as f:
    subs = list(srt.parse(f.read()))
        segments = result["segments"]

        # Align subtitles to audio
        for i, sub in enumerate(subs):
            if i < len(segments):
                sub.start = timedelta(seconds=segments[i]["start"])
                sub.end = timedelta(seconds=segments[i]["end"])

        # Output
        output = srt.compose(subs)

        st.success("Done ✅")
        st.download_button("Download Synced SRT", output, file_name="synced.srt")

    else:
        st.error("Please upload both files")
