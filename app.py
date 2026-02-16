import streamlit as st
import edge_tts
import asyncio
import base64
import json
import nest_asyncio

# 1. Apply the asyncio fix (Essential for Streamlit)
nest_asyncio.apply()

# 2. Page Setup
st.set_page_config(page_title="ESL Audio Reader", page_icon="🎧", layout="centered")
st.title("🎧 ESL Audio Reader")

# --- Sidebar: Controls ---
with st.sidebar:
    st.header("Settings")
    
    # Voice Selection
    voice_options = {
        "American Female (Aria)": "en-US-AriaNeural",
        "American Male (Guy)": "en-US-GuyNeural",
        "British Female (Sonia)": "en-GB-SoniaNeural",
        "British Male (Ryan)": "en-GB-RyanNeural"
    }
    selected_voice = st.selectbox("Choose Voice:", list(voice_options.keys()))
    voice_code = voice_options[selected_voice]

    # Speed
    speed = st.slider("Speed", 0.5, 2.0, 1.0, 0.1)
    
    # Calculate rate string for edge-tts
    percentage = int((speed - 1.0) * 100)
    rate_str = f"+{percentage}%" if percentage >= 0 else f"{percentage}%"

# --- Main Input ---
st.info("Paste your text below. When you click 'Read', a new frame will open with the player.")
user_text = st.text_area("Text to read:", height=150, value="Hello! This is a new test. The words should light up yellow as I speak them.")

# --- Logic: Generate Audio & Timing ---
async def generate_karaoke_data(text, voice, rate):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    audio_data = b""
    word_timings = []
    
    # Stream data from Edge TTS
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            # Convert ticks to seconds
            # 1 tick = 100 nanoseconds. 10,000,000 ticks = 1 second.
            start = chunk["offset"] / 10_000_000
            duration = chunk["duration"] / 10_000_000
            word_timings.append({
                "word": chunk["text"],
                "start": start,
                "end": start + duration
            })
            
    return audio_data, word_timings

# --- The "New Frame" Component ---
def karaoke_frame(audio_base64, timings_json):
    # This HTML/JS acts as a self-contained "app within an app"
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        /* The "Frame" Styling */
        body {{
            font-family: 'Arial', sans-serif;
            margin: 0; 
            padding: 10px;
            background-color: transparent;
        }}
        .reader-box {{
            background-color: #ffffff;
            border: 2px solid #4CAF50; /* Green border to show it's active */
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        audio {{
            width: 100%;
            margin-bottom: 20px;
            outline: none;
        }}
        #text-container {{
            font-size: 18px;
            line-height: 1.6;
            color: #333;
        }}
        .word {{
            padding: 2px 1px;
            border-radius: 4px;
            transition: background-color 0.1s ease;
            margin-right: 4px;
            display: inline-block;
        }}
        /* The Highlight Style */
        .active {{
            background-color: #ffd700 !important; /* Yellow */
            color: #000 !important;
            font-weight: bold;
            transform: scale(1.1);
        }}
    </style>
    </head>
    <body>
        <div class="reader-box">
            <h3 style="margin-top:0; color:#4CAF50;">▶ Reading Frame</h3>
            
            <audio id="player" controls>
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                Your browser does not support the audio element.
            </audio>
            
            <div id="text-container"></div>
            
            <div id="status" style="font-size:12px; color:#999; margin-top:10px;">Loading data...</div>
        </div>

        <script>
            try {{
                // 1. Load Data
                const timings = {timings_json};
                const container = document.getElementById('text-container');
                const player = document.getElementById('player');
                const status = document.getElementById('status');
                const wordSpans = [];

                status.innerText = "Data loaded. " + timings.length + " words ready.";

                // 2. Build the Text from the Timing Data (Ensures 100% match)
                timings.forEach((t, i) => {{
                    const span = document.createElement('span');
                    span.innerText = t.word;
                    span.className = 'word';
                    span.id = 'w-' + i;
                    container.appendChild(span);
                    wordSpans.push(span);
                }});

                // 3. Highlight Logic (The Loop)
                player.ontimeupdate = function() {{
                    const time = player.currentTime;
                    
                    // Optimization: We only check words around the current index if we wanted, 
                    // but for short texts, a full loop is safer.
                    for (let i = 0; i < timings.length; i++) {{
                        let t = timings[i];
                        if (time >= t.start && time < t.end) {{
                            wordSpans[i].classList.add('active');
                        }} else {{
                            wordSpans[i].classList.remove('active');
                        }}
                    }}
                }};
                
                // 4. Auto-play (Might be blocked by browsers, but we try)
                player.play().catch(e => console.log("Autoplay blocked, user must click play."));

            }} catch (err) {{
                document.getElementById('status').innerText = "Error: " + err.message;
            }}
        </script>
    </body>
    </html>
    """
    st.components.v1.html(html_code, height=600, scrolling=True)

# --- Button Logic ---
if st.button("Read Aloud", type="primary"):
    if not user_text.strip():
        st.warning("Please enter text first!")
    else:
        with st.spinner("Creating your reading frame..."):
            try:
                # 1. Run Async Generation
                mp3_bytes, timings = asyncio.run(generate_karaoke_data(user_text, voice_code, rate_str))
                
                # 2. Debug Check
                if not timings:
                    st.error("Error: No word timings received. Try a shorter text or different voice.")
                else:
                    # 3. Prepare Data
                    audio_b64 = base64.b64encode(mp3_bytes).decode()
                    timings_str = json.dumps(timings)
                    
                    # 4. Open the Frame
                    st.success("Ready! See the frame below.")
                    karaoke_frame(audio_b64, timings_str)
                    
            except Exception as e:
                st.error(f"Something went wrong: {e}")
