import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(page_title="ESL Reader", page_icon="🗣️", layout="wide")

st.title("🗣️ ESL Universal Reader")

# --- Input Area ---
default_text = "Hello class. This is a test. We are checking if the highlighting works on your device."
text_input = st.text_area("Paste text here:", value=default_text, height=150)

# --- Python Text Cleaning ---
# We clean the text here to prevent JavaScript errors
clean_text = text_input.replace("\n", " ").strip()
# We use json.dumps to make sure quotes/apostrophes don't break the code
json_text = json.dumps(clean_text)

# --- The Reader Component ---
html_code = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #fff; }}
        
        /* Controls */
        .controls {{ 
            margin-bottom: 20px; 
            padding: 15px; 
            background: #f0f2f6; 
            border-radius: 8px; 
            display: flex; 
            gap: 10px; 
            flex-wrap: wrap; 
        }}
        button {{ 
            padding: 10px 20px; 
            cursor: pointer; 
            background: #ff4b4b; 
            color: white; 
            border: none; 
            border-radius: 4px; 
            font-size: 16px;
        }}
        button:hover {{ background: #ff3333; }}
        select {{ padding: 10px; border-radius: 4px; border: 1px solid #ccc; }}

        /* Text Display */
        #display {{ 
            font-size: 22px; 
            line-height: 1.8; 
            color: #333; 
        }}
        
        /* The Highlight */
        .word {{ 
            padding: 2px 2px; 
            border-radius: 3px; 
            margin-right: 4px; 
            display: inline-block;
            transition: 0.1s;
        }}
        .active {{ 
            background-color: #ffd700; /* Yellow */
            color: black; 
            font-weight: bold; 
            box-shadow: 0 0 5px rgba(255, 215, 0, 0.5);
        }}
        
        /* Debug Status */
        #status {{ margin-top: 20px; color: #888; font-size: 12px; font-family: monospace; }}
    </style>
</head>
<body>

    <div class="controls">
        <button onclick="speak()">▶ Read Aloud</button>
        <button onclick="stop()" style="background:#555;">⏹ Stop</button>
        <select id="voices"></select>
    </div>

    <div id="display"></div>
    <div id="status">Status: Ready</div>

    <script>
        const text = {json_text};
        const display = document.getElementById('display');
        const voiceSelect = document.getElementById('voices');
        const status = document.getElementById('status');
        let synth = window.speechSynthesis;
        let wordSpans = [];

        // 1. Initialize
        function init() {{
            display.innerHTML = '';
            wordSpans = [];
            // Split by space to create spans
            const words = text.split(' ');
            
            words.forEach((w, i) => {{
                let s = document.createElement('span');
                s.innerText = w;
                s.className = 'word';
                // Store the start index of this word in the text
                // This helps us match the 'charIndex' event later
                s.dataset.index = i; 
                display.appendChild(s);
                wordSpans.push(s);
            }});

            loadVoices();
            if (speechSynthesis.onvoiceschanged !== undefined) {{
                speechSynthesis.onvoiceschanged = loadVoices;
            }}
        }}

        function loadVoices() {{
            const voices = synth.getVoices();
            voiceSelect.innerHTML = '';
            // Filter for English
            const enVoices = voices.filter(v => v.lang.includes('en'));
            
            enVoices.forEach(v => {{
                const opt = document.createElement('option');
                opt.textContent = v.name + ' (' + v.lang + ')';
                opt.value = v.name;
                voiceSelect.appendChild(opt);
            }});
        }}

        // 2. The Speaking Logic
        function speak() {{
            stop();
            const utter = new SpeechSynthesisUtterance(text);
            
            // Set Voice
            const voices = synth.getVoices();
            const selected = voiceSelect.value;
            utter.voice = voices.find(v => v.name === selected);
            
            status.innerText = "Status: Speaking using " + selected;

            // 3. The Highlight Event (The Crucial Part)
            utter.onboundary = function(event) {{
                if (event.name === 'word') {{
                    // Remove old highlights
                    wordSpans.forEach(s => s.classList.remove('active'));
                    
                    // Find the word based on character index
                    const charIndex = event.charIndex;
                    
                    // Simple logic: We calculate which word corresponds to this character
                    let currentCount = 0;
                    for (let i = 0; i < wordSpans.length; i++) {{
                        // Add word length + 1 for the space
                        let wLen = wordSpans[i].innerText.length + 1; 
                        
                        if (charIndex >= currentCount && charIndex < (currentCount + wLen)) {{
                            wordSpans[i].classList.add('active');
                            break;
                        }}
                        currentCount += wLen;
                    }}
                }}
            }};

            utter.onend = () => {{ 
                wordSpans.forEach(s => s.classList.remove('active')); 
                status.innerText = "Status: Finished";
            }};
            
            utter.onerror = (e) => {{
                status.innerText = "Status: Error (" + e.error + ")";
            }};

            synth.speak(utter);
        }}

        function stop() {{
            synth.cancel();
            wordSpans.forEach(s => s.classList.remove('active'));
            status.innerText = "Status: Stopped";
        }}

        init();
    </script>
</body>
</html>
"""

components.html(html_code, height=600, scrolling=True)
