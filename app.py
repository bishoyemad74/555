import streamlit as st

st.markdown("""
    <style>
        /* إخفاء الهيدر والفوتر والقوائم */
        #MainMenu, header, footer, [data-testid="stHeader"], [data-testid="stToolbar"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* تمديد مساحة التطبيق لتغطي أسفل الشاشة وتخفي أي شريط خارجي */
        .main .block-container {
            padding-bottom: 0rem !important;
            margin-bottom: -50px !important;
        }
        
        body, .stApp {
            margin-bottom: -50px !important;
        }
    </style>
""", unsafe_allow_html=True)
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


import json
import os
from google.oauth2.service_account import Credentials
import gspread

def get_gsheet_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds_dict = None
    
    # 1. محاولة القراءة من متغير البيئة المباشر (Railway)
    if "GCP_JSON" in os.environ:
        try:
            creds_dict = json.loads(os.environ["GCP_JSON"])
        except Exception:
            pass
            
    # 2. إذا لموا تجدها، ابحث في الطريقة العادية (st.secrets للمحلي)
    if not creds_dict:
        try:
            if "gcp_service_account" in st.secrets:
                creds_dict = dict(st.secrets["gcp_service_account"])
        except Exception:
            pass
            
    if creds_dict:
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(creds)
        
    return None    # ... باقي الكود الأصلي
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


def verify_current_password(username, current_password):
    """التحقق من صحة كلمة السر الحالية للمستخدم"""
    try:
        users_df = load_data_from_gsheet("المستخدمين")
        if not users_df.empty:
            match = users_df[
                (users_df["اسم المستخدم"].astype(str).str.strip() == str(username).strip()) & 
                (users_df["كلمة السر"].astype(str).str.strip() == str(current_password).strip())
            ]
            return not match.empty
    except Exception as e:
        st.error(f"خطأ أثناء التحقق من كلمة السر الحالية: {e}")
    return False


def update_user_password_in_gsheet(username, new_password):
    """تحديث كلمة السر لمستخدم معين في ورقة المستخدمين سحابياً"""
    try:
        client = get_gsheet_client()
        if client:
            sheet = client.open_by_key(SPREADSHEET_ID).worksheet("المستخدمين")
            records = sheet.get_all_records()
            if records:
                df = pd.DataFrame(records)
                df.columns = df.columns.astype(str).str.strip()
                
                # البحث عن رقم الصف بناءً على اسم المستخدم
                for idx, row in df.iterrows():
                    if str(row.get("اسم المستخدم", "")).strip() == str(username).strip():
                        row_number = idx + 2
                        sheet.update_cell(row_number, 2, str(new_password).strip())
                        return True
    except Exception as e:
        st.error(f"خطأ أثناء تحديث كلمة السر سحابياً: {str(e)}")
    return False


def update_leaderboard_in_gsheet(df_leaderboard):
    """تحديث شيت لوحة الصدارة في Google Sheets بالكامل"""
    try:
        client = get_gsheet_client()
        if client:
            sh = client.open_by_key(SPREADSHEET_ID)
            try:
                sheet = sh.worksheet("ترتيب الأعضاء")
            except Exception:
                sheet = sh.add_worksheet(title="ترتيب الأعضاء", rows="100", cols="10")
            
            sheet.clear()
            headers = df_leaderboard.columns.tolist()
            data = df_leaderboard.astype(str).values.tolist()
            sheet.update([headers] + data)
            return True
    except Exception as e:
        st.error(f"خطأ في تحديث شيت الترتيب السحابي: {str(e)}")
    return False


def load_data_from_gsheet(sheet_name):
    try:
        client = get_gsheet_client()
        if client:
            sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
            records = sheet.get_all_records()
            if records:
                df = pd.DataFrame(records)
                df.columns = df.columns.astype(str).str.strip()
                return df
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


