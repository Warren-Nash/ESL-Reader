import streamlit as st
import edge_tts
import asyncio
import base64
import json
import nest_asyncio

# Fix for running asyncio loops in Streamlit
nest_asyncio.apply()

# --- Page Config ---
st.set_page_config(page_title="ESL Karaoke Reader", page_icon="🗣️", layout="centered")

st.title("🗣️ ESL Karaoke Reader")
st.markdown("Paste text, choose a voice, and watch it highlight as it reads!")

# --- Sidebar Options ---
with st.sidebar:
    st.header("Settings")
    
    # Voice Selection
    # Note: Only 'Neural' voices support WordBoundary events reliably
    voice_options = {
        "American Female (Aria)": "en-US-AriaNeural",
        "American Male (Guy)": "en-US-GuyNeural",
        "British Female (Sonia)": "en-GB-SoniaNeural",
        "British Male (Ryan)": "en-GB-RyanNeural"
    }
    selected_voice_name = st.selectbox("Choose Voice:", list(voice_options.keys()))
    voice_code = voice_options[selected_voice_name]

    # Speed Control
    speed_x = st.slider("Reading Speed:", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
    
    # Convert float speed to edge-tts string format
    percentage = int((speed_x - 1.0) * 100)
    rate_str = f"+{percentage}%" if percentage >= 0 else f"{percentage}%"

# --- Main Input Area ---
user_text = st.text_area("Paste English text here:", height=150, value="Hello class! This is an example of how the app highlights text while reading.")

# --- Audio Generation Logic ---
async def generate_audio_with_timing(text, voice, rate):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    audio_data = b""
    word_timings = []
    
    # Stream the data
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            # Convert ticks (100 nanoseconds) to seconds
            start_time = chunk["offset"] / 10_000_000
            duration = chunk["duration"] / 10_000_000
            word_text = chunk["text"]
            
            # Create a simplified timing object
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
            try:
                # Run the async function
                audio_bytes, timings = asyncio.run(generate_audio_with_timing(user_text, voice_code, rate_str))
                
                # Check if timings were actually generated
                if not timings:
                    st.error("Warning: The selected voice did not return timing data. Try 'American Female (Aria)'.")
                
                # Encode audio to base64
                audio_base64 = base64.b64encode(audio_bytes).decode()
                timings_json = json.dumps(timings)
                
                # --- The Karaoke Player (HTML/JS/CSS) ---
                # Key Fixes: 
                # 1. Doubled braces {{ }} for Python f-strings
                # 2. Simplified JS loop
                html_code = f"""
                <style>
                    .karaoke-box {{
                        font-family: 'Helvetica', sans-serif;
                        font-size: 1.3rem;
                        line-height: 1.8;
                        padding: 20px;
                        border: 2px solid #eee;
                        border-radius: 10px;
                        background-color: #ffffff;
                        color: #333;
                        margin-top: 20px;
                    }}
                    .word {{
                        padding: 0 2px;
                        border-radius: 4px;
                        transition: background-color 0.1s ease;
                        display: inline-block; /* Helps with highlighting */
                    }}
                    /* Force the highlight color */
                    .active-word {{
                        background-color: #ffeb3b !important; 
                        color: #000 !important;
                        font-weight: bold;
                        transform: scale(1.05); /* Slight pop effect */
                    }}
                    audio {{
                        width: 100%;
                        margin-bottom: 20px;
                    }}
                </style>

                <div class="karaoke-box">
                    <audio id="player" controls autoplay>
                        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    </audio>
                    <div id="text-display"></div>
                </div>

                <script>
                    (function() {{
                        const timings = {timings_json};
                        const displayDiv = document.getElementById('text-display');
                        const player = document.getElementById('player');
                        const wordSpans = []; // Cache the spans for performance

                        // 1. Build the text display
                        timings.forEach((item, index) => {{
                            const span = document.createElement('span');
                            span.innerText = item.word + " "; // Add space
                            span.className = 'word';
                            displayDiv.appendChild(span);
                            wordSpans.push(span);
                        }});

                        // 2. High performance loop
                        player.ontimeupdate = function() {{
                            const currentTime = player.currentTime;
                            
                            // Check every word (simple but effective for short texts)
                            for (let i = 0; i < timings.length; i++) {{
                                const t = timings[i];
                                if (currentTime >= t.start && currentTime < t.end) {{
                                    wordSpans[i].classList.add('active-word');
                                    // Optional: Scroll into view if text is long
                                    // wordSpans[i].scrollIntoView({{behavior: "smooth", block: "center"}});
                                }} else {{
                                    wordSpans[i].classList.remove('active-word');
                                }}
                            }}
                        }};
                    }})();
                </script>
                """
                
                # Render the component with a fixed height to prevent scrolling issues
                st.components.v1.html(html_code, height=600, scrolling=True)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
            
    else:
        st.
