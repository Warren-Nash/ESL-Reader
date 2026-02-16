import streamlit as st
import edge_tts
import asyncio
import base64
import json
import nest_asyncio

# 1. Apply the asyncio fix for Streamlit
nest_asyncio.apply()

# 2. Configure the page
st.set_page_config(page_title="ESL Karaoke Reader", page_icon="🗣️")
st.title("🗣️ ESL Karaoke Reader")

# --- Settings Sidebar ---
with st.sidebar:
    st.header("Settings")
    
    # Voice Selection
    # These 'Neural' voices are required for the timing to work
    voice_options = {
        "American Female (Aria)": "en-US-AriaNeural",
        "American Male (Guy)": "en-US-GuyNeural",
        "British Female (Sonia)": "en-GB-SoniaNeural",
        "British Male (Ryan)": "en-GB-RyanNeural"
    }
    selected_voice_name = st.selectbox("Choose Voice:", list(voice_options.keys()))
    voice_code = voice_options[selected_voice_name]

    # Speed Slider (0.5x to 2.0x)
    speed_x = st.slider("Reading Speed:", 0.5, 2.0, 1.0, 0.1)
    
    # Convert speed to edge-tts format (e.g., +50%)
    percentage = int((speed_x - 1.0) * 100)
    if percentage >= 0:
        rate_str = f"+{percentage}%"
    else:
        rate_str = f"{percentage}%"

# --- Main Text Input ---
user_text = st.text_area("Paste English text here:", height=150, value="Hello! This is a test to see if the highlighting works correctly.")

# --- The Core Logic Function ---
async def get_audio_and_timings(text, voice, rate):
    """Generates audio MP3 and word timing data."""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    
    audio_data = b""
    word_timings = []
    
    # We loop through the data stream
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
            
        elif chunk["type"] == "WordBoundary":
            # edge-tts gives time in 'ticks' (1 tick = 100 nanoseconds)
            # We convert to seconds: ticks / 10,000,000
            start = chunk["offset"] / 10_000_000
            duration = chunk["duration"] / 10_000_000
            
            word_timings.append({
                "word": chunk["text"],
                "start": start,
                "end": start + duration
            })
            
    return audio_data, word_timings

# --- Run Button ---
if st.button("Read Aloud", type="primary"):
    if not user_text.strip():
        st.warning("Please enter some text first.")
    else:
        with st.spinner("Generating audio..."):
            
            # 1. Run the async generator
            # We use a try/except block to catch connection errors
            try:
                mp3_bytes, timings = asyncio.run(get_audio_and_timings(user_text, voice_code, rate_str))
                
                # 2. Prepare data for the web player
                audio_base64 = base64.b64encode(mp3_bytes).decode()
                timings_json = json.dumps(timings)
                
                # 3. The HTML/JS Player (The "Karaoke" part)
                # We inject this Custom HTML into the app
                custom_html = f"""
                <html>
                <style>
                    .box {{
                        font-family: sans-serif;
                        font-size: 1.2rem;
                        line-height: 1.6;
                        padding: 15px;
                        border: 1px solid #ccc;
                        border-radius: 8px;
                        background: #f9f9f9;
                        margin-top: 10px;
                    }}
                    .word {{
                        padding: 2px;
                        margin: 0 1px;
                        border-radius: 3px;
                        transition: background 0.1s;
                    }}
                    .highlight {{
                        background-color: #ffd700 !important; /* Gold color */
                        color: black !important;
                        font-weight: bold;
                    }}
                    audio {{ width: 100%; margin-bottom: 15px; }}
                </style>
                
                <div class="box">
                    <audio id="audio_player" controls autoplay>
                        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    </audio>
                    <div id="text_container"></div>
                </div>

                <script>
                    (function() {{
                        // Get data from Python
                        const timings = {timings_json};
                        const container = document.getElementById('text_container');
                        const player = document.getElementById('audio_player');
                        const spans = [];

                        // Build the text on screen
                        timings.forEach((t, i) => {{
                            let span = document.createElement('span');
                            span.innerText = t.word + ' ';
                            span.className = 'word';
                            container.appendChild(span);
                            spans.push(span);
                        }});

                        // Update highlighting as audio plays
                        player.ontimeupdate = function() {{
                            let time = player.currentTime;
                            
                            // Simple loop to check which word is active
                            for (let i = 0; i < timings.length; i++) {{
                                let t = timings[i];
                                if (time >= t.start && time < t.end) {{
                                    spans[i].classList.add('highlight');
                                }} else {{
                                    spans[i].classList.remove('highlight');
                                }}
                            }}
                        }};
                    }})();
                </script>
                </html>
                """
                
                # Render the HTML
                st.components.v1.html(custom_html, height=500, scrolling=True)

            except Exception as e:
                st.error(f"Error generating audio: {e}")