def check_login(username, password):
    """التحقق من الدخول وجلب الصلاحيات التفصيلية من النص المدمج بالخلية"""
    try:
        users_df = load_data_from_gsheet("المستخدمين")
        if not users_df.empty:
            user_match = users_df[
                (users_df["اسم المستخدم"].astype(str).str.strip() == str(username).strip()) & 
                (users_df["كلمة السر"].astype(str).str.strip() == str(password).strip())
            ]
            if not user_match.empty:
                row = user_match.iloc[0]
                role = str(row.get("الصلاحية", "مستخدم")).strip()
                
                raw_perms = str(row.get("القوائم المتاحة", "")).strip()
                
                if role == "آدمن":
                    permissions = {
                        "can_attendance": True,
                        "can_evaluations": True,
                        "can_leaderboard": True,
                        "can_directory": True,
                        "can_sheet": True
                    }
                else:
                    permissions = {
                        "can_attendance": "تسجيل الحضور" in raw_perms,
                        "can_evaluations": "التقييمات" in raw_perms,
                        "can_leaderboard": "لوحة الصدارة" in raw_perms,
                        "can_directory": "دليل الكشافة" in raw_perms,
                        "can_sheet": "الشيت السحابي" in raw_perms
                    }

                return True, role, permissions
    except Exception as e:
        st.error(f"خطأ أثناء التحقق من بيانات الدخول: {e}")
    return False, None, {}


# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="كشافة أم النور",
    page_icon="⚜️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- إخفاء كافة خيارات المطور والشريط السفلي (Hosted with Streamlit) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Tajawal', sans-serif;
        direction: rtl;
        text-align: right;
    }
    
    #MainMenu {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    header {visibility: hidden !important; display: none !important;}
    .stDeployButton {display: none !important;}
    
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="manage-app-button"] {display: none !important;}
    
    /* إخفاء إشارات وشريط Streamlit السفلي بالتفصيل */
    .stAppViewerFooter {display: none !important;}
    footer[data-testid="stFooter"] {display: none !important;}
    div[class*="stAppViewerFooter"] {display: none !important;}
    div[class*="viewerBadge"] {display: none !important;}
    div[class*="styles_viewerBadge"] {display: none !important;}
    .viewerBadge_container__1tB92,
    ._profileContainer_gz836_1,
    .viewerBadge_link__1S137,
    div[data-testid="stSidebarCollapseButton"] {
        display: none !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    .stButton>button {
        width: 100%;
        background-color: #1565C0;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 12px;
        font-size: 16px;
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
        <h2> كشافة أم النور ⚜️ </h2>
    </div>
""", unsafe_allow_html=True)


# --- تهيئة حالة الجلسة والتسجيل ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "current_username" not in st.session_state:
    st.session_state.current_username = ""
if "permissions" not in st.session_state:
    st.session_state.permissions = {
        "can_attendance": True,
        "can_evaluations": True,
        "can_leaderboard": True,
        "can_directory": True,
        "can_sheet": False
    }


# --- 🔐 شاشة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.subheader("🔐 تسجيل الدخول للبرنامج")
    
    with st.form("login_form"):
        u_name = st.text_input("اسم المستخدم")
        u_pass = st.text_input("كلمة السر", type="password")
        btn_login = st.form_submit_button("دخول")
        
        if btn_login:
            if u_name.strip() and u_pass.strip():
                is_valid, role, perms = check_login(u_name, u_pass)
                if is_valid:
                    st.session_state.logged_in = True
                    st.session_state.user_role = role
                    st.session_state.current_username = u_name
                    st.session_state.permissions = perms
                    st.success(f"مرحباً بك ({u_name})! جاري التحميل...")
                    st.rerun()
                else:
                    st.error("❌ اسم المستخدم أو كلمة السر غير صحيحة.")
            else:
                st.warning("يرجى كتابة اسم المستخدم وكلمة السر.")
                
    st.stop()


# --- شريط معلومات الحساب وتسجيل الخروج وتغيير كلمة السر ---
col_user_info, col_pwd, col_logout = st.columns([2.5, 1.2, 1])
with col_user_info:
    st.info(f"👤 **المستخدم:** {st.session_state.current_username} | **الصلاحية:** {st.session_state.user_role}")

with col_pwd:
    @st.dialog("🔑 تغيير كلمة السر")
    def change_password_dialog():
        st.write(f"تغيير كلمة السر لحساب: **{st.session_state.current_username}**")
        with st.form("change_pass_form"):
            old_p = st.text_input("كلمة السر الحالية", type="password")
            new_p1 = st.text_input("كلمة السر الجديدة", type="password")
            new_p2 = st.text_input("تأكيد كلمة السر الجديدة", type="password")
            btn_save = st.form_submit_button("تحديث كلمة السر")
            
            if btn_save:
                if not old_p.strip():
                    st.error("❌ يرجى إدخال كلمة السر الحالية أولاً.")
                elif not new_p1.strip():
                    st.error("❌ يرجى إدخال كلمة سر جديدة.")
                elif new_p1 != new_p2:
                    st.error("❌ كلمة السر الجديدة وتأكيدها غير متطابقتين!")
                else:
                    with st.spinner("جاري التحقق من كلمة السر الحالية..."):
                        if verify_current_password(st.session_state.current_username, old_p):
                            if update_user_password_in_gsheet(st.session_state.current_username, new_p1):
                                st.success("🎉 تم تغيير كلمة السر بنجاح ورُفعت للشيت السحابي!")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("حدث خطأ أثناء الاتصال بـ Google Sheets.")
                        else:
                            st.error("❌ كلمة السر الحالية غير صحيحة!")

    if st.button("🔑 كلمة السر"):
        change_password_dialog()

with col_logout:
    if st.button("🚪 خروج"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.current_username = ""
        st.session_state.permissions = {}
        st.rerun()

st.divider()


# --- تهيئة البيانات (Session State) ---
if 'members' not in st.session_state or st.session_state.members.empty:
    fetched_members = load_data_from_gsheet("الأعضاء")
    if not fetched_members.empty:
        st.session_state.members = fetched_members
    else:
        st.session_state.members = pd.DataFrame(columns=["كود العضو", "اسم الكشاف", "الفرقة", "رقم التليفون", "تاريخ الانضمام"])

if 'attendance' not in st.session_state:
    st.session_state.attendance = load_data_from_gsheet("الحضور")
    if st.session_state.attendance.empty:
        st.session_state.attendance = pd.DataFrame(columns=["التاريخ", "كود العضو", "اسم الكشاف", "حالة الحضور", "وقت التسجيل", "درجة الحضور"])

if 'scores' not in st.session_state:
    st.session_state.scores = load_data_from_gsheet("التقييمات")
    if st.session_state.scores.empty:
        st.session_state.scores = pd.DataFrame(columns=["تاريخ التقييم", "كود العضو", "اسم الكشاف", "نوع التقييم", "الدرجة (من 10)", "ملاحظات"])

if 'session_start_time' not in st.session_state:
    st.session_state.session_start_time = None

if 'scanned_members' not in st.session_state:
    st.session_state.scanned_members = {}

if 'eval_scanned_code' not in st.session_state:
    st.session_state.eval_scanned_code = ""

if 'show_eval_camera' not in st.session_state:
    st.session_state.show_eval_camera = False


# --- بناء القوائم المتاحة بناءً على الصلاحيات ---
available_tabs = []
tab_keys = []

if st.session_state.permissions.get("can_attendance", True):
    available_tabs.append("⏱️ تسجيل الحضور")
    tab_keys.append("attendance")

if st.session_state.permissions.get("can_evaluations", True):
    available_tabs.append("📝 التقييمات")
    tab_keys.append("evaluations")

if st.session_state.permissions.get("can_leaderboard", True):
    available_tabs.append("🏆 لوحة الصدارة")
    tab_keys.append("leaderboard")

if st.session_state.permissions.get("can_directory", True):
    available_tabs.append("👥 دليل الكشافة")
    tab_keys.append("directory")

if st.session_state.permissions.get("can_sheet", False) or st.session_state.user_role == "آدمن":
    available_tabs.append("☁️ الشيت السحابي")
    tab_keys.append("sheet_link")

if st.session_state.user_role == "آدمن":
    available_tabs.append("⚙️ إدارة الحسابات")
    tab_keys.append("accounts")

if not available_tabs:
    st.warning("⚠️ لا توجد صلاحيات لعرض أي قوائم. يرجى المراجعة مع مسؤول النظام.")
    st.stop()

tabs = st.tabs(available_tabs)
tab_dict = {key: tabs[i] for i, key in enumerate(tab_keys)}


# --- Tab: تسجيل الحضور ---
if "attendance" in tab_dict:
    with tab_dict["attendance"]:
        st.subheader("تسجيل الحضور الفوري")
        
        col_start, col_stop = st.columns(2)
        with col_start:
            if st.button("🚀 بدء الاجتماع / الجلسة"):
                st.session_state.session_start_time = time.time()
                st.session_state.scanned_members = {}
                st.success("بدأت الجلسة! الدرجة الحالية 10/10.")
                st.rerun()
                
        with col_stop:
            if st.button("🔴 إغلاق الجلسة وترحيل البيانات للسحاب فورا"):
                if st.session_state.session_start_time is not None:
                    today = datetime.datetime.now().strftime("%Y-%m-%d")
                    new_att = []
                    for _, row in st.session_state.members.iterrows():
                        c = row.get("كود العضو", "")
                        n = row.get("اسم الكشاف", row.get("الاسم", "غير معروف"))
                        
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
                    st.rerun()
                else:
                    st.warning("لا توجد جلسة نشطة حالياً.")

        if st.session_state.session_start_time is not None:
            elapsed_min = int((time.time() - st.session_state.session_start_time) // 60)
            curr_score = max(0.0, round(10.0 - (elapsed_min * 0.2), 1))
            st.info(f"⏱️ زمن الاجتماع: {elapsed_min} دقيقة | درجة الحضور الآن: **{curr_score} / 10**")
        else:
            curr_score = 10.0

        st.divider()
        
        if st.session_state.session_start_time is not None:
            st.subheader("📷 التقاط الكارت والتسجيل التلقائي")
            img_file = st.camera_input("اضغط التقاط الصورة لقرائتها وتسجيلها فوراً")
            
            if img_file is not None:
                extracted = extract_qr_code(img_file)
                if extracted:
                    try:
                        code_val = int(extracted)
                        m = st.session_state.members[st.session_state.members["كود العضو"] == code_val]
                        if not m.empty:
                            row_data = m.iloc[0]
                            m_name = row_data.get("اسم الكشاف", row_data.get("الاسم", "كشاف"))
                            
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
        else:
            st.info("💡 اضغط على زر **🚀 بدء الاجتماع / الجلسة** أعلاه لفتح الكاميرا وبدء التسجيل.")

        st.divider()
        
        with st.form("manual_attendance_form"):
            manual_code_str = st.text_input("أو أدخل الكود يدوياً واضغط تسجيل:", value="")
            submit_manual = st.form_submit_button("✅ تسجيل يدوي سريع")
            
            if submit_manual and manual_code_str.strip():
                try:
                    manual_code = int(manual_code_str.strip())
                    m = st.session_state.members[st.session_state.members["كود العضو"] == manual_code]
                    if not m.empty:
                        row_data = m.iloc[0]
                        m_name = row_data.get("اسم الكشاف", row_data.get("الاسم", "كشاف"))
                        if manual_code not in st.session_state.scanned_members:
                            t_now = datetime.datetime.now().strftime("%H:%M:%S")
                            st.session_state.scanned_members[manual_code] = (t_now, curr_score)
                            st.success(f"🎉 تم تسجيل: {m_name} | الدرجة: {curr_score}/10")
                        else:
                            st.info(f"ℹ️ الكشاف {m_name} مسجل بالفعل.")
                    else:
                        st.error("الكود غير مسجل في دليل الكشافة!")
                except ValueError:
                    st.error("يرجى إدخال أرقام فقط لكود الكشاف.")


# --- Tab: تقييمات النشاط الكشفي ---
if "evaluations" in tab_dict:
    with tab_dict["evaluations"]:
        st.subheader("📝 إضافة تقييم أو نشاط كشفي")

        col_cam_btn, _ = st.columns([1, 1])
        with col_cam_btn:
            if st.button("📷 فتح/إغلاق الكاميرا لمسح الكود"):
                st.session_state.show_eval_camera = not st.session_state.show_eval_camera
                st.rerun()

        if st.session_state.show_eval_camera:
            eval_img = st.camera_input("التقط صورة كارت الكشاف للتقييم", key="eval_cam")
            if eval_img is not None:
                extracted_eval = extract_qr_code(eval_img)
                if extracted_eval:
                    st.session_state.eval_scanned_code = str(extracted_eval)
                    st.session_state.show_eval_camera = False
                    st.success(f"تم التقاط الكود: {extracted_eval}")
                    st.rerun()
                else:
                    st.error("لم يتم التعرف على الرمز، يرجى المحاولة مرة أخرى.")

        s_code_input = st.text_input("كود الكشاف", value=st.session_state.eval_scanned_code, placeholder="أدخل الكود أو امسحه بالكاميرا")

        found_member_name = None
        if s_code_input.strip():
            try:
                check_code = int(s_code_input.strip())
                matched = st.session_state.members[st.session_state.members["كود العضو"] == check_code]
                if not matched.empty:
                    row_found = matched.iloc[0]
                    found_member_name = row_found.get("اسم الكشاف", row_found.get("الاسم", "غير معروف"))
                    st.success(f"👤 **اسم الكشاف:** {found_member_name}")
                else:
                    st.error("❌ الكود المدخل غير موجود في دليل الكشافة.")
            except ValueError:
                st.error("⚠️ يرجى إدخال أرقام فقط للكود.")

        with st.form("score_form"):
            s_type = st.selectbox("نوع التقييم", ["الزي الكشفي", "السلوك والانضباط", "الأنشطة والمهارات", "الخدمة", "الاعتراف", "التناول"])
            s_val = st.number_input("الدرجة (من 10)", min_value=0.0, max_value=10.0, step=0.5, value=10.0)
            s_notes = st.text_input("ملاحظات / اسم النشاط")
            
            if st.form_submit_button("حفظ التقييم والمزامنة السحابية"):
                if found_member_name and s_code_input.strip():
                    try:
                        s_code = int(s_code_input.strip())
                        t_date = datetime.datetime.now().strftime("%Y-%m-%d")
                        
                        append_to_google_sheet("التقييمات", [t_date, s_code, found_member_name, s_type, s_val, s_notes])
                        st.session_state.eval_scanned_code = ""
                        st.success(f"تم تسجيل تقييم ({s_type}) للكشاف {found_member_name} وحفظه في Google Sheets!")
                    except ValueError:
                        st.error("حدث خطأ أثناء معالجة الكود.")
                else:
                    st.warning("يرجى التأكد من إدخال كود صحيح لكشاف موجود قبل الحفظ.")


# --- Tab: 🏆 لوحة الصدارة والترتيب ---
if "leaderboard" in tab_dict:
    with tab_dict["leaderboard"]:
        st.subheader("🏆 ترتيب الكشافة حسَب إجمالي الدرجات")
        
        col_ref, col_sync = st.columns(2)
        leaderboard = pd.DataFrame()

        if not st.session_state.members.empty:
            members_df = st.session_state.members.copy()
            code_col = [c for c in members_df.columns if "كود" in c or "Code" in c]
            name_col = [c for c in members_df.columns if "اسم" in c or "Name" in c]
            group_col = [c for c in members_df.columns if "فرقة" in c or "الفرقة" in c or "Group" in c]
            
            c_name = code_col[0] if code_col else members_df.columns[0]
            n_name = name_col[0] if name_col else members_df.columns[1] if len(members_df.columns) > 1 else c_name
            g_name = group_col[0] if group_col else None
            
            cols_to_use = [c_name, n_name]
            if g_name:
                cols_to_use.append(g_name)
                
            leaderboard = members_df[cols_to_use].copy()
            
            att_df = st.session_state.attendance
            if not att_df.empty:
                att_code_col = [c for c in att_df.columns if "كود" in c or "Code" in c]
                att_score_col = [c for c in att_df.columns if "درجة" in c or "Score" in c]
                
                if att_code_col and att_score_col:
                    ac = att_code_col[0]
                    asc = att_score_col[0]
                    att_df[asc] = pd.to_numeric(att_df[asc], errors="coerce").fillna(0)
                    att_sum = att_df.groupby(ac)[asc].sum().reset_index()
                    att_sum.columns = [c_name, "نقاط الحضور"]
                else:
                    att_sum = pd.DataFrame(columns=[c_name, "نقاط الحضور"])
            else:
                att_sum = pd.DataFrame(columns=[c_name, "نقاط الحضور"])

            sc_df = st.session_state.scores
            if not sc_df.empty:
                sc_code_col = [c for c in sc_df.columns if "كود" in c or "Code" in c]
                sc_val_col = [c for c in sc_df.columns if "الدرجة" in c or "درجة" in c or "Score" in c]
                
                if sc_code_col and sc_val_col:
                    scc = sc_code_col[0]
                    scv = sc_val_col[0]
                    sc_df[scv] = pd.to_numeric(sc_df[scv], errors="coerce").fillna(0)
                    sc_sum = sc_df.groupby(scc)[scv].sum().reset_index()
                    sc_sum.columns = [c_name, "نقاط التقييمات"]
                else:
                    sc_sum = pd.DataFrame(columns=[c_name, "نقاط التقييمات"])
            else:
                sc_sum = pd.DataFrame(columns=[c_name, "نقاط التقييمات"])

            leaderboard = leaderboard.merge(att_sum, on=c_name, how="left").fillna(0)
            leaderboard = leaderboard.merge(sc_sum, on=c_name, how="left").fillna(0)
            
            leaderboard["المجموع الكلي"] = leaderboard["نقاط الحضور"] + leaderboard["نقاط التقييمات"]
            leaderboard = leaderboard.sort_values(by="المجموع الكلي", ascending=False).reset_index(drop=True)
            leaderboard.index = leaderboard.index + 1

        with col_ref:
            if st.button("🔄 تحديث البيانات"):
                st.session_state.attendance = load_data_from_gsheet("الحضور")
                st.session_state.scores = load_data_from_gsheet("التقييمات")
                st.session_state.members = load_data_from_gsheet("الأعضاء")
                st.rerun()

        with col_sync:
            if st.button("☁️ رفع ترتيب الأعضاء إلى Google Sheets"):
                if not leaderboard.empty:
                    if update_leaderboard_in_gsheet(leaderboard):
                        st.success("تم تحديث ورقة 'ترتيب الأعضاء' داخل Google Sheets بنجاح! 🎉")
                else:
                    st.warning("لا توجد بيانات لرفعها.")

        if not leaderboard.empty:
            st.dataframe(leaderboard, use_container_width=True)
        else:
            st.info("لا توجد بيانات أعضاء متاحة لحساب الترتيب.")


# --- Tab: دليل الكشافة ---
if "directory" in tab_dict:
    with tab_dict["directory"]:
        st.subheader("👥 إضافة كشاف جديد")
        
        if st.button("🔄 تحديث البيانات من Google Sheets"):
            updated_data = load_data_from_gsheet("الأعضاء")
            if not updated_data.empty:
                st.session_state.members = updated_data
                st.success("تم تحديث قائمة الأعضاء بنجاح!")
                st.rerun()

        with st.form("add_member"):
            m_name = st.text_input("اسم الكشاف رباعي")
            m_phone = st.text_input("رقم التليفون", placeholder="01xxxxxxxxx")
            birth_date = st.date_input(
        "تاريخ الميلاد",
        value=datetime.date(2000, 1, 1),  # التاريخ الافتراضي عند الفتح
        min_value=datetime.date(1900, 1, 1),  # بداية الرينج
        max_value=datetime.date(3000, 1, 1)   # نهاية الرينج
    )
            academic_stage = st.selectbox(
        "المرحلة الدراسية", 
        ["ابتدائي", "إعدادي", "ثانوي", "جامعة", "أخرى"]
    )
            m_dept = st.selectbox("الفرقة الكشفية", ["كشاف", "متقدم", "جوال", "مرشدات", "جوالات", "قادة"])
            
            if st.form_submit_button("إضافة لخدمة الكشافة") and m_name:
                max_c = st.session_state.members["كود العضو"].max() if not st.session_state.members.empty else 21820260
                new_c = int(max_c + 1)
                t_date = datetime.datetime.now().strftime("%Y-%m-%d")
                
                append_to_google_sheet("الأعضاء", [new_c, m_name, m_phone,birth_date,academic_stage, m_dept, t_date])
                
                new_m = {
                    "كود العضو": new_c, 
                    "اسم الكشاف": m_name, 
                    "الفرقة": m_dept, 
                    "رقم التليفون": m_phone, 
                    "تاريخ الانضمام": t_date
                }
                st.session_state.members = pd.concat([st.session_state.members, pd.DataFrame([new_m])], ignore_index=True)
                st.success(f"تم تسجيل {m_name} وتحديث شيت الترتيب تلقائياً! - الكود: {new_c}")

        st.dataframe(st.session_state.members, use_container_width=True)


# --- Tab: فتح الشيت المباشر ---
if "sheet_link" in tab_dict:
    with tab_dict["sheet_link"]:
        st.subheader("☁️ شيت Google Sheets السحابي التفاعلي")
        st.info("البيانات تُحفظ تلقائياً في شيت جوجل بدون أي تدخل يدوي.")
        st.link_button("🔗 فتح Google Sheets في نافذة جديدة للتعديل المباشر", SHEET_FULL_URL)


# --- Tab: إدارة الحسابات (خاص بالآدمن فقط) ---
if "accounts" in tab_dict:
    with tab_dict["accounts"]:
        st.subheader("⚙️ إضافة مستخدم جديد وتحديد الصلاحيات الكاملة")
        
        with st.form("add_user_form"):
            new_u_name = st.text_input("اسم المستخدم الجديد")
            new_u_pass = st.text_input("كلمة السر الجديدة")
            new_u_role = st.selectbox("الصلاحية العامة", ["مستخدم", "آدمن"])
            
            selected_tabs = st.multiselect(
                "حدد القوائم المتاحة لهذا المستخدم:",
                ["تسجيل الحضور", "التقييمات", "لوحة الصدارة", "دليل الكشافة", "الشيت السحابي"],
                default=["تسجيل الحضور", "التقييمات", "لوحة الصدارة", "دليل الكشافة"]
            )
            
            submit_user = st.form_submit_button("إضافة الحساب وحفظه سحابياً")
            
            if submit_user and new_u_name.strip() and new_u_pass.strip():
                perms_str = ", ".join(selected_tabs)
                new_row = [
                    new_u_name.strip(),
                    new_u_pass.strip(),
                    new_u_role,
                    perms_str
                ]
                if append_to_google_sheet("المستخدمين", new_row):
                    st.success(f"تم إنشاء حساب للمستخدم ({new_u_name}) وتسجيل الصلاحيات ({perms_str}) بنجاح!")
                else:
                    st.error("حدث خطأ أثناء حفظ الحساب.")
        
        st.divider()
        st.subheader("📋 قائمة الحسابات والتحكم في الصلاحيات")
        users_list = load_data_from_gsheet("المستخدمين")
        if not users_list.empty:
            st.dataframe(users_list, use_container_width=True)
