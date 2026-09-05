import datetime
import json
import os
import time
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
from PIL import Image
import streamlit as st

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="كشافة أم النور",
    page_icon="⚜️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

# --- 🔥 تهيئة Firebase للحالات الحية واللحظية ---
FIREBASE_CREDS = {
    "type": "service_account",
    "project_id": "scout-app-d5614",
    "private_key_id": "6d124414e35bdcf820dd3315a85cb549f13df03e",
    "private_key": (
        "-----BEGIN PRIVATE"
        " KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCYm6jNDnHySab6\nKKyOVo2LZhCmOeegCWsnaMbW/3vYK9h1tEBMO97Du6rDlG0JryUH+Wg3vUfQBif6\n+n89U+ZUjI+xvFmQv0sZ8KV54CQK9wG82C687z4yDA2XqU4YCFwD8mnrDmB7Yzlz\nyy++XWT6LqCkCRGO7xA0bxGNbSJSlZuJsW4apOxWDurxVzJdDij6s0eSEyzMSWNQ\nIWb44xjzbF1TIf+jdFb98adcCyV1BQf8NHt13vHlWdPVuzp3l3HXqeiHUepgIuo0\nti7WAW/bQzkvUMa4shpSE0ejxptQ0xQyMsqWbH0Vdulss+NgFPQD5iORVOVZJrlo\nqb8wuI1DAgMBAAECggEAEw0fqhW7EOGz+DfartxMSFJCEtZYvahfWaihZha36bkz\niSIrArlYqnvDqi3d3N8iEthGc+rry6LxG8po1wmhz/1KNQiL79+Jqx/ZMJlUNpA2\nhdJBJ3IAhDPwAHZw2tw0TIPXSDJfxheRhQyhFbVIFVl70W6WZA8hKUKSYOL2bXOx\nffOi9HbcmeRUf1RyGnZSCi/LfwobWbiHoWtBtlrjp49VHAbWO3B4QdrpaMOLH/ck\nhTuj8VN+bBfFt34MUfGol4cC/SEWEyytbU3OVwNjtmAw2O7FO1AUHy9BoIpThfJk\naYrl/JWeDL6HLb9d1Hn43eglp1RCpL4RsdXVoN1QaQKBgQDJ+hlgrULlR0uWfeVx\nlJ26xiUAfMdiRGiD6WqoXfH/6QELxNqWJ+hMdbvf1EJnhSn9Ytq/ruVTdNU5p4KQ\n1ALmMp0HHge52V0/iM2qMHZ3/VZt2b9jwVV9BaQK0KqxLcO2fJluf6HtjhwFTA+b\nxUiEcVpD4lyqPog+QJr4/jemmQKBgQDBbSO4AIvIPB7DVoy6KwFhwGl9jH4T6VXO\n9bqSz62W0BhI9JVpAS5GMS/fejys3i8aS37mkUiCVpqK5xc0KRiGqe2nCQH/NICn\nNuxEugPZuenAjQqlcIHiDONcbxt5e+kyT+F/ho5mtxHszUiQ5BoSTOjpunSwKQGA\nJnYEXU9oOwKBgFwCadMnusS18NIysfZG7H+sSijpru6uGSqWh7cBbP/Whlp1J9ql\nfWZvb9GsYT/FYvaCNQKDSwb0vznPfGQ7oMJ7Jhua64wXYCpUSNSR1TYeG2RZgJ2R\n8j7M9gjTPB8QqQqVwlObIwoT5eHn32hnu/xRovwvv2TyraAmUDLDpFhpAoGAdwuD\n00hKv5b43AJVpHK5a/8vLb0dD4YpcLHd/WNiFBLJD4Wwuyql3z+Alks2MrKgTM+w\nL5m1BbrlbJ3jsw+j76WABbDOkNIwaDmuWnId0o/QpNhpd/7xgT2rZQVg5Hj1wihV\nwdX/qIn9tz907O/md+Lr6oX+MTlbmhKRygffymcCgYAkq/1HmSXOj3RCCoY15rt7\na6DnEp3oC1gVBQ9o1A6sjqs/60R6eHqyX347+lFxeLVUHvMucAvCNhs+85VrQtQV\ncG65TPRojplHvt09jAitJF2ZEqT1Vg692kzdIiBl2I0+5WBMETZki7xU+5gRh+nT\nB3RFZh7bqFkM82JJfMF6Lg==\n-----END"
        " PRIVATE KEY-----\n"
    ),
    "client_email": (
        "firebase-adminsdk-fbsvc@scout-app-d5614.iam.gserviceaccount.com"
    ),
    "client_id": "112235328729842790577",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": (
        "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40scout-app-d5614.iam.gserviceaccount.com"
    ),
    "universe_domain": "googleapis.com",
}

