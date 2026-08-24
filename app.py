import streamlit as st
import pandas as pd
import datetime
import time
from PIL import Image

# استيراد مكون المسح الفوري التلقائي عبر المتصفح
try:
    from streamlit_qr_bar_scanner import qr_bar_scanned_id
    HAS_LIVE_SCANNER = True
except ImportError:
    HAS_LIVE_SCANNER = False

# ... [بقية إعدادات الجلسة والدوال كما هي] ...

# --- داخل Tab 1: تسجيل الحضور ---
with tabs[0]:
    st.subheader("تسجيل الحضور")
    
    # ... [أزرار بدء وإغلاق الجلسة كالمعتاد] ...

    if st.session_state.session_start_time is not None:
        elapsed_min = int((time.time() - st.session_state.session_start_time) // 60)
        curr_score = max(0.0, round(10.0 - (elapsed_min * 0.2), 1))
        st.info(f"⏱️ زمن الاجتماع: {elapsed_min} دقيقة | درجة الحضور الآن: **{curr_score} / 10**")
    else:
        curr_score = 10.0

    st.divider()
    st.subheader("📷 المسح الفوري التلقائي للـ QR")
    
    detected_code = 0
    scan_mode = st.radio("اختر طريقة المسح:", ["الكاميرا المباشرة (مسح وتسجيل تلقائي)", "رفع صورة عالية الجودة"])
    
    if scan_mode == "الكاميرا المباشرة (مسح وتسجيل تلقائي)":
        st.write("ضع رمز الـ QR أمام الكاميرا وسيتم التعرف عليه وتسجيله فوراً:")
        
        if HAS_LIVE_SCANNER:
            # القارئ المباشر - يقرأ فوراً بدون الضغط على أي زر
            qr_code_scanned = qr_bar_scanned_id(key="qr_live_scanner")
            
            if qr_code_scanned:
                clean_digits = "".join(filter(str.isdigit, str(qr_code_scanned)))
                if clean_digits:
                    detected_code = int(clean_digits)
                    
                    # تسجيل الحضور تلقائياً فور التعرف على الكود
                    m = st.session_state.members[st.session_state.members["كود العضو"] == detected_code]
                    if not m.empty:
                        m_name = m.iloc[0]["اسم الكشاف"]
                        if detected_code not in st.session_state.scanned_members:
                            t_now = datetime.datetime.now().strftime("%H:%M:%S")
                            st.session_state.scanned_members[detected_code] = (t_now, curr_score)
                            st.success(f"🎉 تم التسجيل التلقائي: {m_name} | الدرجة: {curr_score}/10")
                            st.balloons()
                        else:
                            st.info(f"ℹ️ الكشاف {m_name} مسجل بالفعل في هذه الجلسة.")
                    else:
                        st.error(f"❌ الكود ({detected_code}) غير مسجل في دليل الكشافة!")
        else:
            st.warning("يرجى إضافة `streamlit-qr-bar-scanner` إلى ملف requirements.txt لتفعيل المسح المباشر التلقائي.")

    else:
        img_file = st.file_uploader("اختر صورة كارت الـ QR من الاستوديو", type=["png", "jpg", "jpeg"])
        if img_file is not None:
            extracted = extract_qr_code(img_file)
            if extracted:
                try:
                    detected_code = int(extracted)
                    st.success(f"🎯 تم استخراج الكود: {detected_code}")
                except ValueError:
                    st.warning(f"الرمز يحتوي على نص: {extracted}")

    st.divider()
    manual_code = st.number_input("أو أدخل الكود يدوياً:", step=1, value=0)
    
    if st.button("✅ تسجيل الحضور يدوياً"):
        code_to_use = manual_code if manual_code > 0 else detected_code
        if code_to_use > 0:
            m = st.session_state.members[st.session_state.members["كود العضو"] == code_to_use]
            if not m.empty:
                m_name = m.iloc[0]["اسم الكشاف"]
                t_now = datetime.datetime.now().strftime("%H:%M:%S")
                st.session_state.scanned_members[code_to_use] = (t_now, curr_score)
                st.success(f"تم تسجيل: {m_name} | الدرجة: {curr_score}/10")
            else:
                st.error("الكود غير مسجل في دليل الكشافة!")
