import os
import io
import base64
import streamlit as st
from google import genai
from PIL import Image
from pypdf import PdfReader
from gtts import gTTS

st.set_page_config(page_title="Hagar Robot AI - الروبوت البصري الذكي", page_icon="🤖", layout="wide")

try:
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
except Exception:
    api_key = os.getenv("GEMINI_API_KEY")

st.markdown("""
<style>
    @import url('https://googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    
    .robot-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #3B82F6 100%);
        padding: 25px;
        border-radius: 22px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
        border: 1px solid rgba(96, 165, 250, 0.4);
    }
    .robot-avatar {
        width: 110px;
        height: 110px;
        margin: 0 auto 12px auto;
        background: #1E293B;
        border-radius: 50%;
        border: 4px solid #38BDF8;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 25px #38BDF8;
        animation: float 3s ease-in-out infinite;
    }
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
    }
    .robot-eyes {
        display: flex;
        gap: 18px;
    }
    .eye {
        width: 22px;
        height: 22px;
        background: #38BDF8;
        border-radius: 50%;
        box-shadow: 0 0 15px #38BDF8, 0 0 30px #38BDF8;
        animation: blink 4s infinite;
    }
    @keyframes blink {
        0%, 94%, 100% { transform: scaleY(1); }
        97% { transform: scaleY(0.1); }
    }
    .stChatMessage { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)

def autoplay_audio(text_to_speak):
    try:
        tts = gTTS(text=text_to_speak, lang="ar")
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        b64_audio = base64.b64encode(audio_fp.read()).decode()
        audio_html = f"""
            <audio autoplay="true" controls style="width: 100%; margin-top: 10px; border-radius: 10px;">
                <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception:
        pass

def ask_gemini(contents_list):
    client = genai.Client(api_key=api_key)
    candidate_models = [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash"
    ]
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if ("flash" in name or "pro" in name) and name not in candidate_models:
                candidate_models.append(name)
    except Exception:
        pass

    last_err = None
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents_list
            )
            if response and response.text:
                return response.text
        except Exception as err:
            last_err = err
            continue
    raise last_err

