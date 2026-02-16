import streamlit as st
import edge_tts
import asyncio
import nest_asyncio

# 1. Apply the fix for Streamlit's event loop
nest_asyncio.apply()

# 2. Page Setup
st.set_page_config(page_title="ESL Audio Reader", page_icon="🎧", layout="centered")
st.title("🎧 ESL Audio Reader")
st.markdown("Paste your text, choose a speed, and listen!")

# --- Sidebar: Settings ---
with st.sidebar:
    st.header("Settings")
    
    # Voice Selection
    voice_options = {
        "🇺🇸 US Female (Aria)": "en-US-AriaNeural",
        "🇺🇸 US Male (Guy)": "en-US-GuyNeural",
        "🇬🇧 UK Female (Sonia)": "en-GB-SoniaNeural",
        "🇬🇧 UK Male (Ryan)": "en-GB-RyanNeural"
    }
    selected_voice = st.selectbox("Choose Voice:", list(voice_options.keys()))
    voice_code = voice_options[selected_voice]

    # Speed Control
    # 1.0 is normal. 0.5 is half speed.
    speed = st.slider("Reading Speed:", min_value=0.5, max_value=1.5, value=1.0, step=0.1)
    
    # Convert speed to edge-tts format (e.g., "+50%" or "-20%")
    percentage = int((speed - 1.0) * 100)
    if percentage >= 0:
        rate_str = f"+{percentage}%"
    else:
        rate_str = f"{percentage}%"

# --- Main Input ---
user_text = st.text_area("Paste English text here:", height=200, placeholder="Type something here...")

# --- Audio Logic ---
async def generate_audio(text, voice, rate):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    audio_data = b""
    
    # Simple stream - we only care about the audio, not the timing
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
            
    return audio_data

# --- Play Button ---
if st.button("▶ Read Aloud", type="primary"):
    if not user_text.strip():
        st.warning("Please enter some text first.")
    else:
        with st.spinner("Generating audio..."):
            try:
                # Generate the audio file
                mp3_bytes = asyncio.run(generate_audio(user_text, voice_code, rate_str))
                
                # Display the Audio Player
                st.audio(mp3_bytes, format="audio/mp3")
                
                # Bonus: Add a Download Button
                st.download_button(
                    label="⬇ Download MP3",
                    data=mp3_bytes,
                    file_name="esl_audio.mp3",
                    mime="audio/mp3"
                )
                
            except Exception as e:
                st.error(f"Error: {e}")
