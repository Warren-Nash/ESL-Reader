import streamlit as st
import edge_tts
import asyncio
import nest_asyncio

# 1. Исправление для работы asyncio в Streamlit
nest_asyncio.apply()

# 2. Настройка страницы
st.set_page_config(page_title="Тренажер чтения", page_icon="🗣️", layout="centered")
st.title("🗣️ Тренажер чтения на английском")

# --- Боковая панель: Настройки ---
with st.sidebar:
    st.header("Настройки")
    
    # Выбор голоса (Перевел названия стран)
    voice_options = {
        "🇺🇸 США, Женский (Aria)": "en-US-AriaNeural",
        "🇺🇸 США, Мужской (Guy)": "en-US-GuyNeural",
        "🇬🇧 Британия, Женский (Sonia)": "en-GB-SoniaNeural",
        "🇬🇧 Британия, Мужской (Ryan)": "en-GB-RyanNeural"
    }
    selected_voice_name = st.selectbox("Выберите голос:", list(voice_options.keys()))
    voice_code = voice_options[selected_voice_name]

    # Регулировка скорости
    speed = st.slider("Скорость речи:", 0.5, 1.5, 1.0, 0.1)
    
    # Регулировка размера текста
    text_size = st.slider("Размер шрифта:", 14, 50, 22)
    
    # Конвертация скорости для edge-tts
    percentage = int((speed - 1.0) * 100)
    if percentage >= 0:
        rate_str = f"+{percentage}%"
    else:
        rate_str = f"{percentage}%"

# --- Динамический CSS (Размер шрифта) ---
st.markdown(f"""
<style>
    /* Стиль для поля ввода текста */
    .stTextArea textarea {{
        font-size: {text_size}px !important;
        line-height: 1.5 !important;
        font-family: sans-serif;
    }}
    /* Стиль для заголовка над полем */
    .stTextArea label {{
        font-size: 18px !important;
        font-weight: bold;
    }}
</style>
""", unsafe_allow_html=True)

# --- Основное поле ввода ---
user_text = st.text_area("Вставьте английский текст сюда:", height=300, placeholder="Hello! My name is...")

# --- Логика создания аудио ---
async def generate_audio(text, voice, rate):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
