import os
import io
import streamlit as st
from google import genai
from PIL import Image
from pypdf import PdfReader
from gtts import gTTS

st.set_page_config(page_title="Hagar Visual AI - المساعد البصري الذكي", page_icon="👁️", layout="wide")

try:
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
except Exception:
    api_key = os.getenv("GEMINI_API_KEY")

st.markdown("""
<style>
    @import url('https://googleapis.com');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .banner {
        background: linear-gradient(135deg, #2563EB 0%, #8B5CF6 100%);
        padding: 24px; border-radius: 18px; color: white; text-align: center; margin-bottom: 20px;
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.25);
    }
    .stButton > button {
        border-radius: 12px; font-weight: 700; background: linear-gradient(135deg, #2563EB 0%, #8B5CF6 100%);
        color: white; border: none; padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ لوحة إعدادات النظام")
    mode = st.selectbox(
        "اختر وضع تشغيل المساعد البصري:",
        ["🛍️ مساعد مبيعات بصري للمتاجر", "👁️ مساعد بصري عام (وصف الصور وقراءة النصوص)"]
    )
    store_name = st.text_input("اسم الشركة / المتجر", value="Hagar Smart Store")
    whatsapp = st.text_input("رقم الواتساب للتواصل", value="01000000000")
    
    catalog_text = ""
    if mode == "🛍️ مساعد مبيعات بصري للمتاجر":
        st.divider()
        uploaded_catalog = st.file_uploader("📄 ارفع كتالوج المنتجات (PDF / TXT)", type=["pdf", "txt"])
        if uploaded_catalog:
            if uploaded_catalog.name.endswith(".pdf"):
                reader = PdfReader(uploaded_catalog)
                for page in reader.pages:
                    catalog_text += (page.extract_text() or "") + "\n"
            else:
                catalog_text = uploaded_catalog.read().decode("utf-8", errors="ignore")
            st.success("✅ تم تحميل الكتالوج بنجاح!")
        else:
            catalog_text = st.text_area(
                "قائمة المنتجات والأسعار المتاحة:",
                value="1. لابتوب Dell Core i7 رام 16 - السعر 18,500 جنيه بضمان عام.\n2. ساعة ذكية Smart Watch Ultra - السعر 850 جنيه.\n3. سماعة بلوتوث عازلة للضوضاء - السعر 600 جنيه.\n4. كوتشي رياضي أبيض - السعر 650 جنيه (مقاسات 40-44).",
                height=140
            )
    enable_voice = st.checkbox("🔊 تفعيل القراءة الصوتية للنتيجة", value=True)

st.markdown(f"""
<div class="banner">
    <h2>👁️ المساعد البصري الذكي — {store_name}</h2>
    <p>نظام ذكاء اصطناعي متكامل لتحليل الصور والكاميرا ومطابقة المنتجات والرد بالصوت والنص</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ إدخال الصورة")
    input_type = st.radio("اختر مصدر الصورة:", ["📁 رفع صورة من الجهاز", "📸 التصوير بالكاميرا مباشرة"], horizontal=True)
    img_file = st.file_uploader("ارفع صورة (JPG, PNG)", type=["jpg", "jpeg", "png"]) if input_type == "📁 رفع صورة من الجهاز" else st.camera_input("التقط صورة الآن")
    user_question = st.text_input("سؤالك أو طلبك عن الصورة:", value="اوصف المنتج أو الشيء الموجود في الصورة، وهل هو متوفر في القائمة وكم سعره؟")

with col2:
    st.subheader("2️⃣ تحليل الذكاء الاصطناعي")
    if img_file:
        st.image(img_file, caption="الصورة المدخلة", use_container_width=True)
        if st.button("🚀 ابدأ التحليل البصري الآن", use_container_width=True):
            if not api_key:
                st.error("⚠️ تأكد من إضافة مفتاح GEMINI_API_KEY في إعدادات Secrets.")
            else:
                with st.spinner("جاري فحص الصورة وتحليل التفاصيل..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        pil_image = Image.open(img_file)

                        if mode == "🛍️ مساعد مبيعات بصري للمتاجر":
                            prompt_text = f"""
                            أنت مساعد مبيعات بصري ذكي تعمل في '{store_name}'.
                            1. افحص الصورة بدقة وحدد نوع الشيء أو المنتج ولونه ومواصفاته.
                            2. قارنه بقائمة منتجات المتجر المتاحة التالية:
                            ---
                            {catalog_text}
                            ---
                            3. رد باللهجة المصرية المهذبة وبإملاء عربي سليم: اذكر وصف المنتج، وهل هو متوفر في قائمتنا وسعره، ولو مش متوفر اقترح أقرب بديل أو اعرض التواصل عبر واتساب ({whatsapp}).
                            سؤال العميل: {user_question}
                            """
                        else:
                            prompt_text = f"""
                            أنت مساعد بصري ذكي لمساعدة المستخدمين والمكفوفين.
                            افحص الصورة بدقة، واوصف محتواها بوضوح وباللغة العربية السليمة، واقرأ أي نصوص مكتوبة بداخلها.
                            سؤال المستخدم: {user_question}
                            """

                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=[pil_image, prompt_text]
                        )
                        
                        reply = response.text
                        st.success("✅ نتيجة التحليل:")
                        st.markdown(reply)

                        if enable_voice:
                            tts = gTTS(text=reply, lang="ar")
                            audio_fp = io.BytesIO()
                            tts.write_to_fp(audio_fp)
                            audio_fp.seek(0)
                            st.audio(audio_fp, format="audio/mp3")

                    except Exception as e:
                        st.error(f"حدث خطأ: {e}")
    else:
        st.info("👈 ارفع صورة أو التقط صورة بالكاميرا من اليمين لتبدأ التحليل.")
