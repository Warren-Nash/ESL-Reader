import streamlit as st
import edge_tts
import asyncio
import nest_asyncio

# 1. Apply the fix for Streamlit's event loop
nest_asyncio.apply()

# 2. Page Setup
st.set_page_config(page_title="ESL Audio Reader", page_icon="🗣️", layout="centered")
st.title("🗣️ ESL Audio Reader")

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
    selected_voice_name = st.selectbox("Choose Voice:", list(voice_options.keys()))
    voice_code = voice_options[selected_voice_name]

    # Speed Control
    speed = st.slider("Reading Speed:", 0.5, 1.5, 1.0, 0.1)
    
    # Text Size Control (New!)
    # Range: 14px (Small) to 40px (Huge). Default: 22px.
    text_size = st.slider("Text Size:", 14, 50, 22)
    
    # Convert speed to edge-tts format
    percentage = int((speed - 1.0) * 100)
    rate_str = f"+{percentage}%" if percentage >= 0 else f"{percentage}%"

# --- DYNAMIC CSS ---
# We use the 'text_size' variable from the slider to set the CSS
st.markdown(f"""
<style>
    /* Target the text area inside Streamlit */
    .stTextArea textarea {{
        font-size: {text_size}px !important;
        line-height: 1.5 !important;
        font-family: sans-serif;
    }}
</style>
""", unsafe_allow_html=True)

# --- Main Input ---
user_text = st.text_area("Paste English text here:", height=300, placeholder="Paste text here...")

# --- Audio Logic ---
async def generate_audio(text, voice, rate):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    audio_data = b""
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
                # Run the async function
                mp3_bytes = asyncio.run(generate_audio(user_text, voice_code, rate_str))
                
                # Audio Player
                st
