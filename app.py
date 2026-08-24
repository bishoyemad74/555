import streamlit as st
import pandas as pd
import datetime
import time
import numpy as np

# مكتبة OpenCV لمعالجة واستخراج الـ QR
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# مكتبة البث المباشر التلقائي للكاميرا بدون أزرار
try:
    from camera_input_live import camera_input_live
    HAS_LIVE_CAM = True
except ImportError:
    HAS_LIVE_CAM = False

# مكتبات Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False


SPREADSHEET_ID = "ضع_الـ_ID_الحقيقي_هنا"
SHEET_FULL_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"


def get_gsheet_client():
    if HAS_GSPREAD and "gcp_service_account" in st.secrets:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scope
        )
        return gspread.authorize(creds)
    return None


def append_to_google_sheet(sheet_name, row_data):
    try:
        client = get_gsheet_client()
        if client:
            doc = client.open_by_key(SPREADSHEET_ID)
            try:
                sheet = doc.worksheet(sheet_name)
            except Exception:
                sheet = doc.add_worksheet(title=sheet_name, rows="1000", cols="20")
            sheet.append_row(row_data)
            return True
    except Exception as e:
        st.error(f"خطأ في المزامنة السحابية ({sheet_name}): {str(e)}")
    return False


def extract_qr_code(image_bytes):
    try:
        if HAS_CV2:
            file_bytes = np.asarray(bytearray(image_bytes.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(img)
            if data:
                clean_digits = "".join(filter(str.isdigit, data))
                return clean_digits if clean_digits else data
    except Exception:
        pass
    return None


# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="كشافة أم النور",
    page_icon="⚜️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Tajawal', sans-serif;
        direction: rtl;
        text-align: right;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    .stButton>button {
        width: 100%;
        background-color: #1565C0;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px;
    }
    .header-box {
        background-color: #0D47A1;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="header-box">
        <h2>⚜️ كشافة أم النور ⚜️</h2>
        <p>نظام الحضور التنازلي والمزامنة السحابية المباشرة</p>
    </div>
""", unsafe_allow_html=True)

# إدارة Session State
if 'members' not in st.session_state or 'اسم الكشاف' not in st.session_state.members.columns:
    st.session_state.members = pd.DataFrame([
        {"كود العضو": 1001, "اسم الكشاف": "مينا سامح", "الفرقة": "فتيان", "تاريخ الانضمام": "2026-01-15"},
        {"كود العضو": 1002, "اسم الكشاف": "كيرلس جرجس", "الفرقة": "متقدم", "تاريخ الانضمام": "2026-01-15"},
        {"كود العضو": 1003, "اسم الكشاف": "بيشوي عماد", "الفرقة": "جوالة", "تاريخ الانضمام": "2026-01-20"}
    ])

if 'attendance' not in st.session_state:
    st.session_state.attendance = pd.DataFrame(columns=["التاريخ", "كود العضو", "اسم الكشاف", "حالة الحضور", "وقت التسجيل", "درجة الحضور"])

if 'scores' not in st.session_state or 'اسم الكشاف' not in st.session_state.scores.columns:
    st.session_state.scores = pd.DataFrame(columns=["تاريخ التقييم", "كود العضو", "اسم الكشاف", "نوع التقييم", "الدرجة (من 10)", "ملاحظات"])

if 'session_start_time' not in st.session_state:
    st.session_state.session_start_time = None

if 'scanned_members' not in st.session_state:
    st.session_state.scanned_members = {}

if 'current_scanned_code' not in st.session_state:
    st.session_state.current_scanned_code = 0

tabs = st.tabs(["⏱️ تسجيل الحضور", "📝 التقييمات", "👥 دليل الكشافة", "☁️ الشيت السحابي المباشر"])


# --- Tab 1: الحضور والغياب المباشر ---
with tabs[0]:
    st.subheader("⏱️ إدارة جلسة الحضور التنازلي")
    
    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("🚀 بدء الاجتماع / الجلسة"):
            st.session_state.session_start_time = time.time()
            st.session_state.scanned_members = {}
            st.success("بدأت الجلسة! الدرجة الحالية 10/10.")
            
    with col_stop:
        if st.button("🔴 إغلاق الجلسة وترحيل البيانات للسحاب فورا"):
            if st.session_state.session_start_time is not None:
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                new_att = []
                for _, row in st.session_state.members.iterrows():
                    c, n = row["كود العضو"], row["اسم الكشاف"]
                    if c in st.session_state.scanned_members:
                        t_str, sc = st.session_state.scanned_members[c]
                        st_name = "حاضر"
                    else:
                        t_str, sc, st_name = "تلقائي", 0.0, "غائب"
                    
                    row_data = [today, c, n, st_name, t_str, sc]
                    append_to_google_sheet("الحضور", row_data)
                    
                    new_att.append({
                        "التاريخ": today, "كود العضو": c, "اسم الكشاف": n,
                        "حالة الحضور": st_name, "وقت التسجيل": t_str, "درجة الحضور": sc
                    })
                
                st.session_state.attendance = pd.concat([st.session_state.attendance, pd.DataFrame(new_att)], ignore_index=True)
                st.session_state.session_start_time = None
                st.session_state.scanned_members = {}
                st.success("تم إغلاق الجلسة وترحيل البيانات مباشرة لـ Google Sheets! ☁️")
            else:
                st.warning("لا توجد جلسة نشطة حالياً.")

    if st.session_state.session_start_time is not None:
        elapsed_min = int((time.time() - st.session_state.session_start_time) // 60)
        curr_score = max(0.0, round(10.0 - (elapsed_min * 0.2), 1))
        st.info(f"⏱️ زمن الاجتماع: {elapsed_min} دقيقة | درجة الحضور الآن: **{curr_score} / 10**")
    else:
        curr_score = 10.0

    st.divider()
    st.subheader("📷 الكاميرا المباشرة التلقائية")

    # مسح البث المباشر
    if HAS_LIVE_CAM:
        image = camera_input_live()
        if image:
            extracted = extract_qr_code(image)
            if extracted:
                try:
                    code_val = int(extracted)
                    st.session_state.current_scanned_code = code_val
                    
                    # تسجيل تلقائي فور قراءة الكود
                    m = st.session_state.members[st.session_state.members["كود العضو"] == code_val]
                    if not m.empty:
                        m_name = m.iloc[0]["اسم الكشاف"]
                        if code_val not in st.session_state.scanned_members:
                            t_now = datetime.datetime.now().strftime("%H:%M:%S")
                            st.session_state.scanned_members[code_val] = (t_now, curr_score)
                            st.success(f"🎉 تم التسجيل التلقائي: {m_name} (كود: {code_val})")
                            st.balloons()
                except ValueError:
                    pass
    else:
        st.warning("جاري تحميل مكتبة البث المباشر...")

    st.divider()
    
    # مربع النص يتم تعبئته تلقائياً عند مسح الـ QR
    manual_code = st.number_input(
        "كود العضو (يتحدث تلقائياً عند وجه الكاميرا):", 
        step=1, 
        value=int(st.session_state.current_scanned_code)
    )
    
    if st.button("✅ تأكيد / تسجيل الحضور يدوياً"):
        code_to_use = manual_code
        if code_to_use > 0:
            m = st.session_state.members[st.session_state.members["كود العضو"] == code_to_use]
            if not m.empty:
                m_name = m.iloc[0]["اسم الكشاف"]
                if code_to_use not in st.session_state.scanned_members:
                    t_now = datetime.datetime.now().strftime("%H:%M:%S")
                    st.session_state.scanned_members[code_to_use] = (t_now, curr_score)
                    st.success(f"🎉 تم تسجيل: {m_name} | الدرجة: {curr_score}/10")
                    st.balloons()
                else:
                    st.info(f"ℹ️ الكشاف {m_name} مسجل بالفعل في هذه الجلسة.")
            else:
                st.error("الكود غير مسجل في دليل الكشافة!")


# --- Tab 2: تقييمات النشاط الكشفي ---
with tabs[1]:
    st.subheader("📝 إضافة تقييم أو نشاط كشفي")
    with st.form("score_form"):
        s_code = st.number_input("كود الكشاف", step=1, value=1001)
        s_type = st.selectbox("نوع التقييم", ["الزي الكشفي", "السلوك والانضباط", "الأنشطة والمهارات", "المخيمات والرحلات", "اختبارات الترقي"])
        s_val = st.number_input("الدرجة (من 10)", min_value=0.0, max_value=10.0, step=0.5, value=10.0)
        s_notes = st.text_input("ملاحظات / اسم النشاط")
        
        if st.form_submit_button("حفظ التقييم والمزامنة السحابية"):
            m = st.session_state.members[st.session_state.members["كود العضو"] == s_code]
            if not m.empty:
                m_name = m.iloc[0]["اسم الكشاف"]
                t_date = datetime.datetime.now().strftime("%Y-%m-%d")
                
                append_to_google_sheet("التقييمات", [t_date, s_code, m_name, s_type, s_val, s_notes])
                st.success(f"تم تسجيل تقييم ({s_type}) للكشاف {m_name} وحفظه في Google Sheets!")
            else:
                st.error("الكود غير موجود!")


# --- Tab 3: دليل الكشافة ---
with tabs[2]:
    st.subheader("👥 إضافة كشاف جديد")
    with st.form("add_member"):
        m_name = st.text_input("اسم الكشاف رباعي")
        m_dept = st.selectbox("الفرقة الكشفية", ["براعم", "أشبال", "فتيان", "متقدم", "جوالة", "قادة"])
        if st.form_submit_button("إضافة لخدمة الكشافة") and m_name:
            max_c = st.session_state.members["كود العضو"].max() if not st.session_state.members.empty else 1000
            new_c = int(max_c + 1)
            t_date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            append_to_google_sheet("الأعضاء", [new_c, m_name, m_dept, t_date])
            
            new_m = {"كود العضو": new_c, "اسم الكشاف": m_name, "الفرقة": m_dept, "تاريخ الانضمام": t_date}
            st.session_state.members = pd.concat([st.session_state.members, pd.DataFrame([new_m])], ignore_index=True)
            st.success(f"تم تسجيل {m_name} وحفظه في السحاب - الكود: {new_c}")

    st.dataframe(st.session_state.members, use_container_width=True)


# --- Tab 4: فتح الشيت المباشر ---
with tabs[3]:
    st.subheader("☁️ شيت Google Sheets السحابي التفاعلي")
    st.info("البيانات تُحفظ تلقائياً في شيت جوجل بدون أي تدخل يدوي.")
    
    st.link_button("🔗 فتح Google Sheets في نافذة جديدة للتعديل المباشر", SHEET_FULL_URL)