with st.sidebar:
    st.header("🤖 لوحة تحكم الروبوت")
    robot_name = st.text_input("اسم الروبوت / الشركة", value="روبوت هاجر الذكي")
    mode = st.selectbox(
        "تخصص الروبوت:",
        ["🛍️ روبوت مبيعات بصري للمتاجر", "👁️ روبوت مساعد بصري عام"]
    )
    whatsapp = st.text_input("رقم الواتساب للتواصل", value="01000000000")
    
    catalog_text = ""
    if mode == "🛍️ روبوت مبيعات بصري للمتاجر":
        st.divider()
        uploaded_catalog = st.file_uploader("📄 كتالوج المنتجات (PDF / TXT)", type=["pdf", "txt"])
        if uploaded_catalog:
            if uploaded_catalog.name.endswith(".pdf"):
                reader = PdfReader(uploaded_catalog)
                for page in reader.pages:
                    catalog_text += (page.extract_text() or "") + "\n"
            else:
                catalog_text = uploaded_catalog.read().decode("utf-8", errors="ignore")
            st.success("✅ تم ربط الكتالوج!")
        else:
            catalog_text = st.text_area(
                "قائمة المنتجات المتاحة:",
                value="1. لابتوب Dell Core i7 رام 16 - السعر 18,500 جنيه.\n2. ساعة ذكية Smart Watch Ultra - السعر 850 جنيه.\n3. سماعة بلوتوث عازلة للضوضاء - السعر 600 جنيه.\n4. كوتشي رياضي أبيض - السعر 650 جنيه.",
                height=120
            )
    if st.button("🗑️ مسح المحادثة والبدء من جديد", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.current_image = None
        st.session_state.last_processed_id = None
        st.rerun()

st.markdown(f"""
<div class="robot-header">
    <div class="robot-avatar">
        <div class="robot-eyes">
            <div class="eye"></div>
            <div class="eye"></div>
        </div>
    </div>
    <h2>🤖 أهلاً بك! أنا {robot_name}</h2>
    <p>ورّيني أي صورة أو افتح الكاميرا، وهقولك شايف إيه بصوتي فوراً ونتكلم سوا!</p>
</div>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_image" not in st.session_state:
    st.session_state.current_image = None
if "last_processed_id" not in st.session_state:
    st.session_state.last_processed_id = None

col1, col2 = st.columns([1, 1.3])

with col1:
    st.subheader("📸 عين الروبوت (الكاميرا / الصور)")
    input_type = st.radio("اختر الطريقة:", ["📸 الكاميرا المباشرة", "📁 رفع صورة"], horizontal=True)
    img_file = st.camera_input("التقط صورة ليراها الروبوت") if input_type == "📸 الكاميرا المباشرة" else st.file_uploader("ارفع صورة", type=["jpg", "jpeg", "png"])

    if img_file is not None:
        pil_img = Image.open(img_file)
        st.session_state.current_image = pil_img
        st.image(pil_img, caption="الصورة أمام الروبوت الآن", use_container_width=True)

with col2:
    st.subheader("💬 حوارك المباشر مع الروبوت")
    
    if img_file is not None:
        file_id = f"{img_file.name}_{img_file.size}"
        if st.session_state.last_processed_id != file_id:
            if not api_key:
                st.error("⚠️ تأكد من وضع GEMINI_API_KEY في Secrets.")
            else:
                with st.spinner("🤖 الروبوت يفحص الصورة ويتجهز للكلام..."):
                    try:
                        if mode == "🛍️ روبوت مبيعات بصري للمتاجر":
                            sys_prompt = f"""
                            أنت '{robot_name}'، روبوت ذكي ودود تعمل في مبيعات المتجر.
                            تحدث باللهجة المصرية المهذبة وبجمل قصيرة واضحة ومباشرة (مناسبة للنطق الصوتي).
                            1. اوصف ما تراه في الصورة بسرعة وذكاء.
                            2. قارنه بقائمة منتجات المتجر التالية:
                            {catalog_text}
                            3. اذكر هل هو متوفر وسعره، أو اقترح بديلاً واعرض رقم الواتساب ({whatsapp}) للحجز، ثم اسأل العميل إذا كان لديه أي استفسار آخر.
                            """
                        else:
                            sys_prompt = f"""
                            أنت '{robot_name}'، روبوت مساعد بصري ذكي وودود.
                            تحدث باللهجة المصرية الواضحة وبجمل مرتبة مناسبة للنطق الصوتي.
                            اوصف ما تراه في الصورة بدقة واقرأ أي نصوص مكتوبة فيها، ثم اسأل المستخدم إذا كان يريد معرفة تفاصيل أكثر.
                            """
                        
                        first_reply = ask_gemini([st.session_state.current_image, sys_prompt])
                        st.session_state.last_processed_id = file_id
                        st.session_state.chat_history = [{"role": "assistant", "content": first_reply}]
                        autoplay_audio(first_reply)
                    except Exception as e:
                        st.error(f"حدث خطأ: {e}")

    for msg in st.session_state.chat_history:
        avatar = "🤖" if msg["role"] == "assistant" else "🧑"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    follow_up = st.chat_input("اسأل الروبوت أي سؤال تاني عن الصورة أو الأسعار...")
    if follow_up:
        st.session_state.chat_history.append({"role": "user", "content": follow_up})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(follow_up)

        with st.chat_message("assistant", avatar="🤖"):
            if not api_key:
                st.error("⚠️ تأكد من وضع مفتاح API.")
            else:
                with st.spinner("🤖 الروبوت يفكر ويرد..."):
                    try:
                        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history])
                        chat_prompt = f"""
                        أنت '{robot_name}'. استمر في الحوار باللهجة المصرية المهذبة والمختصرة بناءً على الصورة المرفقة وسجل الحوار السابق:
                        {history_text}
                        بيانات المتجر (إن وجدت): {catalog_text}
                        سؤال المستخدم الحالي: {follow_up}
                        """
                        contents_payload = [st.session_state.current_image, chat_prompt] if st.session_state.current_image else [chat_prompt]
                        bot_reply = ask_gemini(contents_payload)
                        st.markdown(bot_reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
                        autoplay_audio(bot_reply)
                    except Exception as e:
                        st.error(f"حدث خطأ: {e}")
