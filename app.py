import streamlit as st
import pandas as pd
import datetime
import time

st.set_page_config(
    page_title="كشافة أم النور ",
    page_icon="⚜️",
    layout="centered"
)

st.title("⚜️ كشافة أم النور")
# تطبيق اتجاه RTL ونمط بصري جذاب
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Tajawal', sans-serif;
        direction: rtl;
        text-align: right;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px;
    }
    .metric-box {
        background-color: #f0f4f8;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border-right: 5px solid #1E88E5;
    }
    </style>
""", unsafe_allow_html=True)

# إدارة حالة البيانات في الجلسة (Session State)
if 'members' not in st.session_state:
    st.session_state.members = pd.DataFrame([
        {"كود العضو": 1001, "اسم العضو": "أحمد محمود علي", "القسم": "برمجة", "تاريخ الانضمام": "2026-01-15", "الحالة": "نشط"},
        {"كود العضو": 1002, "اسم العضو": "سارة محمد إبراهيم", "القسم": "تصميم", "تاريخ الانضمام": "2026-01-15", "الحالة": "نشط"},
        {"كود العضو": 1003, "اسم العضو": "عمر خالد يوسف", "القسم": "علاقات عامة", "تاريخ الانضمام": "2026-01-20", "الحالة": "نشط"}
    ])

if 'attendance' not in st.session_state:
    st.session_state.attendance = pd.DataFrame(columns=["التاريخ", "كود العضو", "اسم العضو", "حالة الحضور", "وقت التسجيل", "درجة الحضور (من 10)"])

if 'scores' not in st.session_state:
    st.session_state.scores = pd.DataFrame(columns=["تاريخ التقييم", "كود العضو", "اسم العضو", "نوع التقييم", "الدرجة (من 10)", "ملاحظات"])

if 'session_start_time' not in st.session_state:
    st.session_state.session_start_time = None

if 'scanned_members' not in st.session_state:
    st.session_state.scanned_members = {}
tabs = st.tabs(["⏱️ تسجيل الحضور ", "📝 تقييمات الأعضاء", "👥 دليل الأعضاء", "📊 الدرجات الكلية"])

# --- Tab 1: الحضور والغياب  ---
with tabs[0]:
    st.header("تسجيل الحضور")
    
    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("🚀 بدء جلسة الحضور الان"):
            st.session_state.session_start_time = time.time()
            st.session_state.scanned_members = {}
            st.success("بدأت الجلسة الآن! الدرجة المبتدأة هي 10/10.")
            
    with col_stop:
        if st.button("🔴 إغلاق الجلسة وتثبيت الغياب"):
            if st.session_state.session_start_time is not None:
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                new_att = []
                new_sc = []
                for _, row in st.session_state.members.iterrows():
                    c = row["كود العضو"]
                    n = row["اسم العضو"]
                    if c in st.session_state.scanned_members:
                        t_str, sc = st.session_state.scanned_members[c]
                        st_name = "حاضر"
                    else:
                        t_str = "تلقائي"
                        sc = 0.0
                        st_name = "غائب"
                    
                    new_att.append({
                        "التاريخ": today, "كود العضو": c, "اسم العضو": n,
                        "حالة الحضور": st_name, "وقت التسجيل": t_str, "درجة الحضور (من 10)": sc
                    })
                    if st_name == "حاضر":
                        new_sc.append({
                            "تاريخ التقييم": today, "كود العضو": c, "اسم العضو": n,
                            "نوع التقييم": "التزام الحضور بالوقت", "الدرجة (من 10)": sc, "ملاحظات": f"تسجيل الساعة {t_str}"
                        })
                
                st.session_state.attendance = pd.concat([st.session_state.attendance, pd.DataFrame(new_att)], ignore_index=True)
                st.session_state.scores = pd.concat([st.session_state.scores, pd.DataFrame(new_sc)], ignore_index=True)
                st.session_state.session_start_time = None
                st.session_state.scanned_members = {}
                st.success("تم إغلاق الجلسة وترحيل الدرجات لسجل التقييمات والحضور بنجاح!")
            else:
                st.warning("لا توجد جلسة نشطة لإغلاقها.")

    # التوقيت الحالي والدرجة المستحقة
    if st.session_state.session_start_time is not None:
        elapsed_min = int((time.time() - st.session_state.session_start_time) // 60)
        curr_score = max(0.0, round(10.0 - (elapsed_min * 0.2), 1))
        st.info(f"⏱️ زمن الجلسة: {elapsed_min} دقيقة | الدرجة الحالية لمن يسجل الآن: **{curr_score} / 10**")
    else:
        curr_score = 10.0
        st.warning("الجلسة غير نشطة حالياً.")

    st.subheader("مسح الباركود / إدخال الكود")
    code_input = st.number_input("أدخل كود العضو:", step=1, value=0)
    if st.button("تسجيل الحضور للكود"):
        if code_input > 0:
            m = st.session_state.members[st.session_state.members["كود العضو"] == code_input]
            if not m.empty:
                m_name = m.iloc[0]["اسم العضو"]
                t_now = datetime.datetime.now().strftime("%H:%M:%S")
                st.session_state.scanned_members[code_input] = (t_now, curr_score)
                st.success(f"تم تسجيل حضور: {m_name} | الدرجة: {curr_score}/10")
            else:
                st.error("الكود غير موجود في قائمة الأعضاء!")

    st.write("📋 **الحاضرون المقيدون في الجلسة الحالية:**")
    if st.session_state.scanned_members:
        res = []
        for c, (t, s) in st.session_state.scanned_members.items():
            name = st.session_state.members[st.session_state.members["كود العضو"] == c].iloc[0]["اسم العضو"]
            res.append({"كود العضو": c, "اسم العضو": name, "وقت التسجيل": t, "الدرجة": s})
        st.dataframe(pd.DataFrame(res), use_container_width=True)
    else:
        st.text("لم يتم تسجيل أي حضور حتى الآن.")

# --- Tab 2: تسجيل التقييمات ---
with tabs[1]:
    st.header("تسجيل التقييمات والمهام (الدرجة العظمى: 10)")
    with st.form("score_form"):
        s_code = st.number_input("كود العضو", step=1, value=1001)
        s_type = st.selectbox("نوع التقييم", ["درجة التفاعل", "درجة المهام", "مشروع جديد", "اختبار سريع", "مشاركة ورشة"])
        s_val = st.number_input("الدرجة (من 10)", min_value=0.0, max_value=10.0, step=0.5, value=10.0)
        s_notes = st.text_input("ملاحظات")
        btn_submit_score = st.form_submit_button("حفظ التقييم")
        
        if btn_submit_score:
            m = st.session_state.members[st.session_state.members["كود العضو"] == s_code]
            if not m.empty:
                m_name = m.iloc[0]["اسم العضو"]
                new_s = {
                    "تاريخ التقييم": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "كود العضو": s_code,
                    "اسم العضو": m_name,
                    "نوع التقييم": s_type,
                    "الدرجة (من 10)": s_val,
                    "ملاحظات": s_notes
                }
                st.session_state.scores = pd.concat([st.session_state.scores, pd.DataFrame([new_s])], ignore_index=True)
                st.success(f"تم تسجيل تقييم ({s_type}) بـ {s_val}/10 للعضو {m_name}")
            else:
                st.error("كود العضو غير موجود!")

# --- Tab 3: دليل الأعضاء ---
with tabs[2]:
    st.header("إضافة عضو جديد")
    with st.form("add_member_form"):
        m_name = st.text_input("اسم العضو كامل")
        m_dept = st.text_input("القسم / اللجنة")
        btn_add_m = st.form_submit_button("إضافة العضو")
        if btn_add_m and m_name:
            max_c = st.session_state.members["كود العضو"].max() if not st.session_state.members.empty else 1000
            new_c = int(max_c + 1)
            new_m = {
                "كود العضو": new_c,
                "اسم العضو": m_name,
                "القسم": m_dept or "عام",
                "تاريخ الانضمام": datetime.datetime.now().strftime("%Y-%m-%d"),
                "الحالة": "نشط"
            }
            st.session_state.members = pd.concat([st.session_state.members, pd.DataFrame([new_m])], ignore_index=True)
            st.success(f"تم تسجيل {m_name} بنجاح! الكود: {new_c}")

    st.subheader("قائمة الأعضاء الحاليين")
    st.dataframe(st.session_state.members, use_container_width=True)

# --- Tab 4: الدرجات الكلية للأعضاء ---
with tabs[3]:
    st.header("الدرجات الكلية للأعضاء (Dashboard)")
    if not st.session_state.members.empty:
        summary_data = []
        for _, m_row in st.session_state.members.iterrows():
            c = m_row["كود العضو"]
            n = m_row["اسم العضو"]
            user_scores = st.session_state.scores[st.session_state.scores["كود العضو"] == c]
            total_sc = user_scores["الدرجة (من 10)"].sum() if not user_scores.empty else 0.0
            cnt = len(user_scores)
            avg_sc = round(total_sc / cnt, 2) if cnt > 0 else 0.0
