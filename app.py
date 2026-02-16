import streamlit as st
import edge_tts
import asyncio
import base64
import json
import nest_asyncio

# Fix for running asyncio loops in Streamlit
nest_asyncio.apply()

# --- Page Config ---
st.set_page_config(page_title="ESL Reader", page_icon="🗣️", layout="centered")

st.title("🗣️ English Text Reader")
st.markdown("Paste your text below, choose a voice, and listen!")

# --- Sidebar Options ---
with st.sidebar:
    st.header("Settings")
    
    # Voice Selection
    voice_options = {
        "American Female (Aria)": "en-US-AriaNeural",
        "American Male (Guy)": "en-US-GuyNeural",
        "British Female (Sonia)": "en-GB-SoniaNeural",
        "British Male (Ryan)": "en-GB-RyanNeural"
    }
    selected_voice_name = st.selectbox("Choose Voice:", list(voice_options.keys()))
    voice_code = voice_options[selected_voice_name]

    # Speed Control
    # We map 0.5x - 2.0x to edge-tts percentage format (+0%, +50%, etc.)
    speed_x = st.slider("Reading Speed:", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
    
    # Convert float speed to edge-tts string format
    percentage = int((speed_x - 1.0) * 100)
    if percentage >= 0:
        rate_str = f"+{percentage}%"
    else:
        rate_str = f"{percentage}%"

# --- Main Input Area ---
user_text = st.text_area("Paste English text here:", height=150, placeholder="Hello! Welcome to our English class...")

# --- Audio Generation Logic ---
async def generate_audio_with_timing(text, voice, rate):
    """
    Generates audio and word-level timing data using edge-tts.
    """
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    audio_data = b""
    word_timings = []
    
    # Stream the data to capture audio and timing events simultaneously
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            # Edge-TTS provides timing in "ticks" (1 tick = 100 nanoseconds)
            # We convert this to seconds for the web player
            start_time = chunk["offset"] / 10_000_000
            duration = chunk["duration"] / 10_000_000
            word_text = chunk["text"]
            
            word_timings.append({
                "word": word_text,
                "start": start_time,
                "end": start_time + duration
            })
            
    return audio_data, word_timings

# --- Button & Display ---
if st.button("Read Aloud", type="primary"):
    if user_text.strip():
        with st.spinner("Generating audio..."):
            # Run the async function
            audio_bytes, timings = asyncio.run(generate_audio_with_timing(user_text, voice_code, rate_str))
            
            # Encode audio to base64 for HTML embedding
            audio_base64 = base64.b64encode(audio_bytes).decode()
            
            # Convert timings to JSON for JavaScript
            timings_json = json.dumps(timings)
            
            # --- The Karaoke Player (HTML/JS/CSS) ---
            # We embed a custom HTML block that plays audio and highlights text
            html_code = f"""
            <style>
                .karaoke-box {{
                    font-family: sans-serif;
                    font-size: 1.2rem;
                    line-height: 1.6;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 10px;
                    background-color: #f9f9f9;
                    margin-top: 20px;
                    color: #333;
                }}
                .word {{
                    transition: background-color 0.1s;
                    padding: 2px;
                    border-radius: 3px;
                }}
                .active-word {{
                    background-color: #ffeb3b; /* Yellow Highlight */
                    font-weight: bold;
                    color: #000;
                }}
                audio {{
                    width: 100%;
                    margin-bottom: 15px;
                }}
            </style>

            <div class="karaoke-box">
                <audio id="player" controls autoplay>
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                </audio>
                <div id="text-display">
                    </div>
            </div>

            <script>
                const timings = {timings_json};
                const displayDiv = document.getElementById('text-display');
                const player = document.getElementById('player');

                // 1. Build the text display with spans for each word
                timings.forEach((item, index) => {{
                    const span = document.createElement('span');
                    span.id = 'word-' + index;
                    span.className = 'word';
                    span.innerText = item.word + " "; // Add space after word
                    displayDiv.appendChild(span);
                }});

                // 2. Listen for audio time updates to highlight words
                player.ontimeupdate = function() {{
                    const currentTime = player.currentTime;
                    
                    timings.forEach((item, index) => {{
                        const span = document.getElementById('word-' + index);
                        if (currentTime >= item.start && currentTime <= item.end) {{
                            span.classList.add('active-word');
                        }} else {{
                            span.classList.remove('active-word');
                        }}
                    }});
                }};
            </script>
            """
            
            # Render the HTML component
            st.components.v1.html(html_code, height=400, scrolling=True)
            
    else:
        st.warning("Please enter some text first.")
