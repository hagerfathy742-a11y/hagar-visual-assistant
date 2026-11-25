import os
import io
import base64
import asyncio
import edge_tts
import streamlit as st
from google import genai
from PIL import Image
from pypdf import PdfReader

st.set_page_config(page_title="Hagar Robot AI", page_icon="🤖", layout="centered", initial_sidebar_state="collapsed")

try:
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
except Exception:
    api_key = os.getenv("GEMINI_API_KEY")

st.markdown("""
<style>
    @import url('https://googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    section[data-testid="stSidebar"], button[data-testid="collapsedControl"] { display: none !important; width: 0 !important; }
    .stApp { background: radial-gradient(circle at top, #1E1B4B 0%, #090D16 70%) !important; color: #FFFFFF !important; }
    .stApp p, .stApp label, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp div[data-testid="stMarkdownContainer"] { color: #F8FAFC !important; }
    [data-testid="stFileUploader"] section { background-color: rgba(30, 41, 59, 0.9) !important; border: 1.5px dashed #38BDF8 !important; border-radius: 16px !important; }
    [data-testid="stFileUploader"] section * { color: #F8FAFC !important; }
    [data-testid="stFileUploader"] button { background: #2563EB !important; color: #FFFFFF !important; border: none !important; }
    .robot-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.92), rgba(15, 23, 42, 0.96));
        border: 1.5px solid rgba(56, 189, 248, 0.55); border-radius: 26px; padding: 24px 18px; text-align: center;
        box-shadow: 0 12px 35px rgba(56, 189, 248, 0.25), inset 0 0 20px rgba(139, 92, 246, 0.15); margin-bottom: 20px;
    }
    .robot-head {
        width: 105px; height: 90px; margin: 0 auto 14px auto;
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
        border-radius: 28px; border: 3px solid #38BDF8; box-shadow: 0 0 25px rgba(56, 189, 248, 0.65);
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        position: relative; animation: hoverRobot 2.8s ease-in-out infinite;
    }
    .robot-antenna { width: 6px; height: 16px; background: #38BDF8; position: absolute; top: -18px; border-radius: 4px; }
    .robot-antenna::after { content: ""; width: 12px; height: 12px; background: #A855F7; border-radius: 50%; position: absolute; top: -8px; left: -3px; box-shadow: 0 0 12px #A855F7; }
    .robot-eyes { display: flex; gap: 20px; margin-bottom: 10px; }
    .eye { width: 20px; height: 20px; background: #38BDF8; border-radius: 50%; box-shadow: 0 0 14px #38BDF8, 0 0 28px #38BDF8; animation: blinkEye 3.5s infinite; }
    .robot-mouth { width: 34px; height: 6px; background: #A855F7; border-radius: 10px; box-shadow: 0 0 10px #A855F7; animation: talkPulse 1.2s infinite alternate; }
    @keyframes hoverRobot { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-7px); } }
    @keyframes blinkEye { 0%, 92%, 100% { transform: scaleY(1); } 96% { transform: scaleY(0.1); } }
    @keyframes talkPulse { 0% { width: 22px; opacity: 0.7; } 100% { width: 38px; opacity: 1; } }
    .robot-title { font-size: 1.65rem; font-weight: 800; background: linear-gradient(90deg, #38BDF8, #C084FC); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 6px; }
    .robot-sub { color: #E2E8F0 !important; font-size: 0.95rem; margin: 0; }
    .stButton > button { background: linear-gradient(135deg, #2563EB 0%, #9333EA 100%) !important; color: #FFFFFF !important; border: none !important; border-radius: 14px !important; font-weight: 700 !important; padding: 12px 20px !important; }
    .stChatMessage { background: rgba(30, 41, 59, 0.85) !important; border: 1px solid rgba(56, 189, 248, 0.3) !important; border-radius: 16px !important; direction: rtl; text-align: right; }
    div[data-testid="stRadio"] > div { background: rgba(30, 41, 59, 0.8); padding: 12px 16px; border-radius: 14px; border: 1px solid rgba(56, 189, 248, 0.35); }
    details { background: rgba(30, 41, 59, 0.7) !important; border: 1px solid rgba(56, 189, 248, 0.3) !important; border-radius: 14px !important; padding: 4px 10px !important; }
    input, textarea { background-color: #0F172A !important; color: #FFFFFF !important; border: 1px solid #38BDF8 !important; }
</style>
""", unsafe_allow_html=True)

# دالة توليد صوت بشري مصري طبيعي وسريع
async def generate_human_voice(text, voice_id):
    communicate = edge_tts.Communicate(text, voice_id, rate="+18%")
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes

