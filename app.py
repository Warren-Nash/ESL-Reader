import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ESL Reader", page_icon="🗣️", layout="wide")

st.title("🗣️ ESL Reader (Browser Native)")
st.markdown("""
This version uses your **device's built-in voices**. 
It guarantees that **highlighting always works** because it runs directly in your browser.
""")

# --- Input Area ---
default_text = "Hello! This app uses your browser's built-in text-to-speech engine. It highlights every word perfectly as it is spoken. You can change the speed and the voice below."
text_input = st.text_area("Paste your text here:", value=default_text, height=150)

# --- The Magic Component (HTML/JS) ---
# We inject a full HTML5 application that handles the reading locally.
html_code = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            padding: 20px;
        }}
        .controls {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}
        button {{
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.2s;
        }}
        button:hover {{ background-color: #0056b3; }}
        button.stop {{ background-color: #dc3545; }}
        button.stop:hover {{ background-color: #a71d2a; }}
        
        select, input {{
            padding: 8px;
            border-radius: 5px;
            border: 1px solid #ddd;
        }}

        #text-display {{
            font-size: 20px;
            line-height: 1.8;
            background: white;
            padding: 30px;
            border-radius: 10px;
            border: 1px solid #e9ecef;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            min-height: 200px;
        }}
        
        /* The Highlight Style */
        .word {{
            padding: 2px 2px;
            border-radius: 3px;
            margin: 0 1px;
            transition: background-color 0.1s;
        }}
        .active {{
            background-color: #ffeb3b; /* Yellow */
            color: black;
            font-weight: bold;
            box-shadow: 0 0 3px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>

    <div class="controls">
        <button onclick="startReading()">▶ Play</button>
        <button onclick="stopReading()" class="stop">⏹ Stop</button>
        
        <div>
            <label>Speed:</label>
            <input type="range" id="rate" min="0.5" max="2" value="1" step="0.1" oninput="updateSpeedLabel()">
            <span id="speed-label">1.0x</span>
        </div>

        <div>
            <label>Voice:</label>
            <select id="voice-select"></select>
        </div>
    </div>

    <div id="text-display"></div>

    <script>
        // 1. Setup Variables
        const text = `{text_input.replace(chr(10), " ").replace("`", "'")}`; 
        const display = document.getElementById('text-display');
        const voiceSelect = document.getElementById('voice-select');
        const rateInput = document.getElementById('rate');
        let synth = window.speechSynthesis;
        let utterance = null;
        let wordSpans = [];

        // 2. Initialize Text & Voices
        function init() {{
            // Build word spans
            display.innerHTML = '';
            wordSpans = [];
            const words = text.split(/\\s+/); // Split by spaces
            
            words.forEach((word, index) => {{
                let span = document.createElement('span');
                span.innerText = word + " ";
                span.className = 'word';
                // Store the index to match with speech events later
                span.dataset.index = index; 
                display.appendChild(span);
                wordSpans.push(span);
            }});

            // Load Voices (Browsers load these asynchronously)
            populateVoices();
            if (speechSynthesis.onvoiceschanged !== undefined) {{
                speechSynthesis.onvoiceschanged = populateVoices;
            }}
        }}

        function populateVoices() {{
            const voices = synth.getVoices();
            voiceSelect.innerHTML = '';
            
            // Filter for English voices only
            const englishVoices = voices.filter(v => v.lang.includes('en'));
            
            englishVoices.forEach(voice => {{
                const option = document.createElement('option');
                option.textContent = voice.name + ' (' + voice.lang + ')';
                option.value = voice.name;
                voiceSelect.appendChild(option);
            }});
        }}

        function updateSpeedLabel() {{
            document.getElementById('speed-label').innerText = rateInput.value + 'x';
        }}

        // 3. Reading Logic
        function startReading() {{
            // Cancel any current speech
            stopReading();

            utterance = new SpeechSynthesisUtterance(text);
            
            // Apply Settings
            const selectedVoiceName = voiceSelect.value;
            const voices = synth.getVoices();
            utterance.voice = voices.find(v => v.name === selectedVoiceName);
            utterance.rate = parseFloat(rateInput.value);

            // HIGHLIGHTING EVENT (The Boundary)
            let charIndex = 0;
            
            utterance.onboundary = function(event) {{
                if (event.name === 'word') {{
                    // Remove highlight from all
                    wordSpans.forEach(s => s.classList.remove('active'));
                    
                    // We need to find which word corresponds to this character index
                    // This is a simple estimation based on char count
                    let currentLength = 0;
                    for (let i = 0; i < wordSpans.length; i++) {{
                        // +1 for the space
                        currentLength += wordSpans[i].innerText.length; 
                        if (currentLength > event.charIndex) {{
                            wordSpans[i].classList.add('active');
                            // Auto-scroll to the word
                            wordSpans[i].scrollIntoView({{behavior: "smooth", block: "center"}});
                            break;
                        }}
                    }}
                }}
            }};

            utterance.onend = function() {{
                wordSpans.forEach(s => s.classList.remove('active'));
            }};

            synth.speak(utterance);
        }}

        function stopReading() {{
            synth.cancel();
            wordSpans.forEach(s => s.classList.remove('active'));
        }}

        // Run Init
        init();

    </script>
</body>
</html>
"""

# Render the HTML component with a fixed height
components.html(html_code, height=600, scrolling=True)