if not firebase_admin._apps:
  cred = credentials.Certificate(FIREBASE_CREDS)
  firebase_admin.initialize_app(
      cred,
      {
          "databaseURL": (
              "https://scout-app-d5614-default-rtdb.firebaseio.com/"
          )
      },
  )


# --- دوال التعامل مع Firebase ---
def get_live_sessions_firebase():
  try:
    ref = db.reference("active_sessions")
    data = ref.get()
    return data if data else {}
  except Exception:
    return {}


def open_session_firebase(team_name, username, timestamp_now, date_str):
  key_team = "team_1" if team_name == "الفريق الأول" else "team_2"
  ref = db.reference(f"active_sessions/{key_team}")
  ref.set({
      "team": team_name,
      "user": username,
      "status": "مفتوحة",
      "start_time": date_str,
      "start_ts": timestamp_now,
  })


def close_session_firebase(team_name):
  key_team = "team_1" if team_name == "الفريق الأول" else "team_2"
  ref = db.reference(f"active_sessions/{key_team}")
  ref.delete()


def save_draft_scan_firebase(team_name, code, name, time_str, score, username):
  key_team = "team_1" if team_name == "الفريق الأول" else "team_2"
  ref = db.reference(f"drafts/{key_team}/{code}")
  ref.set({
      "code": code,
      "name": name,
      "team": team_name,
      "time": time_str,
      "score": score,
      "user": username,
  })


def get_draft_scans_firebase(team_name):
  key_team = "team_1" if team_name == "الفريق الأول" else "team_2"
  try:
    ref = db.reference(f"drafts/{key_team}")
    data = ref.get()
    return data if data else {}
  except Exception:
    return {}


def clear_draft_scans_firebase(team_name):
  key_team = "team_1" if team_name == "الفريق الأول" else "team_2"
  ref = db.reference(f"drafts/{key_team}")
  ref.delete()


# --- مكتبات الباركود ---
try:
  import zxingcpp

  HAS_ZXING = True
except ImportError:
  HAS_ZXING = False

try:
  from pyzbar.pyzbar import decode

  HAS_PYZBAR = True
except Exception:
  HAS_PYZBAR = False

# --- Google Sheets ---
try:
  from google.oauth2.service_account import Credentials
  import gspread

  HAS_GSPREAD = True
except ImportError:
  HAS_GSPREAD = False

SPREADSHEET_ID = "1B4Ho5U0x0TDf36bu7KqxXnMZCnvAiVxzfLthX_ga94c"
SHEET_FULL_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"


@st.cache_resource
def get_gsheet_client():
  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
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


@st.cache_data(ttl=10, show_spinner=False)
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
  except Exception:
    pass
  return pd.DataFrame()


def append_to_google_sheet(sheet_name, row_data):
  try:
    client = get_gsheet_client()
    if client:
      sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
      sheet.append_row(row_data)
      st.cache_data.clear()
      return True
  except Exception as e:
    st.error(f"⚠️ خطأ في الشيت ({sheet_name}): {type(e).__name__} - {str(e)}")
  return False


def append_rows_to_google_sheet(sheet_name, rows_data):
  """إضافة مجموعة صفوف دفعة واحدة لضمان عدم تجاوز طلبات Google API."""
  try:
    client = get_gsheet_client()
    if client:
      sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
      sheet.append_rows(rows_data)
      st.cache_data.clear()
      return True
  except Exception as e:
    st.error(
        f"⚠️ خطأ في الرفع الجماعي ({sheet_name}): {type(e).__name__} -"
        f" {str(e)}"
    )
  return False


def verify_current_password(username, current_password):
  try:
    users_df = load_data_from_gsheet("المستخدمين")
    if not users_df.empty:
      match = users_df[
          (
              users_df["اسم المستخدم"].astype(str).str.strip()
              == str(username).strip()
          )
          & (
              users_df["كلمة السر"].astype(str).str.strip()
              == str(current_password).strip()
          )
      ]
      return not match.empty
  except Exception:
    pass
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
            sheet.update_cell(idx + 2, 2, str(new_password).strip())
            st.cache_data.clear()
            return True
  except Exception as e:
    st.error(f"خطأ في تحديث كلمة السر: {e}")
  return False


def update_leaderboard_in_gsheet(df_leaderboard):
  try:
    client = get_gsheet_client()
    if client:
      sh = client.open_by_key(SPREADSHEET_ID)
      try:
        sheet = sh.worksheet("ترتيب الأعضاء")
      except Exception:
        sheet = sh.add_worksheet(
            title="ترتيب الأعضاء", rows="100", cols="10"
        )
      sheet.clear()
      headers = df_leaderboard.columns.tolist()
      data = df_leaderboard.astype(str).values.tolist()
      sheet.update([headers] + data)
      st.cache_data.clear()
      return True
  except Exception as e:
    st.error(f"خطأ في ترتيب الأعضاء: {e}")
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
  except Exception:
    pass
  return None


