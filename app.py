import datetime
import json
import os
import time
from zoneinfo import ZoneInfo
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
from PIL import Image
import streamlit as st

CAIRO_TZ = ZoneInfo("Africa/Cairo")

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
        " KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCYm6jNDnHySab6\nKKyOVo2LZhCmOeegCWsnaMbW/3vYK9h1tEBMO97Du6rDlG0JryUH+Wg3vUfQBif6\n+n89U+ZUjI+xvFmQv0sZ8KV54CQK9wG82C687z4yDA2XqU4YCFwD8mnrDmB7Yzlz\nyy++XWT6LqCkCRGO7xA0bxGNbSJSlZuJsW4apOxWDurxVzJdDij6s0eSEyzMSWNQ\nIWb44xjzbF1TIf+jdFb98adcCyV1BQf8NHt13vHlWdPVuzp3l3HXqeiHUepgIuo0\nti7WAW/bQzkvUMa4shpSE0ejxptQ0xQyMsqWbH0Vdulss+NgFPQD5iORVOVZJrlo\nqb8wuI1DAgMBAAECggEAEw0fqhW7EOGz+DfartxMSFJCEtZYvahfWaihZha36bkz\niSIrArlYqnvDqi3d3N8iEthGc+rry6LxG8po1wmhz/1KNQiL79+Jqx/ZMJlUNpA2\nhdJBJ3IAhDPwAHZw2tw0TIPXSDJfxheRhQyhFbVIFVl70W6WZA8hKUKSYOL2bXOx\nffOi9HbcmeRUf1RyGnZSCi/LfwobWbiHoWtBtlrjp49VHAbWO3B4QdrpaMOLH/ck\nhTuj8VN+bBfFt34MUfGol4cC/SEWEyytbU3OVwNjtmAw2O7FO1AUHy9BoIpThfJk\naYrl/JWeDL6HLb9d1Hn43eglp1RCpL4RsdXVoN1QaQKBgQDJ+hlgrULlR0uWfeVx\nlJ26xiUAfMdiRGiD6WqoXfH/6QELxNqWJ+hMdbvf1EJnhSn9Ytq/ruVTdNU5p4KQ\1ALmMp0HHge52V0/iM2qMHZ3/VZt2b9jwVV9BaQK0KqxLcO2fJluf6HtjhwFTA+b\nxUiEcVpD4lyqPog+QJr4/jemmQKBgQDBbSO4AIvIPB7DVoy6KwFhwGl9jH4T6VXO\9bqSz62W0BhI9JVpAS5GMS/fejys3i8aS37mkUiCVpqK5xc0KRiGqe2nCQH/NICn\nNuxEugPZuenAjQqlcIHiDONcbxt5e+kyT+F/ho5mtxHszUiQ5BoSTOjpunSwKQGA\nJnYEXU9oOwKBgFwCadMnusS18NIysfZG7H+sSijpru6uGSqWh7cBbP/Whlp1J9ql\nfWZvb9GsYT/FYvaCNQKDSwb0vznPfGQ7oMJ7Jhua64wXYCpUSNSR1TYeG2RZgJ2R\r\n8j7M9gjTPB8QqQqVwlObIwoT5eHn32hnu/xRovwvv2TyraAmUDLDpFhpAoGAdwuD\00hKv5b43AJVpHK5a/8vLb0dD4YpcLHd/WNiFBLJD4Wwuyql3z+Alks2MrKgTM+w\L5m1BbrlbJ3jsw+j76WABbDOkNIwaDmuWnId0o/QpNhpd/7xgT2rZQVg5Hj1wihV\nwdX/qIn9tz907O/md+Lr6oX+MTlbmhKRygffymcCgYAkq/1HmSXOj3RCCoY15rt7\na6DnEp3oC1gVBQ9o1A6sjqs/60R6eHqyX347+lFxeLVUHvMucAvCNhs+85VrQtQV\ncG65TPRojplHvt09jAitJF2ZEqT1Vg692kzdIiBl2I0+5WBMETZki7xU+5gRh+nT\B3RFZh7bqFkM82JJfMF6Lg==\n-----END"
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
          now_egypt = datetime.datetime.now(CAIRO_TZ)
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
            now_egypt = datetime.datetime.now(CAIRO_TZ)
            today = now_egypt.strftime("%Y-%m-%d")

            team_members = (
                st.session_state.members[
                    st.session_state.members["الفريق"] == selected_team
                ]
                if "الفريق" in st.session_state.members.columns
                else st.session_state.members
            )

            rows_to_upload = []
            new_att_records = []
            scanned_codes_set = set(scanned_members.keys())

            for c_code, (t_str, sc) in scanned_members.items():
              m_match = (
                  st.session_state.members[
                      st.session_state.members["كود العضو"]
                      .astype(str)
                      .str.strip()
                      == c_code
                  ]
                  if not st.session_state.members.empty
                  else pd.DataFrame()
              )

              if not m_match.empty:
                r_found = m_match.iloc[0]
                m_name = r_found.get(
                    "اسم الكشاف", r_found.get("الاسم", "غير معروف")
                )
                m_orig_team = r_found.get("الفريق", selected_team)
              else:
                m_name = "غير معروف"
                m_orig_team = selected_team

              row_data = [
                  today,
                  c_code,
                  m_name,
                  m_orig_team,
                  "حاضر",
                  t_str,
                  sc,
              ]
              rows_to_upload.append(row_data)

              new_att_records.append({
                  "التاريخ": today,
                  "كود العضو": c_code,
                  "اسم الكشاف": m_name,
                  "الفريق": m_orig_team,
                  "حالة الحضور": "حاضر",
                  "وقت التسجيل": t_str,
                  "درجة الحضور": sc,
              })

            for _, row in team_members.iterrows():
              raw_code = row.get("كود العضو", "")
              clean_code_str = str(raw_code).strip()
              member_name = row.get(
                  "اسم الكشاف", row.get("الاسم", "غير معروف")
              )

              if clean_code_str not in scanned_codes_set:
                row_data = [
                    today,
                    raw_code,
                    member_name,
                    selected_team,
                    "غائب",
                    "تلقائي",
                    0.0,
                ]
                rows_to_upload.append(row_data)

                new_att_records.append({
                    "التاريخ": today,
                    "كود العضو": raw_code,
                    "اسم الكشاف": member_name,
                    "الفريق": selected_team,
                    "حالة الحضور": "غائب",
                    "وقت التسجيل": "تلقائي",
                    "درجة الحضور": 0.0,
                })

            if rows_to_upload:
              if append_rows_to_google_sheet("الحضور", rows_to_upload):
                st.session_state.attendance = pd.concat(
                    [
                        st.session_state.attendance,
                        pd.DataFrame(new_att_records),
                    ],
                    ignore_index=True,
                )

                close_session_firebase(selected_team)
                clear_draft_scans_firebase(selected_team)

                st.success(
                    f"🎉 تم ترحيل سجلات الحضور والغياب لجلسة ({selected_team}) بنجاح! ☁️"
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
      st.subheader(f"📷 مسح مباشر بالـ QR للـ ({selected_team})")

      # معالجة الكود المباشر القادم من الباركود فوراً
      query_p = st.query_params
      if "auto_code" in query_p:
        scanned_code_val = query_p["auto_code"]
        st.query_params.clear()
        if scanned_code_val:
          clean_code = str(scanned_code_val).strip()
          m_match = (
              st.session_state.members[
                  st.session_state.members["كود العضو"]
                  .astype(str)
                  .str.strip()
                  == clean_code
              ]
              if not st.session_state.members.empty
              else pd.DataFrame()
          )

          if not m_match.empty:
            r_data = m_match.iloc[0]
            m_name = r_data.get("اسم الكشاف", r_data.get("الاسم", "كشاف"))
            m_orig_team = r_data.get("الفريق", "غير محدد")

            if clean_code not in scanned_members:
              t_now = datetime.datetime.now(CAIRO_TZ).strftime("%H:%M:%S")
              save_draft_scan_firebase(
                  selected_team,
                  clean_code,
                  m_name,
                  t_now,
                  curr_score,
                  st.session_state.current_username,
              )
              st.success(
                  f"🎉 تم تسجيل الحضور تلقائياً: {m_name} (الفريق الأصلي:"
                  f" {m_orig_team}) | الدرجة: {curr_score}/10"
              )
              st.balloons()
              time.sleep(1)
              st.rerun()
            else:
              st.info(f"ℹ️ الكشاف {m_name} مسجل مسبقاً في هذه الجلسة.")
          else:
            st.error(
                f"❌ الكود الممسوح ({clean_code}) غير موجود في قاعدة بيانات"
                " الأعضاء!"
            )

      html_live_scanner = (
          """
      <div style="text-align: center; background: #f0f2f6; padding: 15px; border-radius: 12px; margin-bottom: 15px;">
          <div id="reader-live" style="width: 100%; max-width: 350px; margin: auto; border-radius: 10px; overflow: hidden;"></div>
          <button id="btn-start-scan" onclick="startScanner()" style="background-color: #2E7D32; color: white; padding: 12px 24px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; width: 100%;">🟢 فتح الكاميرا للمسح التلقائي</button>
          <button id="btn-stop-scan" onclick="stopScanner()" style="background-color: #C62828; color: white; padding: 10px 20px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; display: none; width: 100%;">إغلاق الكاميرا</button>
          <p id="scan-status" style="color: #1565C0; font-weight: bold; margin-top: 10px; font-size: 15px;"></p>
      </div>

      <script src="https://unpkg.com/html5-qrcode"></script>
      <script>
          let html5QrCode = null;

          function startScanner() {
              document.getElementById('btn-start-scan').style.display = 'none';
              document.getElementById('btn-stop-scan').style.display = 'block';
              document.getElementById('scan-status').innerText = "جاري تفعيل الكاميرا الخلفية...";

              html5QrCode = new Html5Qrcode("reader-live");
              
              Html5Qrcode.getCameras().then(devices => {
                  if (devices && devices.length) {
                      let camId = devices.length > 1 ? devices[devices.length - 1].id : devices[0].id;
                      for (let i = 0; i < devices.length; i++) {
                          let label = devices[i].label.toLowerCase();
                          if ((label.includes('back') || label.includes('rear') || label.includes('environment')) && !label.includes('wide')) {
                              camId = devices[i].id;
                              break;
                          }
                      }

                      html5QrCode.start(
                          camId ? { deviceId: { exact: camId } } : { facingMode: "environment" },
                          { fps: 20, qrbox: { width: 250, height: 250 } },
                          (decodedText) => {
                              document.getElementById('scan-status').innerText = "✅ تم التقاط الكود: " + decodedText;
                              window.location.search = "?auto_code=" + encodeURIComponent(decodedText) + "&team=" + encodeURIComponent('"""
          + selected_team
          + """');
                              stopScanner();
                          },
                          (errorMessage) => {}
                      ).catch(err => {
                          document.getElementById('scan-status').innerText = "خطأ في تشغيل الكاميرا: " + err;
                      });
                  }
              }).catch(err => {
                  document.getElementById('scan-status').innerText = "لا توجد كاميرات متاحة.";
              });
          }

          function stopScanner() {
              if (html5QrCode) {
                  html5QrCode.stop().then(() => {
                      document.getElementById('btn-start-scan').style.display = 'block';
                      document.getElementById('btn-stop-scan').style.display = 'none';
                  }).catch(err => {});
              }
          }
      </script>
      """
      )
      st.components.v1.html(html_live_scanner, height=420)

    st.divider()

    with st.form("manual_attendance_form"):
      manual_code_str = st.text_input("أو أدخل الكود يدوياً:")
      submit_manual = st.form_submit_button("✅ تسجيل يدوي سريع")
      if submit_manual and manual_code_str.strip():
        clean_manual = str(manual_code_str.strip()).strip()
        m = (
            st.session_state.members[
                st.session_state.members["كود العضو"]
                .astype(str)
                .str.strip()
                == clean_manual
            ]
            if not st.session_state.members.empty
            else pd.DataFrame()
        )
        if not m.empty:
          row_data = m.iloc[0]
          m_name = row_data.get("اسم الكشاف", row_data.get("الاسم", "كشاف"))
          if clean_manual not in scanned_members:
            t_now = datetime.datetime.now(CAIRO_TZ).strftime("%H:%M:%S")
            save_draft_scan_firebase(
                selected_team,
                clean_manual,
                m_name,
                t_now,
                curr_score,
                st.session_state.current_username,
            )
            st.success(f"🎉 تم تسجيل: {m_name} | الدرجة: {curr_score}/10")
            time.sleep(0.8)
            st.rerun()
          else:
            st.info(f"ℹ️ الكشاف {m_name} مسجل بالفعل.")
        else:
          st.error("❌ الكود غير مسجل في قاعدة البيانات!")

# --- Tab: التقييمات ---
if "evaluations" in tab_dict:
  with tab_dict["evaluations"]:
    st.subheader("📝 إضافة تقييم أو نشاط كشفي")

    query_eval_p = st.query_params
    scanned_eval_val = ""
    if "auto_eval_code" in query_eval_p:
      scanned_eval_val = query_eval_p["auto_eval_code"]
      st.query_params.clear()

    html_live_scanner_eval = """
    <div style="text-align: center; background: #f0f2f6; padding: 15px; border-radius: 12px; margin-bottom: 15px;">
        <div id="reader-live-eval" style="width: 100%; max-width: 350px; margin: auto; border-radius: 10px; overflow: hidden;"></div>
        <button id="btn-start-eval" onclick="startEvalScanner()" style="background-color: #2E7D32; color: white; padding: 12px 24px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; width: 100%;">🟢 فتح الكاميرا لمسح تقييم الكشاف</button>
        <button id="btn-stop-eval" onclick="stopEvalScanner()" style="background-color: #C62828; color: white; padding: 10px 20px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; display: none; width: 100%;">إغلاق الكاميرا</button>
        <p id="eval-scan-status" style="color: #1565C0; font-weight: bold; margin-top: 10px; font-size: 15px;"></p>
    </div>

    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
        let html5QrCodeEval = null;

        function startEvalScanner() {
            document.getElementById('btn-start-eval').style.display = 'none';
            document.getElementById('btn-stop-eval').style.display = 'block';
            document.getElementById('eval-scan-status').innerText = "جاري تفعيل الكاميرا...";

            html5QrCodeEval = new Html5Qrcode("reader-live-eval");
            
            Html5Qrcode.getCameras().then(devices => {
                if (devices && devices.length) {
                    let camId = devices.length > 1 ? devices[devices.length - 1].id : devices[0].id;
                    for (let i = 0; i < devices.length; i++) {
                        let label = devices[i].label.toLowerCase();
                        if ((label.includes('back') || label.includes('rear') || label.includes('environment')) && !label.includes('wide')) {
                            camId = devices[i].id;
                            break;
                        }
                    }

                    html5QrCodeEval.start(
                        camId ? { deviceId: { exact: camId } } : { facingMode: "environment" },
                        { fps: 20, qrbox: { width: 250, height: 250 } },
                        (decodedText) => {
                            document.getElementById('eval-scan-status').innerText = "✅ تم التقاط الكود: " + decodedText;
                            window.location.search = "?auto_eval_code=" + encodeURIComponent(decodedText);
                            stopEvalScanner();
                        },
                        (errorMessage) => {}
                    ).catch(err => {
                        document.getElementById('eval-scan-status').innerText = "خطأ: " + err;
                    });
                }
            }).catch(err => {
                document.getElementById('eval-scan-status').innerText = "لا توجد كاميرات.";
            });
        }

        function stopEvalScanner() {
            if (html5QrCodeEval) {
                html5QrCodeEval.stop().then(() => {
                    document.getElementById('btn-start-eval').style.display = 'block';
                    document.getElementById('btn-stop-eval').style.display = 'none';
                }).catch(err => {});
            }
        }
    </script>
    """
    st.components.v1.html(html_live_scanner_eval, height=420)

    with st.form("score_form"):
      eval_team = st.selectbox(
          "الفريق", ["الفريق الأول", "الفريق الثاني"], key="eval_team_select"
      )
      s_code_input = st.text_input(
          "كود الكشاف",
          value=str(scanned_eval_val).strip() if scanned_eval_val else "",
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
            t_date = datetime.datetime.now(CAIRO_TZ).strftime("%Y-%m-%d")

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
        t_date = datetime.datetime.now(CAIRO_TZ).strftime("%Y-%m-%d")

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
    st.subheader("⚙️ إدارة الصلاحيات والحسابات")
    all_tabs_list = [
        "تسجيل الحضور",
        "التقييمات",
        "لوحة الصدارة",
        "دليل الكشافة",
        "الشيت السحابي",
    ]
    u_role_choice = st.selectbox(
        "الصلاحية", ["كابتن", "عضو", "آدمن"], key="new_role_sel"
    )
    if u_role_choice == "آدمن":
      chosen_tabs = all_tabs_list
    elif u_role_choice == "عضو":
      chosen_tabs = ["لوحة الصدارة"]
    else:
      chosen_tabs = st.multiselect(
          "القوائم المتاحة للقائد:",
          all_tabs_list,
          default=[
              "تسجيل الحضور",
              "التقييمات",
              "لوحة الصدارة",
              "دليل الكشافة",
          ],
      )

    with st.form("new_user_form", clear_on_submit=True):
      new_username_val = st.text_input("اسم المستخدم")
      new_pass_val = st.text_input("كلمة السر", type="password")
      btn_add_u = st.form_submit_button("حفظ وحفظه سحابياً")
      if btn_add_u:
        if new_username_val.strip() and new_pass_val.strip():
          p_str = ", ".join(chosen_tabs)
          if append_to_google_sheet(
              "المستخدمين",
              [
                  new_username_val.strip(),
                  new_pass_val.strip(),
                  u_role_choice,
                  p_str,
              ],
          ):
            st.success("🎉 تم إنشاء الحساب بنجاح!")
            st.rerun()

    st.divider()
    df_users = load_data_from_gsheet("المستخدمين")
    if not df_users.empty:
      st.dataframe(df_users, use_container_width=True)
