import streamlit as st
import edge_tts
import asyncio
import base64
import json
import nest_asyncio

# 1. Apply Async Fix
nest_asyncio.apply()

st.set_page_config(page_title="ESL Reader", page_icon="🏫")
st.title("🏫 ESL Reader (Stable)")

# --- Settings ---
with st.sidebar:
    st.header("Settings")
    st.info("Note: Speed control is disabled in this version to ensure highlighting works.")
    
    # We only use Aria and Guy (US) as they are the most reliable for timestamps
    voice_options = {
        "US Female (Aria)": "en-US-AriaNeural",
        "US Male (Guy)": "en-US-GuyNeural",
        "UK Female (Sonia)": "en-GB-SoniaNeural",
        "UK Male (Ryan)": "en-GB-RyanNeural"
    }
    selected_voice = st.selectbox("Choose Voice:", list(voice_options.keys()))
    voice_code = voice_options[selected_voice]

user_text = st.text_area("Paste Text:", height=150, value="Hello class. This is a test of the highlighting system.")

# --- Logic ---
async def get_data(text, voice):
    # REMOVED: rate=rate_str (This is often the culprit)
    communicate = edge_tts.Communicate(text, voice)
    
    audio_data = b""
    word_timings = []
    
    # Debug counters
    audio_chunks = 0
    timing_chunks = 0
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
            audio_chunks += 1
        elif chunk["type"] == "WordBoundary":
            timing_chunks += 1
            start = chunk["offset"] / 10_000_000
            duration = chunk["duration"] / 10_000_000
            word_timings.append({
                "word": chunk["text"],
                "start": start,
                "end": start + duration
            })
            
    return audio_data, word_timings, audio_chunks, timing_chunks

# --- Button ---
if st.button("Read Aloud"):
    if not user_text.strip():
        st.warning("Enter text first.")
    else:
        with st.spinner("Connecting to Microsoft Edge servers..."):
            try:
                # Run Async
                mp3_bytes, timings, a_count, t_count = asyncio.run(get_data(user_text, voice_code))
                
                # --- DIAGNOSTIC INFO (This will tell us the problem) ---
                if not timings:
                    st.error(f"Failed. Received {a_count} audio chunks but {t_count} timing chunks.")
                    st.write("Troubleshooting: Try a longer sentence. Try 'US Female (Aria)'.")
                else:
                    # Success! Render the player.
                    st.success(f"Success! Generated {len(timings)} words.")
                    
                    audio_b64 = base64.b64encode(mp3_bytes).decode()
                    timings_json = json.dumps(timings)
                    
                    html_code = f"""
                    <!DOCTYPE html>
                    <html>
                    <style>
                        .box {{ padding: 20px; border: 1px solid #ddd; border-radius: 8px; background: #fff; line-height: 1.8; font-family: sans-serif; font-size: 18px; }}
                        .word {{ padding: 2px; border-radius: 3px; transition: 0.1s; margin-right: 4px; display: inline-block; }}
                        .active {{ background: #ffd700; color: black; font-weight: bold; }}
                    </style>
                    <div class="box">
                        <audio id="player" controls autoplay style="width:100%; margin-bottom:15px;">
                            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                        </audio>
                        <div id="text"></div>
                    </div>
                    <script>
                        const data = {timings_json};
                        const div = document.getElementById('text');
                        const player = document.getElementById('player');
                        const spans = [];

                        // Build text
                        data.forEach((item, i) => {{
                            let s = document.createElement('span');
                            s.innerText = item.word;
                            s.className = 'word';
                            div.appendChild(s);
                            spans.push(s);
                        }});

                        // Highlight loop
                        player.ontimeupdate = () => {{
                            let t = player.currentTime;
                            for(let i=0; i<data.length; i++) {{
                                if (t >= data[i].start && t < data[i].end) spans[i].classList.add('active');
                                else spans[i].classList.remove('active');
                            }}
                        }};
                    </script>
                    </html>
                    """
                    st.components.v1.html(html_code, height=500, scrolling=True)

            except Exception as e:
                st.error(f"System Error: {e}")
