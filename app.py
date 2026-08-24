import streamlit as st
import pandas as pd
import datetime
import time
from PIL import Image

# مكتبة قراءة الـ QR والباركود السريعة (ZXing)
try:
    import zxingcpp
    HAS_ZXING = True
except ImportError:
    HAS_ZXING = False

# مكتبة fallback ثانوية لقراءة الباركود
try:
    from pyzbar.pyzbar import decode
    HAS_PYZBAR = True
except Exception:
    HAS_PYZBAR = False

# مكتبات الربط المباشر مع Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False


SPREADSHEET_ID = "1B4Ho5U0x0TDf36bu7KqxXnMZCnvAiVxzfLthX_ga94c"
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
            sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
            sheet.append_row(row_data)
            return True
    except Exception as e:
        st.error(f"خطأ في المزامنة السحابية ({sheet_name}): {str(e)}")
    return False


def load_data_from_gsheet(sheet_name):
    try:
        client = get_gsheet_client()
        if client:
            sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
            records = sheet.get_all_records()
            if records:
                return pd.DataFrame(records)
    except Exception as e:
        st.warning(f"تعذر جلب بيانات ({sheet_name}) من Google Sheets: {str(e)}")
    return pd.DataFrame()


def extract_qr_code(image_file):
    try:
        img = Image.open(image_file)
        
        if HAS_ZXING:
            results = zxingcpp.read_barcodes(img)
            if results:
                raw_text = results[0].text
                clean_digits = "".join(filter(str.isdigit, raw_text))
                return clean_digits if clean_digits else raw_text
        
        if HAS_PYZBAR:
            decoded = decode(img)
            if decoded:
                raw_text = decoded[0].data.decode("utf-8")
                clean_digits = "".join(filter(str.isdigit, raw_text))
                return clean_digits if clean_digits else raw_text
                
    except Exception as e:
        st.error(f"خطأ أثناء معالجة الصورة: {e}")
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
    </div>
