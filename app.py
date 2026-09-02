import streamlit as st
import pandas as pd
import datetime
import time
from PIL import Image
import json
import os

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="كشافة أم النور",
    page_icon="⚜️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        #MainMenu, header, footer, [data-testid="stHeader"], [data-testid="stToolbar"] {
            display: none !important;
            visibility: hidden !important;
        }

        .main .block-container {
            padding-bottom: 0rem !important;
            margin-bottom: -50px !important;
        }
        
        body, .stApp {
            margin-bottom: -50px !important;
        }
    </style>
""", unsafe_allow_html=True)

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
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = None
    
    if "GCP_JSON" in os.environ:
        try:
            creds_dict = json.loads(os.environ["GCP_JSON"])
        except Exception:
            pass
            
    if not creds_dict:
        try:
            if "gcp_service_account" in st.secrets:
                creds_dict = dict(st.secrets["gcp_service_account"])
        except Exception:
            pass
            
    if creds_dict:
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(creds)
        
    return None


def append_to_google_sheet(sheet_name, row_data):
    try:
        client = get_gsheet_client()
        if client:
            sh = client.open_by_key(SPREADSHEET_ID)
            try:
                sheet = sh.worksheet(sheet_name)
            except Exception:
                sheet = sh.add_worksheet(title=sheet_name, rows="500", cols="10")
            sheet.append_row(row_data)
            return True
    except Exception as e:
        st.error(f"خطأ في المزامنة السحابية ({sheet_name}): {str(e)}")
    return False


def verify_current_password(username, current_password):
    try:
        users_df = load_data_from_gsheet("المستخدمين")
        if not users_df.empty and "اسم المستخدم" in users_df.columns and "كلمة السر" in users_df.columns:
            match = users_df[
                (users_df["اسم المستخدم"].astype(str).str.strip() == str(username).strip()) & 
                (users_df["كلمة السر"].astype(str).str.strip() == str(current_password).strip())
            ]
            return not match.empty
    except Exception as e:
        st.error(f"خطأ أثناء التحقق من كلمة السر الحالية: {e}")
    return False


def update_user_password_in_gsheet(username, new_password):
    try:
        client = get_gsheet_client()
        if client:
            sheet = client.open_by_key(SPREADSHEET_ID).worksheet("المستخدمين")
            records = sheet.get_all_records()
            if records:
                df = pd.DataFrame(records)
                df.columns = df.columns.astype(str).str.strip()
                
                for idx, row in df.iterrows():
                    if str(row.get("اسم المستخدم", "")).strip() == str(username).strip():
                        row_number = idx + 2
                        sheet.update_cell(row_number, 2, str(new_password).strip())
                        return True
    except Exception as e:
        st.error(f"خطأ أثناء تحديث كلمة السر سحابياً: {str(e)}")
    return False


def update_leaderboard_in_gsheet(df_leaderboard):
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
            sh = client.open_by_key(SPREADSHEET_ID)
            try:
                sheet = sh.worksheet(sheet_name)
            except Exception:
                return pd.DataFrame()
            records = sheet.get_all_records()
            if records:
                df = pd.DataFrame(records)
                df.columns = df.columns.astype(str).str.strip()
                return df
    except Exception as e:
        st.warning(f"تعذر جلب بيانات ({sheet_name}) من Google Sheets: {str(e)}")
    return pd.DataFrame()


def clear_gsheet_tab(sheet_name):
    try:
        client = get_gsheet_client()
        if client:
            sh = client.open_by_key(SPREADSHEET_ID)
            try:
                sheet = sh.worksheet(sheet_name)
                sheet.clear()
                return True
            except Exception:
                pass
    except Exception as e:
        st.error(f"خطأ أثناء تفريغ شيت ({sheet_name}): {e}")
    return False


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
    try:
        users_df = load_data_from_gsheet("المستخدمين")
        if not users_df.empty and "اسم المستخدم" in users_df.columns and "كلمة السر" in users_df.columns:
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
                        "can_directory": "الاعضاء" in raw_perms,
                        "can_sheet": "الشيت السحابي" in raw_perms
                    }

                return True, role, permissions
    except Exception as e:
        st.error(f"خطأ أثناء التحقق من بيانات الدخول: {e}")
    return False, None, {}


# --- إخفاء عناصر التحكم واستايل الصفحة ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Tajawal', sans-serif;
        direction: rtl;
        text-align: right;
    }
    
    #MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"] {display: none !important;}
    
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


# --- شريط معلومات الحساب وتسجيل الخروج ---
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


if "form_reset_counter" not in st.session_state:
    st.session_state.form_reset_counter = 0

if "eval_reset_counter" not in st.session_state:
    st.session_state.eval_reset_counter = 0


# --- تهيئة البيانات الجداول والتأكد من الأعمدة ---
if 'members' not in st.session_state or st.session_state.members.empty:
    fetched_members = load_data_from_gsheet("الأعضاء")
    if not fetched_members.empty:
        st.session_state.members = fetched_members
    else:
        st.session_state.members = pd.DataFrame(columns=["كود العضو", "اسم الكشاف", "الفرقة", "رقم التليفون", "تاريخ الانضمام"])

if 'attendance' not in st.session_state:
    st.session_state.attendance = load_data_from_gsheet("الحضور")

# التحقق والتأكد من وجود جميع أعمدة جدول الحضور
expected_att_cols = ["التاريخ", "كود العضو", "اسم الكشاف", "حالة الحضور", "وقت التسجيل", "درجة الحضور"]
if st.session_state.attendance.empty:
    st.session_state.attendance = pd.DataFrame(columns=expected_att_cols)
else:
    for col in expected_att_cols:
        if col not in st.session_state.attendance.columns:
            st.session_state.attendance[col] = 0.0 if col == "درجة الحضور" else ""

if 'scores' not in st.session_state:
    st.session_state.scores = load_data_from_gsheet("التقييمات")

expected_score_cols = ["تاريخ التقييم", "كود العضو", "اسم الكشاف", "نوع التقييم", "الدرجة (من 10)", "ملاحظات"]
if st.session_state.scores.empty:
    st.session_state.scores = pd.DataFrame(columns=expected_score_cols)
else:
    for col in expected_score_cols:
        if col not in st.session_state.scores.columns:
            st.session_state.scores[col] = 0.0 if col == "الدرجة (من 10)" else ""

if 'session_start_time' not in st.session_state:
    st.session_start_time = None

if 'scanned_members' not in st.session_state:
    st.session_state.scanned_members = {}

if 'eval_scanned_code' not in st.session_state:
    st.session_state.eval_scanned_code = ""

if 'show_eval_camera' not in st.session_state:
    st.session_state.show_eval_camera = False


# --- مزامنة الجلسة السحابية المشتركة (المسودة) ---
session_info = load_data_from_gsheet("حالة_الجلسة")
active_session = None

if not session_info.empty:
    open_rows = session_info[session_info.get("الحالة", "") == "مفتوحة"]
    if not open_rows.empty:
        active_session = open_rows.iloc[-1].to_dict()
        st.session_state.session_start_time = float(active_session.get("Start_Timestamp", time.time()))

if active_session:
    draft_df = load_data_from_gsheet("مسودة_الحضور")
    if not draft_df.empty and "كود العضو" in draft_df.columns:
        for _, d_row in draft_df.iterrows():
            c_code = d_row.get("كود العضو", "")
            t_str = str(d_row.get("وقت التسجيل", ""))
            sc_val = float(d_row.get("درجة الحضور", 10.0))
            if c_code:
                st.session_state.scanned_members[c_code] = (t_str, sc_val)


# --- القوائم والتنقل ---
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
    available_tabs.append("👥 الاعضاء")
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
        
        if active_session:
            st.warning(f"⚠️ توجد جلسة مفتوحة بدأها ({active_session.get('المستخدم', 'كابتن')}) بتاريخ {active_session.get('التاريخ', '')}")
        
        col_start, col_stop = st.columns(2)
        with col_start:
            if st.button("🚀 بدء الاجتماع / الجلسة"):
                now_ts = time.time()
                today_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                st.session_state.session_start_time = now_ts
                st.session_state.scanned_members = {}
                
                new_sess_row = [today_date, st.session_state.current_username, "مفتوحة", str(now_ts)]
                append_to_google_sheet("حالة_الجلسة", new_sess_row)
                
                st.success("بدأت الجلسة السحابية المشتركة! الدرجة الحالية 10/10.")
                st.rerun()
                
        with col_stop:
            if st.button("🔴 إغلاق الجلسة وترحيل البيانات للسحاب فورا"):
                if active_session or st.session_state.session_start_time is not None:
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
                    
                    clear_gsheet_tab("حالة_الجلسة")
                    clear_gsheet_tab("مسودة_الحضور")
                    
                    st.success("تم إغلاق الجلسة وترحيل البيانات مباشرة لـ Google Sheets! ☁️")
                    st.rerun()
                else:
                    st.warning("لا توجد جلسة نشطة حالياً.")

        if st.session_state.session_start_time is not None:
            elapsed_min = int((time.time() - st.session_state.session_start_time) // 60)
            curr_score = max(0.0, round(10.0 - (int(elapsed_min // 5) * 1.0), 1))
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
                            row_data_m = m.iloc[0]
                            m_name = row_data_m.get("اسم الكشاف", row_data_m.get("الاسم", "كشاف"))
                            
                            if code_val not in st.session_state.scanned_members:
                                t_now = datetime.datetime.now().strftime("%H:%M:%S")
                                st.session_state.scanned_members[code_val] = (t_now, curr_score)
                                
                                draft_row = [code_val, m_name, t_now, curr_score, st.session_state.current_username]
                                append_to_google_sheet("مسودة_الحضور", draft_row)
                                
                                st.success(f"✅ تم تسجيل حضور الكشاف: ({m_name}) بدرجة ({curr_score}) في المسودة السحابية!")
                            else:
                                st.warning(f"⚠️ الكشاف ({m_name}) مسجل بالفعل في هذه الجلسة.")
                        else:
                            st.error(f"❌ الكود الممسوح ({code_val}) غير موجود في قائمة الأعضاء!")
                    except ValueError:
                        st.error("❌ الكود المقروء غير صالح.")

            st.divider()
            
            st.subheader("📊 استعراض ومتابعة الجلسة المفتوحة حالياً")
            
            all_members_list = st.session_state.members["كود العضو"].tolist() if not st.session_state.members.empty else []
            present_codes = list(st.session_state.scanned_members.keys())
            absent_codes = [c for c in all_members_list if c not in present_codes]
            
            c_p_cnt, c_a_cnt, c_t_cnt = st.columns(3)
            with c_p_cnt:
                st.metric("✅ عدد الحاضرين", len(present_codes))
            with c_a_cnt:
                st.metric("❌ عدد الغائبين حتى الآن", len(absent_codes))
            with c_t_cnt:
                st.metric("👥 إجمالي الأعضاء", len(all_members_list))
                
            sub_tab_present, sub_tab_absent = st.tabs(["📋 الحاضرون بالمسودة السحابية", "⚠️ الغائبون حتى الآن"])
            
            with sub_tab_present:
                if st.session_state.scanned_members:
                    draft_data_list = []
                    for c_code, (t_val, sc_val) in st.session_state.scanned_members.items():
                        m = st.session_state.members[st.session_state.members["كود العضو"] == c_code]
                        name_val = m.iloc[0].get("اسم الكشاف", m.iloc[0].get("الاسم", "كشاف")) if not m.empty else "غير معروف"
                        squad_val = m.iloc[0].get("الفرقة", "-") if not m.empty else "-"
                        draft_data_list.append({
                            "كود العضو": c_code,
                            "اسم الكشاف": name_val,
                            "الفرقة": squad_val,
                            "وقت التسجيل": t_val,
                            "درجة الحضور": sc_val
                        })
                    st.dataframe(pd.DataFrame(draft_data_list), use_container_width=True)
                else:
                    st.info("لم يتم تسجيل أي كشاف في المسودة السحابية حتى الآن.")
                    
            with sub_tab_absent:
                if absent_codes:
                    absent_data_list = []
                    for a_code in absent_codes:
                        m = st.session_state.members[st.session_state.members["كود العضو"] == a_code]
                        if not m.empty:
                            row_m = m.iloc[0]
                            absent_data_list.append({
                                "كود العضو": a_code,
                                "اسم الكشاف": row_m.get("اسم الكشاف", row_m.get("الاسم", "غير معروف")),
                                "الفرقة": row_m.get("الفرقة", "-"),
                                "رقم التليفون": row_m.get("رقم التليفون", "-")
                            })
                    st.dataframe(pd.DataFrame(absent_data_list), use_container_width=True)
                else:
                    st.success("🎉 جميع الأعضاء حاضرون في الجلسة!")


# --- Tab: التقييمات ---
if "evaluations" in tab_dict:
    with tab_dict["evaluations"]:
        st.subheader("رصد وتقييم الأعضاء")
        
        col_btn_cam, col_reset_cam = st.columns([2, 1])
        with col_btn_cam:
            if st.button("📷 مسح كارت التقييم بـ الكاميرا"):
                st.session_state.show_eval_camera = not st.session_state.show_eval_camera
                
        if st.session_state.show_eval_camera:
            eval_img = st.camera_input("التقط صورة الكارت لتحديد العضو للتقييم")
            if eval_img is not None:
                extracted_eval = extract_qr_code(eval_img)
                if extracted_eval:
                    st.session_state.eval_scanned_code = extracted_eval
                    st.success(f"تم التعرف على الكود: {extracted_eval}")
                    st.session_state.show_eval_camera = False
                    st.rerun()

        with st.form(f"eval_form_{st.session_state.eval_reset_counter}"):
            eval_date = st.date_input("تاريخ التقييم", datetime.date.today())
            
            member_list = st.session_state.members["اسم الكشاف"].tolist() if "اسم الكشاف" in st.session_state.members.columns else st.session_state.members["الاسم"].tolist() if not st.session_state.members.empty else []
            
            selected_idx = 0
            if st.session_state.eval_scanned_code and not st.session_state.members.empty:
                try:
                    c_val = int(st.session_state.eval_scanned_code)
                    match = st.session_state.members[st.session_state.members["كود العضو"] == c_val]
                    if not match.empty:
                        m_name = match.iloc[0].get("اسم الكشاف", match.iloc[0].get("الاسم", ""))
                        if m_name in member_list:
                            selected_idx = member_list.index(m_name)
                except Exception:
                    pass

            selected_member = st.selectbox("اختر العضو", member_list, index=selected_idx if member_list else 0)
            eval_type = st.selectbox("نوع التقييم", ["سلوك وانتظام", "أنشطة واجتماعات", "الزي الكشفي", "افتراضية أخرى"])
            eval_score = st.slider("الدرجة (من 10)", 0.0, 10.0, 10.0, 0.5)
            eval_notes = st.text_input("ملاحظات")
            
            btn_save_eval = st.form_submit_button("💾 حفظ التقييم وترحيله سحابياً")
            
            if btn_save_eval:
                if selected_member:
                    m_row = st.session_state.members[
                        (st.session_state.members.get("اسم الكشاف", st.session_state.members.get("الاسم")) == selected_member)
                    ].iloc[0]
                    c_code = m_row.get("كود العضو", "")
                    
                    row_data = [str(eval_date), c_code, selected_member, eval_type, eval_score, eval_notes]
                    
                    if append_to_google_sheet("التقييمات", row_data):
                        new_score_df = pd.DataFrame([{
                            "تاريخ التقييم": str(eval_date), "كود العضو": c_code, "اسم الكشاف": selected_member,
                            "نوع التقييم": eval_type, "الدرجة (من 10)": eval_score, "ملاحظات": eval_notes
                        }])
                        st.session_state.scores = pd.concat([st.session_state.scores, new_score_df], ignore_index=True)
                        st.session_state.eval_scanned_code = ""
                        st.session_state.eval_reset_counter += 1
                        st.success("✅ تم حفظ التقييم ورَفعه للسحاب بنجاح!")
                        st.rerun()
                else:
                    st.error("يرجى اختيار عضو أوالتأكد من وجود أعضاء بالقائمة.")


# --- Tab: لوحة الصدارة (المعدل بالكامل لتفادي الخطأ) ---
if "leaderboard" in tab_dict:
    with tab_dict["leaderboard"]:
        st.subheader("🏆 لوحة صدارة وترتيب الأعضاء")
        
        if not st.session_state.members.empty:
            df_board = st.session_state.members.copy()
            
            # معالجة درجات الحضور بشكل آمن
            att_df = st.session_state.attendance.copy()
            if not att_df.empty and "كود العضو" in att_df.columns and "درجة الحضور" in att_df.columns:
                att_df["درجة الحضور"] = pd.to_numeric(att_df["درجة الحضور"], errors="coerce").fillna(0)
                att_sum = att_df.groupby("كود العضو")["درجة الحضور"].sum().reset_index()
                att_sum.rename(columns={"درجة الحضور": "مجموع الحضور"}, inplace=True)
            else:
                att_sum = pd.DataFrame(columns=["كود العضو", "مجموع الحضور"])
                
            # معالجة درجات التقييمات بشكل آمن
            scores_df = st.session_state.scores.copy()
            if not scores_df.empty and "كود العضو" in scores_df.columns and "الدرجة (من 10)" in scores_df.columns:
                scores_df["الدرجة (من 10)"] = pd.to_numeric(scores_df["الدرجة (من 10)"], errors="coerce").fillna(0)
                score_sum = scores_df.groupby("كود العضو")["الدرجة (من 10)"].sum().reset_index()
                score_sum.rename(columns={"الدرجة (من 10)": "مجموع التقييمات"}, inplace=True)
            else:
                score_sum = pd.DataFrame(columns=["كود العضو", "مجموع التقييمات"])
                
            # دمج الجداول مع جدول الأعضاء الأساسي
            df_board = pd.merge(df_board, att_sum, on="كود العضو", how="left").fillna(0)
            df_board = pd.merge(df_board, score_sum, on="كود العضو", how="left").fillna(0)
            
            df_board["مجموع الحضور"] = pd.to_numeric(df_board["مجموع الحضور"], errors="coerce").fillna(0)
            df_board["مجموع التقييمات"] = pd.to_numeric(df_board["مجموع التقييمات"], errors="coerce").fillna(0)
            
            df_board["المجموع الكلي"] = df_board["مجموع الحضور"] + df_board["مجموع التقييمات"]
            df_board = df_board.sort_values(by="المجموع الكلي", ascending=False).reset_index(drop=True)
            df_board.index += 1
            
            # استعراض الحقول المتاحة فقط لمنع أي KeyError
            cols_to_show = [c for c in ["كود العضو", "اسم الكشاف", "الفرقة", "مجموع الحضور", "مجموع التقييمات", "المجموع الكلي"] if c in df_board.columns]
            st.dataframe(df_board[cols_to_show], use_container_width=True)
            
            if st.session_state.user_role == "آدمن":
                if st.button("☁️ تحديث ورقة ترتيب الأعضاء سحابياً"):
                    if update_leaderboard_in_gsheet(df_board[cols_to_show]):
                        st.success("تم تحديث شيت لوحة الصدارة بنجاح!")
        else:
            st.info("لا يوجد أعضاء لعرض لوحة الصدارة.")


# --- Tab: الأعضاء ---
if "directory" in tab_dict:
    with tab_dict["directory"]:
        st.subheader("👥 دليل وقائمة الأعضاء")
        
        if not st.session_state.members.empty:
            st.dataframe(st.session_state.members, use_container_width=True)
        else:
            st.info("القائمة فارغة حالياً.")
            
        if st.session_state.user_role == "آدمن":
            st.divider()
            st.subheader("➕ إضافة عضو جديد")
            with st.form(f"add_member_form_{st.session_state.form_reset_counter}"):
                new_code = st.number_input("كود العضو", min_value=1, step=1)
                new_name = st.text_input("اسم الكشاف")
                new_squad = st.text_input("الفرقة")
                new_phone = st.text_input("رقم التليفون")
                new_date = st.date_input("تاريخ الانضمام", datetime.date.today())
                
                btn_add_m = st.form_submit_button("إضافة العضو")
                if btn_add_m:
                    if new_name.strip():
                        m_row = [new_code, new_name, new_squad, new_phone, str(new_date)]
                        if append_to_google_sheet("الأعضاء", m_row):
                            new_m_df = pd.DataFrame([{
                                "كود العضو": new_code, "اسم الكشاف": new_name,
                                "الفرقة": new_squad, "رقم التليفون": new_phone, "تاريخ الانضمام": str(new_date)
                            }])
                            st.session_state.members = pd.concat([st.session_state.members, new_m_df], ignore_index=True)
                            st.session_state.form_reset_counter += 1
                            st.success("✅ تم حفظ وإضافة العضو بنجاح سحابياً!")
                            st.rerun()
                    else:
                        st.error("يرجى كتابة اسم العضو.")


# --- Tab: الشيت السحابي ---
if "sheet_link" in tab_dict:
    with tab_dict["sheet_link"]:
        st.subheader("☁️ Google Sheets مباشر")
        st.markdown(f"يمكنك الانتقال المباشر وتعديل البيانات في Google Sheets من الرابط التالي:\n\n 🔗 [{SHEET_FULL_URL}]({SHEET_FULL_URL})")


# --- Tab: إدارة الحسابات ---
if "accounts" in tab_dict:
    with tab_dict["accounts"]:
        st.subheader("⚙️ إدارة حسابات المستخدمين والصلاحيات")
        
        users_df = load_data_from_gsheet("المستخدمين")
        if not users_df.empty:
            st.dataframe(users_df, use_container_width=True)
            
        st.divider()
        st.subheader("➕ إضافة مستخدم جديد وتحديد قوائمه")
        
        with st.form("add_user_form"):
            new_u_name = st.text_input("اسم المستخدم الجديد")
            new_u_pass = st.text_input("كلمة السر", type="password")
            new_u_role = st.selectbox("الصلاحية العامة", ["مستخدم", "آدمن"])
            
            st.write("📌 حدد القوائم المتاحة لهذا الحساب:")
            chk_att = st.checkbox("تسجيل الحضور", value=True)
            chk_eval = st.checkbox("التقييمات", value=True)
            chk_lead = st.checkbox("لوحة الصدارة", value=True)
            chk_dir = st.checkbox("الاعضاء", value=True)
            chk_sht = st.checkbox("الشيت السحابي", value=False)
            
            btn_create_user = st.form_submit_button("إنشاء الحساب ورَفعه سحابياً")
            
            if btn_create_user:
                if new_u_name.strip() and new_u_pass.strip():
                    perms_list = []
                    if chk_att: perms_list.append("تسجيل الحضور")
                    if chk_eval: perms_list.append("التقييمات")
                    if chk_lead: perms_list.append("لوحة الصدارة")
                    if chk_dir: perms_list.append("الاعضاء")
                    if chk_sht: perms_list.append("الشيت السحابي")
                    
                    perms_str = " - ".join(perms_list)
                    user_row = [new_u_name, new_u_pass, new_u_role, perms_str]
                    
                    if append_to_google_sheet("المستخدمين", user_row):
                        st.success(f"🎉 تم إنشاء حساب ({new_u_name}) بنجاح!")
                        time.sleep(1.5)
                        st.rerun()
                else:
                    st.error("يرجى كتابة اسم المستخدم وكلمة السر.")
