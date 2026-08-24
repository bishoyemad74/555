import streamlit as st
import pandas as pd
import datetime
import time

# 1. تهيئة الصفحة وإخفاء القوائم
st.set_page_config(
    page_title="كشافة أم النور",
    page_icon="⚜️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تنسيق الواجهة وإخفاء شريط الأدوات
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

# إدارة الذاكرة
if 'members' not in st.session_state or 'اسم الكشاف' not in st.session_state.members.columns:
    st.session_state.members = pd.DataFrame([
        {"كود العضو": 21820261, "اسم الكشاف": "مينا سامح", "الفرقة": "فتيان", "تاريخ الانضمام": "2026-01-15"},
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

GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/"

tabs = st.tabs(["⏱️ تسجيل الحضور", "📝 التقييمات", "👥 دليل الكشافة", "☁️ الشيت السحابي (Excel)"])

# --- Tab 1: الحضور والغياب ---
with tabs[0]:
    st.subheader("⏱️ إدارة جلسة الحضور التنازلي")
    
    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("🚀 بدء الاجتماع / الجلسة"):
            st.session_state.session_start_time = time.time()
            st.session_state.scanned_members = {}
            st.success("بدأت الجلسة! الدرجة الحالية 10/10.")
            
    with col_stop:
        if st.button("🔴 إغلاق الجلسة وترحيل الغياب"):
            if st.session_state.session_start_time is not None:
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                new_att = []
                new_sc = []
                for _, row in st.session_state.members.iterrows():
                    c = row["كود العضو"]
                    n = row["اسم الكشاف"]
                    if c in st.session_state.scanned_members:
                        t_str, sc = st.session_state.scanned_members[c]
                        st_name = "حاضر"
                    else:
                        t_str = "تلقائي"
                        sc = 0.0
                        st_name = "غائب"
                    
                    new_att.append({
                        "التاريخ": today, "كود العضو": c, "اسم الكشاف": n,
                        "حالة الحضور": st_name, "وقت التسجيل": t_str, "درجة الحضور": sc
                    })
                    if st_name == "حاضر":
                        new_sc.append({
                            "تاريخ التقييم": today, "كود العضو": c, "اسم الكشاف": n,
                            "نوع التقييم": "الالتزام بموعد الاجتماع", "الدرجة (من 10)": sc, "ملاحظات": f"حضور {t_str}"
                        })
                
                st.session_state.attendance = pd.concat([st.session_state.attendance, pd.DataFrame(new_att)], ignore_index=True)
                st.session_state.scores = pd.concat([st.session_state.scores, pd.DataFrame(new_sc)], ignore_index=True)
                st.session_state.session_start_time = None
                st.session_state.scanned_members = {}
                st.success("تم إغلاق الجلسة وترحيل الدرجات!")
            else:
                st.warning("لا توجد جلسة نشطة حالياً.")

    if st.session_state.session_start_time is not None:
        elapsed_min = int((time.time() - st.session_state.session_start_time) // 60)
        curr_score = max(0.0, round(10.0 - (elapsed_min * 0.2), 1))
        st.info(f"⏱️ زمن الاجتماع: {elapsed_min} دقيقة | درجة الحضور الآن: **{curr_score} / 10**")
    else:
        curr_score = 10.0

    st.divider()
    st.subheader("📋 تسجيل الكشاف")
    
    # التقاط الصورة للتوثيق
    img_input = st.camera_input("التقط صورة كارت الكشاف للتسجيل السريع")
    
    manual_code = st.number_input("ادخل كود الكشاف:", step=1, value=21820261)
    
    if st.button("✅ تسجيل الحضور"):
        if manual_code > 0:
            m = st.session_state.members[st.session_state.members["كود العضو"] == manual_code]
            if not m.empty:
                m_name = m.iloc[0]["اسم الكشاف"]
                t_now = datetime.datetime.now().strftime("%H:%M:%S")
                st.session_state.scanned_members[manual_code] = (t_now, curr_score)
                st.success(f"تم تسجيل: {m_name} | الدرجة: {curr_score}/10")
            else:
                st.error("الكود غير مسجل في دليل الكشافة!")

    st.write("📋 **الحاضرون في هذه الجلسة:**")
    if st.session_state.scanned_members:
        res = []
        for c, (t, s) in st.session_state.scanned_members.items():
            m_f = st.session_state.members[st.session_state.members["كود العضو"] == c]
            name = m_f.iloc[0]["اسم الكشاف"] if not m_f.empty else "غير معروف"
            res.append({"كود العضو": c, "اسم الكشاف": name, "وقت التسجيل": t, "الدرجة": s})
        st.dataframe(pd.DataFrame(res), use_container_width=True)

# --- Tab 2: تقييمات النشاط الكشفي ---
with tabs[1]:
    st.subheader("📝 إضافة تقييم أو نشاط كشفي")
    with st.form("score_form"):
        s_code = st.number_input("كود الكشاف", step=1, value=1001)
        s_type = st.selectbox("نوع التقييم", ["الزي الكشفي", "السلوك والانضباط", "الأنشطة والمهارات", "المخيمات والرحلات", "اختبارات الترقي"])
        s_val = st.number_input("الدرجة (من 10)", min_value=0.0, max_value=10.0, step=0.5, value=10.0)
        s_notes = st.text_input("ملاحظات / اسم النشاط")
        
        if st.form_submit_button("حفظ التقييم"):
            m = st.session_state.members[st.session_state.members["كود العضو"] == s_code]
            if not m.empty:
                m_name = m.iloc[0]["اسم الكشاف"]
                new_s = {
                    "تاريخ التقييم": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "كود العضو": s_code,
                    "اسم الكشاف": m_name,
                    "نوع التقييم": s_type,
                    "الدرجة (من 10)": s_val,
                    "ملاحظات": s_notes
                }
                st.session_state.scores = pd.concat([st.session_state.scores, pd.DataFrame([new_s])], ignore_index=True)
                st.success(f"تم تسجيل تقييم ({s_type}) للكشاف {m_name}")
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
            new_m = {
                "كود العضو": new_c,
                "اسم الكشاف": m_name,
                "الفرقة": m_dept,
                "تاريخ الانضمام": datetime.datetime.now().strftime("%Y-%m-%d")
            }
            st.session_state.members = pd.concat([st.session_state.members, pd.DataFrame([new_m])], ignore_index=True)
            st.success(f"تم تسجيل {m_name} - الكود الخاص به: {new_c}")

    st.dataframe(st.session_state.members, use_container_width=True)

# --- Tab 4: شيت السحاب المباشر وGoogle Sheets ---
with tabs[3]:
    st.subheader("☁️ الربط المباشر مع شيت السحاب (Google Sheets / Excel)")
    st.link_button("🔗 فتح جدول البيانات على Google Drive مباشر", GOOGLE_SHEET_URL)
    st.divider()
    
    summary_data = []
    for _, m_row in st.session_state.members.iterrows():
        c = m_row["كود العضو"]
        n = m_row["اسم الكشاف"]
        u_sc = st.session_state.scores[st.session_state.scores["كود العضو"] == c]
        tot = u_sc["الدرجة (من 10)"].sum() if not u_sc.empty else 0.0
        summary_data.append({"كود العضو": c, "اسم الكشاف": n, "إجمالي درجات الكشافة": tot})
    
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    if st.button("توليد ملف Excel المحدث"):
        with pd.ExcelWriter("kashaf_am_elnoor.xlsx") as writer:
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="الدرجات الكلية", index=False)
            st.session_state.attendance.to_excel(writer, sheet_name="سجل الحضور", index=False)
            st.session_state.scores.to_excel(writer, sheet_name="سجل التقييمات", index=False)
        with open("kashaf_am_elnoor.xlsx", "rb") as f:
            st.download_button("💾 اضغط هنا لتنزيل ملف Excel", f, file_name="kashaf_am_elnoor.xlsx")