""", unsafe_allow_html=True)


# --- تهيئة الحالة (Session State) ---
if 'members' not in st.session_state or st.session_state.members.empty:
    fetched_members = load_data_from_gsheet("الأعضاء")
    if not fetched_members.empty:
        st.session_state.members = fetched_members
    else:
        st.session_state.members = pd.DataFrame(columns=["كود العضو", "اسم الكشاف", "الفرقة", "رقم التليفون", "تاريخ الانضمام"])

if 'attendance' not in st.session_state:
    st.session_state.attendance = pd.DataFrame(columns=["التاريخ", "كود العضو", "اسم الكشاف", "حالة الحضور", "وقت التسجيل", "درجة الحضور"])

if 'scores' not in st.session_state or 'اسم الكشاف' not in st.session_state.scores.columns:
    st.session_state.scores = pd.DataFrame(columns=["تاريخ التقييم", "كود العضو", "اسم الكشاف", "نوع التقييم", "الدرجة (من 10)", "ملاحظات"])

if 'session_start_time' not in st.session_state:
    st.session_start_time = None

if 'scanned_members' not in st.session_state:
    st.session_state.scanned_members = {}


tabs = st.tabs(["⏱️ تسجيل الحضور", "📝 التقييمات", "👥 دليل الكشافة", "☁️ الشيت السحابي المباشر"])


# --- Tab 1: الحضور والغياب المباشر ---
with tabs[0]:
    st.subheader("تسجيل الحضور الفوري")
    
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
    st.subheader("📷 التقاط الكارت والتسجيل التلقائي")
    
    # التقاط الصورة (بمجرد التقاط الصورة يتم التنفيذ فوراً)
    img_file = st.camera_input("اضغط التقاط الصورة لقرائتها وتسجيلها فوراً")
    
    if img_file is not None:
        extracted = extract_qr_code(img_file)
        if extracted:
            try:
                code_val = int(extracted)
                m = st.session_state.members[st.session_state.members["كود العضو"] == code_val]
                if not m.empty:
                    m_name = m.iloc[0]["اسم الكشاف"]
                    if code_val not in st.session_state.scanned_members:
                        t_now = datetime.datetime.now().strftime("%H:%M:%S")
                        st.session_state.scanned_members[code_val] = (t_now, curr_score)
                        st.success(f"🎉 تم قراءة الكود وتسجيل الحضور فوراً: {m_name} (كود: {code_val})")
                        st.balloons()
                    else:
                        st.info(f"ℹ️ الكشاف {m_name} مسجل بالفعل في هذه الجلسة.")
                else:
                    st.error(f"❌ الكود المنسوخ ({code_val}) غير مسجل في دليل الكشافة!")
            except ValueError:
                st.warning(f"الـ QR يحتوي على نص: {extracted}")
        else:
            st.error("❌ لم يتم التعرف على الرمز، يرجى التقاط صورة أقرب وأوضح للـ QR.")

    st.divider()
    
    # إدخال يدوي سريع
    with st.form("manual_attendance_form"):
        manual_code = st.number_input("أو أدخل الكود يدوياً اضغط تسجيل:", step=1, value=0)
        submit_manual = st.form_submit_button("✅ تسجيل يدوي سريع")
        
        if submit_manual and manual_code > 0:
            m = st.session_state.members[st.session_state.members["كود العضو"] == manual_code]
            if not m.empty:
                m_name = m.iloc[0]["اسم الكشاف"]
                if manual_code not in st.session_state.scanned_members:
                    t_now = datetime.datetime.now().strftime("%H:%M:%S")
                    st.session_state.scanned_members[manual_code] = (t_now, curr_score)
                    st.success(f"🎉 تم تسجيل: {m_name} | الدرجة: {curr_score}/10")
                else:
                    st.info(f"ℹ️ الكشاف {m_name} مسجل بالفعل.")
            else:
                st.error("الكود غير مسجل في دليل الكشافة!")


# --- Tab 2: تقييمات النشاط الكشفي ---
with tabs[1]:
    st.subheader("📝 إضافة تقييم أو نشاط كشفي")
    with st.form("score_form"):
        s_code = st.number_input("كود الكشاف", step=1, value=1001)
        s_type = st.selectbox("نوع التقييم", ["الزي الكشفي", "السلوك والانضباط", "الأنشطة والمهارات", "الخدمة", "الاعتراف", "التناول"])
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
    
    if st.button("🔄 تحديث البيانات من Google Sheets"):
        updated_data = load_data_from_gsheet("الأعضاء")
        if not updated_data.empty:
            st.session_state.members = updated_data
            st.success("تم تحديث قائمة الأعضاء بنجاح!")
            st.rerun()

    with st.form("add_member"):
        m_name = st.text_input("اسم الكشاف رباعي")
        m_dept = st.selectbox("الفرقة الكشفية", ["كشاف", "متقدم", "جوال", "مرشدات", "جوالات", "قادة"])
        m_phone = st.text_input("رقم التليفون", placeholder="01xxxxxxxxx")
        
        if st.form_submit_button("إضافة لخدمة الكشافة") and m_name:
            max_c = st.session_state.members["كود العضو"].max() if not st.session_state.members.empty else 21820261
            new_c = int(max_c + 1)
            t_date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            append_to_google_sheet("الأعضاء", [new_c, m_name, m_dept, m_phone, t_date])
            
            new_m = {
                "كود العضو": new_c, 
                "اسم الكشاف": m_name, 
                "الفرقة": m_dept, 
                "رقم التليفون": m_phone, 
                "تاريخ الانضمام": t_date
            }
            st.session_state.members = pd.concat([st.session_state.members, pd.DataFrame([new_m])], ignore_index=True)
            st.success(f"تم تسجيل {m_name} ورقم التليفون ({m_phone}) - الكود: {new_c}")

    st.dataframe(st.session_state.members, use_container_width=True)


# --- Tab 4: فتح الشيت المباشر ---
with tabs[3]:
    st.subheader("☁️ شيت Google Sheets السحابي التفاعلي")
    st.info("البيانات تُحفظ تلقائياً في شيت جوجل بدون أي تدخل يدوي.")
    
    st.link_button("🔗 فتح Google Sheets في نافذة جديدة للتعديل المباشر", SHEET_FULL_URL)
