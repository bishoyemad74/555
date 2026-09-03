import datetime
import json
import os
import time
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

# مكتبات الباركود
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

# مكتبات Google Sheets
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


# جلب البيانات المباشر بدون Cache للمزامنة اللحظية بين عدة أجهزة
def load_data_from_gsheet(sheet_name, bypass_cache=False):
  if not bypass_cache:
    return _load_data_cached(sheet_name)
  return _fetch_gsheet_uncached(sheet_name)


@st.cache_data(ttl=10)
def _load_data_cached(sheet_name):
  return _fetch_gsheet_uncached(sheet_name)


def _fetch_gsheet_uncached(sheet_name):
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
    st.error(f"خطأ في المزامنة السحابية ({sheet_name}): {str(e)}")
  return False


def clear_gsheet_tab(sheet_name):
  try:
    client = get_gsheet_client()
    if client:
      sh = client.open_by_key(SPREADSHEET_ID)
      try:
        sheet = sh.worksheet(sheet_name)
        sheet.clear()
        st.cache_data.clear()
        return True
      except Exception:
        pass
  except Exception as e:
    st.error(f"خطأ أثناء تفريغ شيت ({sheet_name}): {e}")
  return False


def verify_current_password(username, current_password):
  try:
    users_df = load_data_from_gsheet("المستخدمين", bypass_cache=True)
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
    users_df = load_data_from_gsheet("المستخدمين", bypass_cache=True)
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

if "eval_reset_counter" not in st.session_state:
  st.session_state.eval_reset_counter = 0
if "manual_reset_counter" not in st.session_state:
  st.session_state.manual_reset_counter = 0
