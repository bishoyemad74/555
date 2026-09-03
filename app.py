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

# مكتبات الربط المباشر مع Google Sheets
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


def load_data_from_gsheet(sheet_name, bypass_cache=False):
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

if "active_teams" not in st.session_state:
  st.session_state.active_teams = {}
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

    # زر تحديث حالة الجلسات بين الأجهزة
    if st.button("🔄 تحديث حالة الجلسات من السحاب"):
      st.cache_data.clear()
      st.session_state.active_teams = {}
      st.rerun()

    # --- فحص شامل وعام لجميع الجلسات المفتوحة في Google Sheets مباشرة ---
    session_info = load_data_from_gsheet("حالة_الجلسة", bypass_cache=True)
    st.session_state.active_teams = {}

    if not session_info.empty and "الحالة" in session_info.columns:
      open_rows = session_info[session_info["الحالة"] == "مفتوحة"]
      for _, r in open_rows.iterrows():
        t_name = str(r.get("الفريق", "")).strip()
        if t_name:
          st.session_state.active_teams[t_name] = r.to_dict()

    # تنبيه عام ثابت بأي جلسة مفتوحة في التطبيق
    if st.session_state.active_teams:
      for team_k, sess_v in st.session_state.active_teams.items():
        st.success(
            f"🟢 **جلسة نشطة حالياً لـ ({team_k})** | 👤 **القائد:**"
            f" {sess_v.get('المستخدم', '')} | 📅 **بدأت:**"
            f" {sess_v.get('التاريخ', '')}"
        )
    else:
      st.info("ℹ️ لا توجد أي جلسات مفتوحة حالياً في أي فريق.")

    st.divider()

    selected_team = st.radio(
        "اختر الفريق للعمل عليه:",
        ["الفريق الأول", "الفريق الثاني"],
        horizontal=True,
    )

    active_session = st.session_state.active_teams.get(selected_team, None)

    if active_session:
      draft_df = load_data_from_gsheet("مسودة_الحضور", bypass_cache=True)
      if not draft_df.empty and "كود العضو" in draft_df.columns:
        for _, d_row in draft_df.iterrows():
          c_code = d_row.get("كود العضو", "")
          t_str = str(d_row.get("وقت التسجيل", ""))
          sc_val = float(d_row.get("درجة الحضور", 10.0))
          if c_code:
            try:
              st.session_state.scanned_members[int(c_code)] = (t_str, sc_val)
            except ValueError:
              st.session_state.scanned_members[c_code] = (t_str, sc_val)

    col_start, col_stop = st.columns(2)

    with col_start:
      if st.button("🚀 بدء الاجتماع / الجلسة"):
        # جلب البيانات مباشرة بدون كاش للتأكد في نفس اللحظة
        st.cache_data.clear()
        latest_check = load_data_from_gsheet("حالة_الجلسة", bypass_cache=True)
        already_open = False
        if not latest_check.empty and "الحالة" in latest_check.columns:
          existing = latest_check[
              (latest_check["الحالة"] == "مفتوحة")
              & (
                  latest_check["الفريق"].astype(str).str.strip()
                  == selected_team
              )
          ]
          if not existing.empty:
            already_open = True
            m_user = existing.iloc[-1].get("المستخدم", "قائد آخر")
            m_time = existing.iloc[-1].get("التاريخ", "")
            st.error(
                f"❌ عذراً! توجد جلسة مفتوحة بالفعل لـ ({selected_team}) قام"
                f" بفتحها القائد ({m_user}) في ({m_time})."
            )

        if not already_open:
          now_ts = time.time()
          today_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

          new_sess_row = [
              today_date,
              st.session_state.current_username,
              "مفتوحة",
              selected_team,
              str(now_ts),
          ]
          if append_to_google_sheet("حالة_الجلسة", new_sess_row):
            st.success(f"🎉 تم بدء الجلسة لـ ({selected_team}) بنجاح!")
            st.cache_data.clear()
            time.sleep(0.5)
            st.rerun()

    with col_stop:
      if st.button("🔴 إغلاق الجلسة وترحيل البيانات للسحاب فورا"):
        if active_session:
          today = datetime.datetime.now().strftime("%Y-%m-%d")
          new_att = []

          if (
              not st.session_state.members.empty
              and "الفريق" not in st.session_state.members.columns
          ):
            st.session_state.members["الفريق"] = "الفريق الأول"

          team_members = (
              st.session_state.members[
                  st.session_state.members["الفريق"] == selected_team
              ]
              if "الفريق" in st.session_state.members.columns
              else st.session_state.members
          )

          for _, row in team_members.iterrows():
            c = row.get("كود العضو", "")
            n = row.get("اسم الكشاف", row.get("الاسم", "غير معروف"))

            if c in st.session_state.scanned_members:
              t_str, sc = st.session_state.scanned_members[c]
              st_name = "حاضر"
            else:
              t_str, sc, st_name = "تلقائي", 0.0, "غائب"

            row_data = [today, c, n, selected_team, st_name, t_str, sc]
            append_to_google_sheet("الحضور", row_data)

            new_att.append({
                "التاريخ": today,
                "كود العضو": c,
                "اسم الكشاف": n,
                "الفريق": selected_team,
                "حالة الحضور": st_name,
                "وقت التسجيل": t_str,
                "درجة الحضور": sc,
            })

          st.session_state.attendance = pd.concat(
              [st.session_state.attendance, pd.DataFrame(new_att)],
              ignore_index=True,
          )

          if selected_team in st.session_state.active_teams:
            del st.session_state.active_teams[selected_team]

          st.session_state.scanned_members = {}

          clear_gsheet_tab("حالة_الجلسة")
          clear_gsheet_tab("مسودة_الحضور")

          st.success("تم إغلاق الجلسة وترحيل البيانات سحابياً! ☁️")
          time.sleep(1)
          st.rerun()
        else:
          st.warning("لا توجد جلسة نشطة لهذا الفريق حالياً.")

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
          try:
            code_val = int(extracted)
            m = (
                st.session_state.members[
                    (st.session_state.members["كود العضو"] == code_val)
                    & (st.session_state.members["الفريق"] == selected_team)
                ]
                if "الفريق" in st.session_state.members.columns
                else st.session_state.members[
                    st.session_state.members["كود العضو"] == code_val
                ]
            )

            if not m.empty:
              row_data = m.iloc[0]
              m_name = row_data.get(
                  "اسم الكشاف", row_data.get("الاسم", "كشاف")
              )

              if code_val not in st.session_state.scanned_members:
                t_now = datetime.datetime.now().strftime("%H:%M:%S")
                st.session_state.scanned_members[code_val] = (t_now, curr_score)

                draft_row = [
                    code_val,
                    m_name,
                    selected_team,
                    t_now,
                    curr_score,
                    st.session_state.current_username,
                ]
                append_to_google_sheet("مسودة_الحضور", draft_row)

                st.success(
                    f"🎉 تم تسجيل حضور: {m_name} ({selected_team}) - كود:"
                    f" {code_val}"
                )
                st.balloons()
              else:
                st.info(
                    f"ℹ️ الكشاف {m_name} مسجل بالفعل في هذه الجلسة."
                )
            else:
              st.error(
                  f"❌ الكود ({code_val}) غير مسجل ضمن أعضاء {selected_team}!"
              )
          except ValueError:
            st.warning(f"الـ QR يحتوي على نص: {extracted}")
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
            try:
              manual_code = int(manual_code_str.strip())
              m = (
                  st.session_state.members[
                      (st.session_state.members["كود العضو"] == manual_code)
                      & (st.session_state.members["الفريق"] == selected_team)
                  ]
                  if "الفريق" in st.session_state.members.columns
                  else st.session_state.members[
                      st.session_state.members["كود العضو"] == manual_code
                  ]
              )

              if not m.empty:
                row_data = m.iloc[0]
                m_name = row_data.get(
                    "اسم الكشاف", row_data.get("الاسم", "كشاف")
                )
                if manual_code not in st.session_state.scanned_members:
                  t_now = datetime.datetime.now().strftime("%H:%M:%S")
                  st.session_state.scanned_members[manual_code] = (
                      t_now,
                      curr_score,
                  )

                  draft_row = [
                      manual_code,
                      m_name,
                      selected_team,
                      t_now,
                      curr_score,
                      st.session_state.current_username,
                  ]
                  append_to_google_sheet("مسودة_الحضور", draft_row)

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
            except ValueError:
              st.error("يرجى إدخال أرقام فقط لكود الكشاف.")
          else:
            st.warning("يرجى إدخال كود الكشاف أولاً.")