def speak_like_human(text_to_speak, voice_choice):
    try:
        clean_text = text_to_speak.replace("*", "").replace("#", "").replace("-", " ")
        voice_id = "ar-EG-SalmaNeural" if "بنت" in voice_choice else "ar-EG-ShakirNeural"
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_data = loop.run_until_complete(generate_human_voice(clean_text, voice_id))
        b64_audio = base64.b64encode(audio_data).decode()
        audio_html = f'<audio id="humanVoice" autoplay="true" controls style="width:100%;height:38px;margin-top:8px;"><source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3"></audio><script>var a=document.getElementById("humanVoice");if(a){{a.play().catch(function(e){{}});}}</script>'
        st.components.v1.html(audio_html, height=55)
    except Exception:
        pass

def ask_gemini(contents_list):
    client = genai.Client(api_key=api_key)
    candidate_models = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash-lite", "gemini-2.0-flash"]
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if ("flash" in name or "pro" in name) and name not in candidate_models:
                candidate_models.append(name)
    except Exception:
        pass
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(model=model_name, contents=contents_list)
            if response and response.text:
                return response.text
        except Exception:
            continue
    return "معلش يا فندم، الشبكة تقيلة لحظة، جرب تبعتلي تاني كده."

with st.expander("⚙️ إعدادات الروبوت وصوته (اضغط للفتح)"):
    robot_name = st.text_input("اسم الروبوت", value="روبوت هاجر الذكي")
    voice_type = st.selectbox("نبرة الصوت البشري:", ["👩 صوت بنت مصرية (سلمى - طبيعي وودود)", "👨 صوت شاب مصري (شاكر - حيوي وسريع)"])
    whatsapp = st.text_input("رقم الواتساب", value="01000000000")
    catalog_text = st.text_area("قائمة منتجات المتجر (اختياري):", value="", height=80)

st.markdown(f"""
<div class="robot-card">
    <div class="robot-head">
        <div class="robot-antenna"></div>
        <div class="robot-eyes"><div class="eye"></div><div class="eye"></div></div>
        <div class="robot-mouth"></div>
    </div>
    <div class="robot-title">🤖 {robot_name}</div>
    <p class="robot-sub">ورّيني أي حاجة بالكاميرا أو الصورة، وهكلمك عنها بصوت مصري طبيعي وأقولك سعرها فوراً!</p>
</div>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_image" not in st.session_state:
    st.session_state.current_image = None
if "last_processed_id" not in st.session_state:
    st.session_state.last_processed_id = None

st.markdown("### 📸 عين الروبوت")
input_type = st.radio("اختر مصدر الرؤية:", ["📸 الكاميرا المباشرة", "📁 رفع صورة"], horizontal=True)
img_file = st.camera_input("التقط صورة ليراها الروبوت") if input_type == "📸 الكاميرا المباشرة" else st.file_uploader("اختر صورة من جهازك", type=["jpg", "jpeg", "png"])

if img_file is not None:
    pil_img = Image.open(img_file)
    st.session_state.current_image = pil_img
    st.image(pil_img, caption="الصورة أمام الروبوت الآن", use_container_width=True)
    file_id = f"{img_file.name}_{img_file.size}"
    if st.session_state.last_processed_id != file_id:
        if not api_key:
            st.error("⚠️ تأكد من وضع GEMINI_API_KEY في Secrets.")
        else:
            with st.spinner("🤖 ثواني ببص على الصورة..."):
                human_prompt = f"أنت {robot_name}. اتكلم بالعامية المصرية الطبيعية جداً كأنك إنسان مصري ودود وذكي واقف جنب صاحبك، بلاش كلام رسمي أو آلي أبداً! في 3 جمل قصيرة وسريعة: قول إيه اللي في الصورة بعفوية، وقدّر سعره في السوق المصري بالجنيه، ولو في كتابة مهمة اقرأها، واسأله لو حابب يعرف حاجة تانية. بيانات إضافية: {catalog_text} - واتساب: {whatsapp}"
                first_reply = ask_gemini([st.session_state.current_image, human_prompt])
                st.session_state.last_processed_id = file_id
                st.session_state.chat_history = [{"role": "assistant", "content": first_reply}]
                speak_like_human(first_reply, voice_type)

if st.session_state.chat_history:
    st.markdown("### 💬 حوار الروبوت")
    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "🧑").markdown(msg["content"])
    if st.button("🗑️ محادثة جديدة", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.current_image = None
        st.session_state.last_processed_id = None
        st.rerun()

follow_up = st.chat_input("اتكلم مع الروبوت واسأله أي سؤال...")
if follow_up:
    st.session_state.chat_history.append({"role": "user", "content": follow_up})
    st.chat_message("user", avatar="🧑").markdown(follow_up)
    if api_key:
        with st.spinner("🤖 بيرد عليك..."):
            history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history])