def check_login(username, password):
  try:
    users_df = load_data_from_gsheet("المستخدمين")
    if not users_df.empty:
      user_match = users_df[
          (
              users_df["اسم المستخدم"].astype(str).str.strip()
              == str(username).strip()
          )
          & (
              users_df["كلمة السر"].astype(str).str.strip()
              == str(password).strip()
          )
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
              "can_sheet": True,
          }
        else:
          permissions = {
              "can_attendance": "تسجيل الحضور" in raw_perms,
              "can_evaluations": "التقييمات" in raw_perms,
              "can_leaderboard": "لوحة الصدارة" in raw_perms,
              "can_directory": "الاعضاء" in raw_perms,
              "can_sheet": "الشيت السحابي" in raw_perms,
          }
        return True, role, permissions
  except Exception:
    pass
  return False, None, {}


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; }
    #MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }
    .stButton>button { width: 100%; background-color: #1565C0; color: white; font-weight: bold; border-radius: 10px; padding: 12px; font-size: 16px; }
    .header-box { background-color: #0D47A1; color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="header-box"><h2> كشافة أم النور ⚜️ </h2></div>',
    unsafe_allow_html=True,
)

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
      "can_sheet": False,
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

col_user_info, col_pwd, col_logout = st.columns([2.5, 1.2, 1])
with col_user_info:
  st.info(
      f"👤 **المستخدم:** {st.session_state.current_username} | **الصلاحية:**"
      f" {st.session_state.user_role}"
  )

with col_pwd:

  @st.dialog("🔑 تغيير كلمة السر")
  def change_password_dialog():
    st.write(
        f"تغيير كلمة السر لحساب: **{st.session_state.current_username}**"
    )
    with st.form("change_pass_form"):
      old_p = st.text_input("كلمة السر الحالية", type="password")
      new_p1 = st.text_input("كلمة السر الجديدة", type="password")
      new_p2 = st.text_input("تأكيد كلمة السر الجديدة", type="password")
      btn_save = st.form_submit_button("تحديث كلمة السر")
      if btn_save:
        if not old_p.strip() or not new_p1.strip():
          st.error("❌ يرجى إدخال البيانات كاملة.")
        elif new_p1 != new_p2:
          st.error("❌ كلمتا السر غير متطابقتين!")
        else:
          if verify_current_password(st.session_state.current_username, old_p):
            if update_user_password_in_gsheet(
                st.session_state.current_username, new_p1
            ):
              st.success("🎉 تم التحديث بنجاح!")
              time.sleep(1)
              st.rerun()
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
if "manual_reset_counter" not in st.session_state:
  st.session_state.manual_reset_counter = 0

# --- تهيئة البيانات ---
if "members" not in st.session_state or st.session_state.members.empty:
  fetched_members = load_data_from_gsheet("الأعضاء")
  st.session_state.members = (
      fetched_members
      if not fetched_members.empty
      else pd.DataFrame(columns=[
          "كود العضو",
          "اسم الكشاف",
          "الفرقة",
          "الفريق",
          "رقم التليفون",
          "تاريخ الانضمام",
      ])
  )

if (
    not st.session_state.members.empty
    and "الفريق" not in st.session_state.members.columns
):
  st.session_state.members["الفريق"] = "الفريق الأول"

if "attendance" not in st.session_state:
  st.session_state.attendance = load_data_from_gsheet("الحضور")
  if st.session_state.attendance.empty:
    st.session_state.attendance = pd.DataFrame(columns=[
        "التاريخ",
        "كود العضو",
        "اسم الكشاف",
        "الفريق",
        "حالة الحضور",
        "وقت التسجيل",
        "درجة الحضور",
    ])

if "scores" not in st.session_state:
  st.session_state.scores = load_data_from_gsheet("التقييمات")
  if st.session_state.scores.empty:
    st.session_state.scores = pd.DataFrame(columns=[
        "تاريخ التقييم",
        "كود العضو",
        "اسم الكشاف",
        "الفريق",
        "نوع التقييم",
        "الدرجة (من 10)",
        "ملاحظات",
    ])

if "eval_scanned_code" not in st.session_state:
  st.session_state.eval_scanned_code = ""
if "show_eval_camera" not in st.session_state:
  st.session_state.show_eval_camera = False

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
if (
    st.session_state.permissions.get("can_sheet", False)
    or st.session_state.user_role == "آدمن"
):
  available_tabs.append("☁️ الشيت السحابي")
  tab_keys.append("sheet_link")
if st.session_state.user_role == "آدمن":
  available_tabs.append("⚙️ إدارة الحسابات")
  tab_keys.append("accounts")

if not available_tabs:
  st.warning("⚠️ لا توجد صلاحيات لعرض أي قوائم.")
  st.stop()

tabs = st.tabs(available_tabs)
tab_dict = {key: tabs[i] for i, key in enumerate(tab_keys)}

# --- Tab: تسجيل الحضور ---
if "attendance" in tab_dict:
  with tab_dict["attendance"]:
    st.subheader("تسجيل الحضور الفوري")

    col_btn_refresh, _ = st.columns([1, 1])
    with col_btn_refresh:
      if st.button("🔄 مزامنة الجلسات الحية فوراً"):
        st.rerun()

    live_sessions = get_live_sessions_firebase()

    if live_sessions:
      for k_item, sess_v in live_sessions.items():
        t_title = sess_v.get("team", "الفريق")
        u_owner = sess_v.get("user", "قائد")
        st_time = sess_v.get("start_time", "")
        st.success(
            f"🟢 **جلسة نشطة حالياً لـ ({t_title})** | 👤 **القائد:** {u_owner} |"
            f" 📅 **بدأت:** {st_time}"
        )
    else:
      st.info("ℹ️ لا توجد أي جلسات مفتوحة حالياً في أي فريق.")

    st.divider()

    selected_team = st.radio(
        "اختر الفريق للعمل عليه:",
        ["الفريق الأول", "الفريق الثاني"],
        horizontal=True,
    )

    selected_key = "team_1" if selected_team == "الفريق الأول" else "team_2"
    active_session = live_sessions.get(selected_key, None)

    # جلب المسودة الحية من Firebase وتحويل المفاتيح إلى نصوص نظيفة
    scanned_members = {}
    if active_session:
      draft_scans = get_draft_scans_firebase(selected_team)
      for c_k, item_v in draft_scans.items():
        clean_k = str(c_k).strip()
        scanned_members[clean_k] = (
            item_v.get("time", ""),
            float(item_v.get("score", 10.0)),
        )

    col_start, col_stop = st.columns(2)

    with col_start:
      if st.button("🚀 بدء الاجتماع / الجلسة"):
        if active_session:
          m_user = active_session.get("user", "قائد آخر")
          m_time = active_session.get("start_time", "")
          st.error(
              f"❌ عذراً! توجد جلسة مفتوحة بالفعل لـ ({selected_team}) قام"
              f" بفتحها القائد ({m_user}) في ({m_time})."
          )
        else:
          now_ts = time.time()
          # استبدال سطر today_date القديم بهذا السطر:
now_egypt = datetime.datetime.now() + datetime.timedelta(hours=3)
today_date = now_egypt.strftime("%Y-%m-%d %H:%M")

          open_session_firebase(
              selected_team, st.session_state.current_username, now_ts, today_date
          )
          st.success(
              f"🎉 تم بدء الجلسة لـ ({selected_team}) بنجاح عبر Firebase!"
          )
          time.sleep(0.3)
          st.rerun()

    with col_stop:
      if st.button("🔴 إغلاق الجلسة وترحيل البيانات للسحاب فورا"):
        if active_session:
          try:
            # إضافة 3 ساعات للتوقيت المحلي
now_egypt = datetime.datetime.now() + datetime.timedelta(hours=3)
today = now_egypt.strftime("%Y-%m-%d")



            # 1. جلب أعضاء الفريق المحدد فقط
            team_members = (
                st.session_state.members[
                    st.session_state.members["الفريق"] == selected_team
                ]
                if "الفريق" in st.session_state.members.columns
                else st.session_state.members
            )

            rows_to_upload = []
            new_att_records = []

            # 2. المرور على جميع أعضاء الفريق بدون استثناء
            for _, row in team_members.iterrows():
              raw_code = row.get("كود العضو", "")
              clean_code_str = str(raw_code).strip()
              member_name = row.get(
                  "اسم الكشاف", row.get("الاسم", "غير معروف")
              )

              # المطابقة
              if clean_code_str in scanned_members:
                t_str, sc = scanned_members[clean_code_str]
                st_name = "حاضر"
              else:
                t_str = "تلقائي"
                sc = 0.0
                st_name = "غائب"

              # تجهيز الصف للرفع الجماعي
              row_data = [
                  today,
                  raw_code,
                  member_name,
                  selected_team,
                  st_name,
                  t_str,
                  sc,
              ]
              rows_to_upload.append(row_data)

              new_att_records.append({
                  "التاريخ": today,
                  "كود العضو": raw_code,
                  "اسم الكشاف": member_name,
                  "الفريق": selected_team,
                  "حالة الحضور": st_name,
                  "وقت التسجيل": t_str,
                  "درجة الحضور": sc,
              })

            # 3. إرسال الصفوف دفعة واحدة للسحاب
            if rows_to_upload:
              if append_rows_to_google_sheet("الحضور", rows_to_upload):
                st.session_state.attendance = pd.concat(
                    [
                        st.session_state.attendance,
                        pd.DataFrame(new_att_records),
                    ],
                    ignore_index=True,
                )

                # إغلاق الجلسة ومسح المسودة من Firebase
                close_session_firebase(selected_team)
                clear_draft_scans_firebase(selected_team)

                st.success(
                    f"🎉 تم تسجيل حضور وغياب ({len(rows_to_upload)}) عضو لـ"
                    f" ({selected_team}) بنجاح! ☁️"
                )
                time.sleep(1)
                st.rerun()
              else:
                st.error("❌ فشلت عملية الرفع الجماعي لـ Google Sheets.")
          except Exception as ex:
            st.error(f"❌ حدث خطأ غير متوقع أثناء إغلاق الجلسة: {ex}")
            st.exception(ex)
        else:
          st.warning("لا توجد جلسة نشطة لهذا الفريق حالياً.")

    if active_session:
      start_ts = float(active_session.get("start_ts", time.time()))
      elapsed_min = int((time.time() - start_ts) // 60)
      curr_score = max(0.0, round(10.0 - (int(elapsed_min // 5) * 1.0), 1))
      st.info(
          f"⏱️ زمن الاجتماع: {elapsed_min} دقيقة | درجة الحضور الآن:"
          f" **{curr_score} / 10**"
      )
    else:
      curr_score = 10.0

    st.divider()

    if active_session:
      st.subheader(f"📷 التقاط الكارت والتسجيل التلقائي ({selected_team})")
      img_file = st.camera_input("اضغط التقاط الصورة لقرائتها وتسجيلها فوراً")

      if img_file is not None:
        extracted = extract_qr_code(img_file)
        if extracted:
          clean_extracted = str(extracted).strip()
          m = (
              st.session_state.members[
                  (
                      st.session_state.members["كود العضو"]
                      .astype(str)
                      .str.strip()
                      == clean_extracted
                  )
                  & (st.session_state.members["الفريق"] == selected_team)
              ]
              if "الفريق" in st.session_state.members.columns
              else st.session_state.members[
                  st.session_state.members["كود العضو"].astype(str).str.strip()
                  == clean_extracted
              ]
          )

          if not m.empty:
            row_data = m.iloc[0]
            m_name = row_data.get("اسم الكشاف", row_data.get("الاسم", "كشاف"))

            if clean_extracted not in scanned_members:
              t_now = datetime.datetime.now().strftime("%H:%M:%S")
              save_draft_scan_firebase(
                  selected_team,
                  clean_extracted,
                  m_name,
                  t_now,
                  curr_score,
                  st.session_state.current_username,
              )
              st.success(
                  f"🎉 تم تسجيل حضور: {m_name} ({selected_team}) - كود:"
                  f" {clean_extracted}"
              )
              st.balloons()
            else:
              st.info(
                  f"ℹ️ الكشاف {m_name} مسجل بالفعل في هذه الجلسة."
              )
          else:
            st.error(
                f"❌ الكود ({clean_extracted}) غير مسجل ضمن أعضاء"
                f" {selected_team}!"
            )
        else:
          st.error("❌ لم يتم التعرف على الرمز.")
    else:
      st.info(
          "💡 لا توجد جلسة مفتوحة لهذا الفريق. قم باختيار الفريق ثم اضغط **🚀"
          " بدء الاجتماع / الجلسة**."
      )

    st.divider()

    if active_session:
      with st.form(
          f"manual_attendance_form_{st.session_state.manual_reset_counter}"
      ):
        manual_code_str = st.text_input(
            "أو أدخل الكود يدوياً واضغط تسجيل:", value=""
        )
        submit_manual = st.form_submit_button("✅ تسجيل يدوي سريع")

        if submit_manual:
          if manual_code_str.strip():
            clean_manual = str(manual_code_str.strip()).strip()
            m = (
                st.session_state.members[
                    (
                        st.session_state.members["كود العضو"]
                        .astype(str)
                        .str.strip()
                        == clean_manual
                    )
                    & (st.session_state.members["الفريق"] == selected_team)
                ]
                if "الفريق" in st.session_state.members.columns
                else st.session_state.members[
                    st.session_state.members["كود العضو"].astype(str).str.strip()
                    == clean_manual
                ]
            )

            if not m.empty:
              row_data = m.iloc[0]
              m_name = row_data.get("اسم الكشاف", row_data.get("الاسم", "كشاف"))
              if clean_manual not in scanned_members:
                # استبدال سطر t_now القديم بهذا السطر:
t_now = (datetime.datetime.now() + datetime.timedelta(hours=3)).strftime(
    "%H:%M:%S"
)

                save_draft_scan_firebase(
                    selected_team,
                    clean_manual,
                    m_name,
                    t_now,
                    curr_score,
                    st.session_state.current_username,
                )
                st.session_state.manual_reset_counter += 1
                st.success(
                    f"🎉 تم تسجيل: {m_name} ({selected_team}) | الدرجة:"
                    f" {curr_score}/10"
                )
                time.sleep(0.8)
                st.rerun()
              else:
                st.info(f"ℹ️ الكشاف {m_name} مسجل بالفعل.")
            else:
              st.error(f"الكود غير مسجل في {selected_team}!")
          else:
            st.warning("يرجى إدخال كود الكشاف أولاً.")

# --- Tab: التقييمات ---
if "evaluations" in tab_dict:
  with tab_dict["evaluations"]:
    st.subheader("📝 إضافة تقييم أو نشاط كشفي")
    col_cam_btn, _ = st.columns([1, 1])
    with col_cam_btn:
      if st.button(
          "📷 فتح/إغلاق الكاميرا لمسح الكود", key="toggle_eval_cam_btn"
      ):
        st.session_state.show_eval_camera = (
            not st.session_state.show_eval_camera
        )
        st.rerun()

    if st.session_state.show_eval_camera:
      eval_img = st.camera_input(
          "التقط صورة كارت الكشاف للتقييم", key="eval_cam"
      )
      if eval_img is not None:
        extracted_eval = extract_qr_code(eval_img)
        if extracted_eval:
          st.session_state.eval_scanned_code = str(extracted_eval).strip()
          st.session_state.show_eval_camera = False
          st.success(f"تم التقاط الكود: {extracted_eval}")
          st.rerun()
        else:
          st.error("لم يتم التعرف على الرمز.")

    with st.form(f"score_form_{st.session_state.eval_reset_counter}"):
      eval_team = st.selectbox(
          "الفريق", ["الفريق الأول", "الفريق الثاني"], key="eval_team_select"
      )
      s_code_input = st.text_input(
          "كود الكشاف",
          value=st.session_state.eval_scanned_code,
          placeholder="أدخل الكود أو امسحه بالكاميرا",
      )
      s_type = st.selectbox("نوع التقييم", [
          "الزي الكشفي",
          "السلوك والانضباط",
          "الأنشطة والمهارات",
          "الخدمة",
          "الاعتراف",
          "التناول",
      ])
      s_val = st.number_input(
          "الدرجة (من 10)",
          min_value=0.0,
          max_value=10.0,
          step=0.5,
          value=10.0,
      )
      s_notes = st.text_input("ملاحظات / اسم النشاط", value="")

      submit_eval = st.form_submit_button("حفظ التقييم والمزامنة السحابية")

      if submit_eval:
        if s_code_input.strip():
          clean_s_code = str(s_code_input.strip()).strip()
          matched = st.session_state.members[
              st.session_state.members["كود العضو"].astype(str).str.strip()
              == clean_s_code
          ]
          if not matched.empty:
            row_found = matched.iloc[0]
            found_member_name = row_found.get(
                "اسم الكشاف", row_found.get("الاسم", "غير معروف")
            )
            # استبدال t_date القديم بهذا السطر:
            t_date = (datetime.datetime.now() + datetime.timedelta(hours=3)).strftime(
    "%Y-%m-%d"
)


            if append_to_google_sheet(
                "التقييمات",
                [
                    t_date,
                    clean_s_code,
                    found_member_name,
                    eval_team,
                    s_type,
                    s_val,
                    s_notes,
                ],
            ):
              st.session_state.eval_scanned_code = ""
              st.session_state.eval_reset_counter += 1
              st.success(
                  f"تم تسجيل تقييم ({s_type}) للكشاف {found_member_name} ({eval_team}) بنجاح!"
              )
              time.sleep(1)
              st.rerun()
            else:
              st.error("حدث خطأ أثناء الرفع السحابي.")
          else:
            st.error("❌ الكود المدخل غير موجود في الأعضاء.")
        else:
          st.warning("يرجى إدخال كود الكشاف أولاً.")

# --- Tab: لوحة الصدارة ---
if "leaderboard" in tab_dict:
  with tab_dict["leaderboard"]:
    st.subheader("🏆 ترتيب الكشافة حسَب إجمالي الدرجات")
    col_ref, col_sync = st.columns(2)
    leaderboard = pd.DataFrame()

    if not st.session_state.members.empty:
      members_df = st.session_state.members.copy()
      c_name = (
          "كود العضو"
          if "كود العضو" in members_df.columns
          else members_df.columns[0]
      )
      n_name = (
          "اسم الكشاف"
          if "اسم الكشاف" in members_df.columns
          else members_df.columns[1]
      )
      t_name = "الفريق" if "الفريق" in members_df.columns else "الفريق"

      if t_name not in members_df.columns:
        members_df[t_name] = "الفريق الأول"

      leaderboard = members_df[[c_name, n_name, t_name]].copy()
      leaderboard[c_name] = leaderboard[c_name].astype(str).str.strip()

      att_df = st.session_state.attendance.copy()
      if not att_df.empty and "كود العضو" in att_df.columns:
        att_df["كود العضو"] = att_df["كود العضو"].astype(str).str.strip()
        if "درجة الحضور" in att_df.columns:
          att_df["درجة الحضور"] = pd.to_numeric(
              att_df["درجة الحضور"], errors="coerce"
          ).fillna(0)
        att_sum = (
            att_df.groupby("كود العضو")["درجة الحضور"].sum().reset_index()
            if "درجة الحضور" in att_df.columns
            else pd.DataFrame(columns=[c_name, "نقاط الحضور"])
        )
        if "درجة الحضور" in att_df.columns:
          att_sum.columns = [c_name, "نقاط الحضور"]
      else:
        att_sum = pd.DataFrame(columns=[c_name, "نقاط الحضور"])

      sc_df = st.session_state.scores.copy()
      if not sc_df.empty and "كود العضو" in sc_df.columns:
        sc_df["كود العضو"] = sc_df["كود العضو"].astype(str).str.strip()
        sc_col = [
            c
            for c in sc_df.columns
            if "الدرجة" in c or "درجة" in c or "Score" in c
        ]
        sc_v = sc_col[0] if sc_col else sc_df.columns[-1]
        sc_df[sc_v] = pd.to_numeric(sc_df[sc_v], errors="coerce").fillna(0)
        sc_sum = sc_df.groupby("كود العضو")[sc_v].sum().reset_index()
        sc_sum.columns = [c_name, "نقاط التقييمات"]
      else:
        sc_sum = pd.DataFrame(columns=[c_name, "نقاط التقييمات"])

      leaderboard = leaderboard.merge(att_sum, on=c_name, how="left").fillna(0)
      leaderboard = leaderboard.merge(sc_sum, on=c_name, how="left").fillna(0)
      leaderboard["المجموع الكلي"] = (
          leaderboard["نقاط الحضور"] + leaderboard["نقاط التقييمات"]
      )
      leaderboard = leaderboard.sort_values(
          by="المجموع الكلي", ascending=False
      ).reset_index(drop=True)
      leaderboard.index = leaderboard.index + 1

    with col_ref:
      if st.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.session_state.attendance = load_data_from_gsheet("الحضور")
        st.session_state.scores = load_data_from_gsheet("التقييمات")
        st.session_state.members = load_data_from_gsheet("الأعضاء")
        st.rerun()

    with col_sync:
      if st.button("☁️ رفع ترتيب الأعضاء إلى Google Sheets"):
        if not leaderboard.empty:
          if update_leaderboard_in_gsheet(leaderboard):
            st.success("تم تحديث ورقة 'ترتيب الأعضاء' سحابياً بنجاح! 🎉")

    if not leaderboard.empty:
      sub_t1, sub_t2, sub_all = st.tabs(
          ["🥇 الفريق الأول", "🥇 الفريق الثاني", "📊 الترتيب العام"]
      )
      with sub_t1:
        st.dataframe(
            leaderboard[leaderboard[t_name] == "الفريق الأول"],
            use_container_width=True,
        )
      with sub_t2:
        st.dataframe(
            leaderboard[leaderboard[t_name] == "الفريق الثاني"],
            use_container_width=True,
        )
      with sub_all:
        st.dataframe(leaderboard, use_container_width=True)

# --- Tab: الأعضاء ---
if "directory" in tab_dict:
  with tab_dict["directory"]:
    st.subheader("👥 إضافة كشاف جديد")
    if "form_version" not in st.session_state:
      st.session_state.form_version = 0

    v = st.session_state.form_version
    m_name = st.text_input(
        "اسم الكشاف رباعي",
        placeholder="أدخل الاسم رباعياً",
        key=f"widget_m_name_{v}",
    )
    m_team = st.selectbox(
        "اختر الفريق",
        ["الفريق الأول", "الفريق الثاني"],
        key=f"widget_m_team_{v}",
    )
    m_phone = st.text_input(
        "رقم التليفون", placeholder="01xxxxxxxxx", key=f"widget_m_phone_{v}"
    )
    gender = st.radio(
        "النوع", ["ذكر", "أنثى"], horizontal=True, key=f"widget_gender_{v}"
    )
    birth_date = st.date_input(
        "تاريخ الميلاد",
        value=datetime.date(2000, 1, 1),
        key=f"widget_birth_date_{v}",
    )
    academic_stage = st.selectbox(
        "المرحلة الدراسية",
        [
            "أولى إعدادي",
            "تانية إعدادي",
            "تالتة إعدادي",
            "أولى ثانوي",
            "تانية ثانوي",
            "تالتة ثانوي",
            "جامعة",
            "أخرى",
        ],
        key=f"widget_academic_stage_{v}",
    )

    suggested_dept = "كشاف"
    if gender == "ذكر":
      if "إعدادي" in academic_stage:
        suggested_dept = "كشاف"
      elif "ثانوي" in academic_stage:
        suggested_dept = "متقدم"
      elif academic_stage in ["جامعة", "أخرى"]:
        suggested_dept = "جوال"
    else:
      if "إعدادي" in academic_stage or "ثانوي" in academic_stage:
        suggested_dept = "مرشدات"
      elif academic_stage in ["جامعة", "أخرى"]:
        suggested_dept = "جوالات"

    default_depts = ["كشاف", "متقدم", "جوال", "مرشدات", "جوالات", "قادة"]
    default_idx = (
        default_depts.index(suggested_dept)
        if suggested_dept in default_depts
        else 0
    )
    m_dept = st.selectbox(
        "الفرقة الكشفية",
        default_depts,
        index=default_idx,
        key=f"widget_m_dept_{v}_{gender}_{academic_stage}",
    )

    if st.button("إضافة لخدمة الكشافة"):
      if m_name.strip():
        cleaned_input_name = " ".join(m_name.strip().split())
        try:
          max_c = (
              pd.to_numeric(
                  st.session_state.members["كود العضو"], errors="coerce"
              ).max()
              if not st.session_state.members.empty
              else 21820260
          )
          if pd.isna(max_c):
            max_c = 21820260
        except Exception:
          max_c = 21820260

        new_c = int(max_c + 1)
        # استبدال t_date القديم بهذا السطر:
            t_date = (datetime.datetime.now() + datetime.timedelta(hours=3)).strftime(
    "%Y-%m-%d"
)


        if append_to_google_sheet("الأعضاء", [
            new_c,
            cleaned_input_name,
            m_team,
            m_phone,
            gender,
            str(birth_date),
            academic_stage,
            m_dept,
            t_date,
        ]):
          new_m = {
              "كود العضو": new_c,
              "اسم الكشاف": cleaned_input_name,
              "الفريق": m_team,
              "رقم التليفون": m_phone,
              "النوع": gender,
              "تاريخ الميلاد": birth_date,
              "المرحلة الدراسية": academic_stage,
              "الفرقة": m_dept,
              "تاريخ الانضمام": t_date,
          }
          st.session_state.members = pd.concat(
              [st.session_state.members, pd.DataFrame([new_m])],
              ignore_index=True,
          )
          st.session_state.form_version += 1
          st.success(
              f"🎉 تمت إضافة الكشاف ({cleaned_input_name}) لـ ({m_team}) بنجاح!"
          )
          time.sleep(1)
          st.rerun()

# --- Tab: الشيت السحابي ---
if "sheet_link" in tab_dict:
  with tab_dict["sheet_link"]:
    st.subheader("☁️ رابط Google Sheets المباشر")
    st.markdown(
        f"[اضغط هنا لفتح Google Sheets في نافذة جديدة]({SHEET_FULL_URL})"
    )
    st.markdown(
        f'<iframe src="{SHEET_FULL_URL}" width="100%" height="600px"></iframe>',
        unsafe_allow_html=True,
    )

# --- Tab: إدارة الحسابات ---
if "accounts" in tab_dict:
  with tab_dict["accounts"]:
    st.subheader("⚙️ إضافة حساب جديد وتحديد الصلاحيات")
    all_possible_tabs = [
        "تسجيل الحضور",
        "التقييمات",
        "لوحة الصدارة",
        "دليل الكشافة",
        "الشيت السحابي",
    ]
    new_u_role = st.selectbox(
        "نوع الحساب", ["كابتن", "عضو", "آدمن"], key="user_role_select"
    )

    if new_u_role == "آدمن":
      selected_tabs = all_possible_tabs
    elif new_u_role == "عضو":
      selected_tabs = ["لوحة الصدارة"]
    else:
      selected_tabs = st.multiselect(
          "حدد القوائم المتاحة لـ (كابتن):",
          options=all_possible_tabs,
          default=[
              "تسجيل الحضور",
              "التقييمات",
              "لوحة الصدارة",
              "دليل الكشافة",
          ],
          key="captain_perms",
      )

    with st.form("add_user_form", clear_on_submit=True):
      new_u_name = st.text_input("اسم المستخدم الجديد", key="input_u_name")
      new_u_pass = st.text_input(
          "كلمة السر الجديدة", type="password", key="input_u_pass"
      )
      submit_user = st.form_submit_button("إضافة الحساب وحفظه سحابياً")
      if submit_user:
        if new_u_name.strip() and new_u_pass.strip():
          perms_str = ", ".join(selected_tabs)
          new_row = [
              new_u_name.strip(),
              new_u_pass.strip(),
              new_u_role,
              perms_str,
          ]
          if append_to_google_sheet("المستخدمين", new_row):
            st.success(f"🎉 تم إنشاء حساب ({new_u_name}) بنجاح!")
            st.rerun()

    st.divider()
    users_list = load_data_from_gsheet("المستخدمين")
    if not users_list.empty:
      st.dataframe(users_list, use_container_width=True)