# --- باقي القوائم ---
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
          try:
            s_code = int(s_code_input.strip())
            matched = st.session_state.members[
                st.session_state.members["كود العضو"] == s_code
            ]
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
                      s_code,
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
          except ValueError:
            st.error("⚠️ يرجى إدخال أرقام صحيحة للكود.")
        else:
          st.warning("يرجى إدخال كود الكشاف أولاً.")

if "leaderboard" in tab_dict:
  with tab_dict["leaderboard"]:
    st.subheader("🏆 ترتيب الكشافة حسَب إجمالي الدرجات")
    col_ref, col_sync = st.columns(2)
    leaderboard = pd.DataFrame()

    if not st.session_state.members.empty:
      members_df = st.session_state.members.copy()
      c_name = "كود العضو" if "كود العضو" in members_df.columns else members_df.columns[0]
      n_name = (
          "اسم الكشاف"
          if "اسم الكشاف" in members_df.columns
          else members_df.columns[1]
      )
      t_name = "الفريق" if "الفريق" in members_df.columns else "الفريق"

      if t_name not in members_df.columns:
        members_df[t_name] = "الفريق الأول"

      leaderboard = members_df[[c_name, n_name, t_name]].copy()

      att_df = st.session_state.attendance
      if not att_df.empty and "كود العضو" in att_df.columns:
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

      sc_df = st.session_state.scores
      if not sc_df.empty and "كود العضو" in sc_df.columns:
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
        max_c = (
            st.session_state.members["كود العضو"].max()
            if not st.session_state.members.empty
            else 21820260
        )
        new_c = int(max_c + 1)
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
