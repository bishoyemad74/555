import streamlit as st
import pandas as pd
import datetime
import time
from PIL import Image

# مكتبات الربط المباشر مع Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

# محرك قراءة الباركود
try:
    from pyzbar.pyzbar import decode
    HAS_PYZBAR = True
except Exception:
    HAS_PYZBAR = False

# دالة الاتصال المباشر بشيت جوجل
def get_gsheet_client():
    if HAS_GSPREAD and "gcp_service_account" in st.secrets:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds)
    return None

# دالة حفظ صف جديد في شيت جوجل فوراً
# ضع الـ ID الخاص بشيت جوجل هنا
SPREADSHEET_ID = "1B4Ho5U0x0TDf36bu7KqxXnMZCnvAiVxzfLthX_ga94c"

def append_to_google_sheet(sheet_name, row_data):
    try:
        client = get_gsheet_client()
        if client:
            # الفتح عن طريق الـ ID أضمن بكثير من الاسم
            sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
            sheet.append_row(row_data)
            return True
    except Exception as e:
        # عرض نص الخطأ الحقيقي بدلاً من كائن الاستجابة
        st.error(f"خطأ في المزامنة السحابية ({sheet_name}): {str(e)}")
    return False
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
                new_att, new_sc = [], []
                for _, row in st.session_state.members.iterrows():
                    c, n = row["كود العضو"], row["اسم الكشاف"]
                    if c in st.session_state.scanned_members:
                        t_str, sc = st.session_state.scanned_members[c]
                        st_name = "حاضر"
                    else:
                        t_str, sc, st_name = "تلقائي", 0.0, "غائب"
                    
                    # حفظ محلي + رفع سحابي تلقائي
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
    st.subheader("📷 مسح كارت الـ QR")
    
    detected_code = 0
    scan_mode = st.radio("اختر طريقة المسح الضوئي:", ["رفع صورة عالية الجودة (أدق وأسرع)", "فتح الكاميرا المباشرة"])
    
    img_file = None
    if scan_mode == "رفع صورة عالية الجودة (أدق وأسرع)":
        img_file = st.file_uploader("اختر صورة كارت الـ QR من الاستوديو", type=["png", "jpg", "jpeg"])
    else:
        img_file = st.camera_input("وجّه الكاميرا إلى الكارت واضغط التقاط")
    
    if img_file is not None and HAS_PYZBAR:
        try:
            img = Image.open(img_file)
            decoded_objs = decode(img)
            if decoded_objs:
                qr_data = decoded_objs[0].data.decode("utf-8")
                clean_code = "".join(filter(str.isdigit, qr_data))
                if clean_code:
                    detected_code = int(clean_code)
                    st.success(f"🎯 تم استخراج الكود بنجاح: {detected_code}")
                else:
                    st.warning(f"الـ QR يحتوي على نص وليس رقماً: {qr_data}")
            else:
                st.error("لم يتم التعرف على الرمز. تأكد من وضوح الصورة وتدفق الإضاءة.")
        except Exception:
            st.error("حدث خطأ أثناء معالجة الصورة.")

    manual_code = st.number_input("أو ادخل الكود يدوياً:", step=1, value=detected_code)
    
    if st.button("✅ تسجيل الحضور"):
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
                
                # رفع سحابي آلي
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
            
            # رفع سحابي آلي
            append_to_google_sheet("الأعضاء", [new_c, m_name, m_dept, t_date])
            
            new_m = {"كود العضو": new_c, "اسم الكشاف": m_name, "الفرقة": m_dept, "تاريخ الانضمام": t_date}
            st.session_state.members = pd.concat([st.session_state.members, pd.DataFrame([new_m])], ignore_index=True)
            st.success(f"تم تسجيل {m_name} وحفظه في السحاب - الكود: {new_c}")

    st.dataframe(st.session_state.members, use_container_width=True)

# --- Tab 4: فتح الشيت المباشر ---
with tabs[3]:
    st.subheader("☁️ شيت Google Sheets السحابي التفاعلي")
    st.info("البيانات تُحفظ تلقائياً في شيت جوجل بدون أي تدخل يدوي منك.")
    
    sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit"
    st.link_button("🔗 فتح Google Sheets في نافذة جديدة للتعديل المباشر", sheet_url)