if "scanned_members" not in st.session_state:
  st.session_state.scanned_members = {}
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

    selected_team = st.radio(
        "اختر الفريق لتسجيل الجلسة:",
        ["الفريق الأول", "الفريق الثاني"],
        horizontal=True,
    )

    session_info = load_data_from_gsheet("حالة_الجلسة", bypass_cache=True)
    members_df = load_data_from_gsheet("الأعضاء", bypass_cache=True)

    active_session = None
    if not session_info.empty and "الحالة" in session_info.columns:
      open_rows = session_info[
          (session_info["الحالة"] == "مفتوحة")
          & (session_info["الفريق"] == selected_team)
      ]
      if not open_rows.empty:
        active_session = open_rows.iloc[-1].to_dict()

    if active_session:
      start_ts = float(active_session.get("Start_Timestamp", time.time()))
      st.success(
          f"🟢 **توجد جلسة مفتوحة حالياً لـ ({selected_team})**\n\n"
          f"👤 **القائد:** {active_session.get('المستخدم', '')} | 📅 **بدأت:**"
          f" {active_session.get('التاريخ', '')}"
      )

      draft_df = load_data_from_gsheet("مسودة_الحضور", bypass_cache=True)
      if not draft_df.empty and "كود العضو" in draft_df.columns:
        for _, d_row in draft_df.iterrows():
          c_code = d_row.get("كود العضو", "")
          t_str = str(d_row.get("وقت التسجيل", ""))
          sc_val = float(d_row.get("درجة الحضور", 10.0))
          if c_code:
            st.session_state.scanned_members[str(c_code).strip()] = (
                t_str,
                sc_val,
            )
    else:
      st.info(
          f"ℹ️ لا توجد جلسة مفتوحة حالياً لـ (**{selected_team}**). يمكنك بدء"
          " جلسة جديدة."
      )

    col_start, col_stop, col_sync = st.columns([1.5, 1.5, 1])

    with col_start:
      if st.button("🚀 بدء الاجتماع / الجلسة"):
        if active_session:
          st.error(
              f"❌ توجد جلسة مفتوحة بالفعل لـ ({selected_team}) فتحها القائد"
              f" ({active_session.get('المستخدم', '')})."
          )
        else:
          now_ts = time.time()
          today_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
          new_sess_row = [
              today_date,
              st.session_state.current_username,
              "مفتوحة",
              selected_team,
              str(now_ts),
          ]
          append_to_google_sheet("حالة_الجلسة", new_sess_row)
          st.success(f"🎉 تم بدء الجلسة لـ ({selected_team}) بنجاح!")
          time.sleep(0.5)
          st.rerun()

    with col_stop:
      if st.button("🔴 إغلاق الجلسة وترحيل البيانات"):
        if active_session:
          today = datetime.datetime.now().strftime("%Y-%m-%d")

          if not members_df.empty:
            if "الفريق" not in members_df.columns:
              members_df["الفريق"] = "الفريق الأول"
            team_members = members_df[members_df["الفريق"] == selected_team]
          else:
            team_members = pd.DataFrame()

          for _, row in team_members.iterrows():
            c = str(row.get("كود العضو", "")).strip()
            n = row.get("اسم الكشاف", row.get("الاسم", "غير معروف"))

            if c in st.session_state.scanned_members:
              t_str, sc = st.session_state.scanned_members[c]
              st_name = "حاضر"
            else:
              t_str, sc, st_name = "تلقائي", 0.0, "غائب"

            row_data = [today, c, n, selected_team, st_name, t_str, sc]
            append_to_google_sheet("الحضور", row_data)

          st.session_state.scanned_members = {}
          clear_gsheet_tab("حالة_الجلسة")
          clear_gsheet_tab("مسودة_الحضور")

          st.success("تم إغلاق الجلسة وترحيل البيانات سحابياً! ☁️")
          time.sleep(1)
          st.rerun()

    with col_sync:
      if st.button("🔄 مزامنة الجلسة"):
        st.cache_data.clear()
        st.rerun()

    if active_session:
      start_ts = float(active_session.get("Start_Timestamp", time.time()))
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
          code_str = str(extracted).strip()
          if not members_df.empty and "كود العضو" in members_df.columns:
            members_df["كود_مطابق"] = (
                members_df["كود العضو"].astype(str).str.strip()
            )
            matched = members_df[
                (members_df["كود_مطابق"] == code_str)
                & (members_df["الفريق"] == selected_team)
            ]

            if not matched.empty:
              row_data = matched.iloc[0]
              m_name = row_data.get("اسم الكشاف", "كشاف")
              c_val = row_data.get("كود العضو")

              if code_str not in st.session_state.scanned_members:
                t_now = datetime.datetime.now().strftime("%H:%M:%S")
                draft_row = [
                    c_val,
                    m_name,
                    selected_team,
                    t_now,
                    curr_score,
                    st.session_state.current_username,
                ]
                append_to_google_sheet("مسودة_الحضور", draft_row)
                st.session_state.scanned_members[code_str] = (t_now, curr_score)
                st.success(f"🎉 تم تسجيل: {m_name} ({selected_team})")
                st.balloons()
              else:
                st.info(f"ℹ️ الكشاف {m_name} مسجل بالفعل.")
            else:
              st.error(
                  f"❌ الكود ({code_str}) غير موجود ضمن أعضاء ({selected_team})!"
              )
        else:
          st.error("❌ لم يتم التعرف على الرمز.")

      st.divider()

      with st.form(
          f"manual_attendance_form_{st.session_state.manual_reset_counter}"
      ):
        manual_code_str = st.text_input(
            "أو أدخل الكود يدوياً واضغط تسجيل:", value=""
        )
        submit_manual = st.form_submit_button("✅ تسجيل يدوي سريع")

        if submit_manual:
          if manual_code_str.strip():
            c_input_str = manual_code_str.strip()
            if not members_df.empty and "كود العضو" in members_df.columns:
              members_df["كود_مطابق"] = (
                  members_df["كود العضو"].astype(str).str.strip()
              )
              matched = members_df[
                  (members_df["كود_مطابق"] == c_input_str)
                  & (members_df["الفريق"] == selected_team)
              ]

              if not matched.empty:
                row_data = matched.iloc[0]
                m_name = row_data.get("اسم الكشاف", "كشاف")
                c_val = row_data.get("كود العضو")

                if c_input_str not in st.session_state.scanned_members:
                  t_now = datetime.datetime.now().strftime("%H:%M:%S")
                  draft_row = [
                      c_val,
                      m_name,
                      selected_team,
                      t_now,
                      curr_score,
                      st.session_state.current_username,
                  ]
                  append_to_google_sheet("مسودة_الحضور", draft_row)
                  st.session_state.scanned_members[c_input_str] = (
                      t_now,
                      curr_score,
                  )
                  st.session_state.manual_reset_counter += 1
                  st.success(
                      f"🎉 تم تسجيل: {m_name} ({selected_team}) | الدرجة:"
                      f" {curr_score}/10"
                  )
                  time.sleep(0.5)
                  st.rerun()
                else:
                  st.info(f"ℹ️ الكشاف {m_name} مسجل بالفعل.")
              else:
                st.error(
                    f"❌ الكود ({c_input_str}) غير موجود ضمن أعضاء"
                    f" ({selected_team})!"
                )
            else:
              st.error("تعذر تحميل قائمة الأعضاء.")
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
          st.session_state.eval_scanned_code = str(extracted_eval)
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
          c_str = s_code_input.strip()
          m_all = load_data_from_gsheet("الأعضاء", bypass_cache=True)
          if not m_all.empty and "كود العضو" in m_all.columns:
            m_all["كود_مطابق"] = m_all["كود العضو"].astype(str).str.strip()
            matched = m_all[m_all["كود_مطابق"] == c_str]
            if not matched.empty:
              row_found = matched.iloc[0]
              found_member_name = row_found.get(
                  "اسم الكشاف", row_found.get("الاسم", "غير معروف")
              )
              t_date = datetime.datetime.now().strftime("%Y-%m-%d")

              if append_to_google_sheet(
                  "التقييمات",
                  [
                      t_date,
                      row_found.get("كود العضو"),
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
              st.error("❌ الكود المدخل غير موجود في الأعضاء.")
          else:
            st.error("تعذر تحميل جدول الأعضاء.")
        else:
          st.warning("يرجى إدخال كود الكشاف أولاً.")

# --- Tab: لوحة الصدارة ---
if "leaderboard" in tab_dict:
  with tab_dict["leaderboard"]:
    st.subheader("🏆 ترتيب الكشافة حسَب إجمالي الدرجات")
    col_ref, col_sync = st.columns(2)

    members_lead = load_data_from_gsheet("الأعضاء", bypass_cache=True)
    att_lead = load_data_from_gsheet("الحضور", bypass_cache=True)
    scores_lead = load_data_from_gsheet("التقييمات", bypass_cache=True)

    leaderboard = pd.DataFrame()

    if not members_lead.empty:
      c_name = (
          "كود العضو"
          if "كود العضو" in members_lead.columns
          else members_lead.columns[0]
      )
      n_name = (
          "اسم الكشاف"
          if "اسم الكشاف" in members_lead.columns
          else members_lead.columns[1]
      )
      t_name = "الفريق" if "الفريق" in members_lead.columns else "الفريق"

      if t_name not in members_lead.columns:
        members_lead[t_name] = "الفريق الأول"

      leaderboard = members_lead[[c_name, n_name, t_name]].copy()

      # معالجة آمنة لجدول الحضور لحماية الكود من KeyError
      if not att_lead.empty and "كود العضو" in att_lead.columns:
        att_score_col = [
            c
            for c in att_lead.columns
            if "درجة" in c or "الحضور" in c or "Score" in c
        ]
        if att_score_col:
          target_col = att_score_col[0]
          att_lead[target_col] = pd.to_numeric(
              att_lead[target_col], errors="coerce"
          ).fillna(0)
          att_sum = (
              att_lead.groupby("كود العضو")[target_col].sum().reset_index()
          )
          att_sum.columns = [c_name, "نقاط الحضور"]
        else:
          att_sum = pd.DataFrame(columns=[c_name, "نقاط الحضور"])
      else:
        att_sum = pd.DataFrame(columns=[c_name, "نقاط الحضور"])

      # معالجة آمنة لجدول التقييمات
      if not scores_lead.empty and "كود العضو" in scores_lead.columns:
        sc_col = [
            c
            for c in scores_lead.columns
            if "الدرجة" in c or "درجة" in c or "Score" in c
        ]
        if sc_col:
          sc_v = sc_col[0]
          scores_lead[sc_v] = pd.to_numeric(
              scores_lead[sc_v], errors="coerce"
          ).fillna(0)
          sc_sum = scores_lead.groupby("كود العضو")[sc_v].sum().reset_index()
          sc_sum.columns = [c_name, "نقاط التقييمات"]
        else:
          sc_sum = pd.DataFrame(columns=[c_name, "نقاط التقييمات"])
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
        m_curr = load_data_from_gsheet("الأعضاء", bypass_cache=True)
        if not m_curr.empty and "كود العضو" in m_curr.columns:
          max_c = (
              pd.to_numeric(m_curr["كود العضو"], errors="coerce")
              .fillna(0)
              .max()
          )
          new_c = int(max_c + 1)
        else:
          new_c = 21820261

        t_date = datetime.datetime.now().strftime("%Y-%m-%d")

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
          st.session_state.form_version += 1
          st.success(
              f"🎉 تمت إضافة الكشاف ({cleaned_input_name}) لـ ({m_team}) بكود:"
              f" {new_c}!"
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
    users_list = load_data_from_gsheet("المستخدمين", bypass_cache=True)
    if not users_list.empty:
      st.dataframe(users_list, use_container_width=True)
