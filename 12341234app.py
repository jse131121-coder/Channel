import streamlit as st
import sqlite3, os
from datetime import datetime

st.set_page_config(page_title="rocade", layout="wide")
st.markdown("# 💬 rocade")

# ================= DB =================
conn = sqlite3.connect("rocade.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id TEXT PRIMARY KEY,
    pw TEXT,
    name TEXT,
    image TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    image TEXT,
    created TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER,
    content TEXT,
    created TEXT,
    admin_id TEXT,
    admin_name TEXT,
    admin_image TEXT
)
""")

conn.commit()
os.makedirs("uploads", exist_ok=True)

# ================= SESSION =================
if "admin" not in st.session_state:
    st.session_state.admin = None
if "login_open" not in st.session_state:
    st.session_state.login_open = False

# ================= HEADER =================
col = st.columns([8,2])
with col[1]:
    if not st.session_state.admin:
        if st.button("Admin Login"):
            st.session_state.login_open = True
    else:
        st.image(st.session_state.admin[3], width=40)
        st.write(st.session_state.admin[2])
        if st.button("Logout"):
            st.session_state.admin = None
            st.rerun()

# ================= LOGIN =================
if st.session_state.login_open:
    st.subheader("관리자 로그인")
    i = st.text_input("ID")
    p = st.text_input("PW", type="password")
    if st.button("Login"):
        c.execute("SELECT * FROM admin WHERE id=? AND pw=?", (i,p))
        a = c.fetchone()
        if a:
            st.session_state.admin = a
            st.session_state.login_open = False
            st.rerun()
        else:
            st.error("로그인 실패")

# ================= 관리자 생성 (관리자만 가능) =================
if st.session_state.admin:
    with st.expander("➕ 관리자 추가"):
        ni = st.text_input("새 관리자 ID")
        np = st.text_input("PW", type="password")
        nn = st.text_input("이름")
        img = st.file_uploader("프로필 사진", type=["jpg","png"])

        if st.button("관리자 생성"):
            try:
                path = None
                if img:
                    path = f"uploads/{img.name}"
                    with open(path,"wb") as f:
                        f.write(img.getbuffer())

                c.execute(
                    "INSERT INTO admin VALUES (?,?,?,?)",
                    (ni, np, nn, path)
                )
                conn.commit()
                st.success("✅ 관리자 생성 완료")
            except:
                st.error("이미 존재하는 ID")

# ================= USER QUESTION =================
st.markdown("## ✉️ 질문 보내기")
msg = st.text_area("내용")
img = st.file_uploader("사진", type=["png","jpg"])

if st.button("전송"):
    if msg or img:
        path = None
        if img:
            path = f"uploads/{img.name}"
            with open(path,"wb") as f:
                f.write(img.getbuffer())

        c.execute(
            "INSERT INTO messages VALUES (NULL,?,?,?)",
            (msg, path, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        st.rerun()

# ================= CHAT =================
st.markdown("---")
messages = c.execute(
    "SELECT * FROM messages ORDER BY id DESC"
).fetchall()

for m in messages:
    st.markdown(
        f"""
        <div style="
        background:#f1f1f1;
        padding:14px;
        border-radius:18px;
        max-width:70%;
        margin-left:auto;
        margin-bottom:8px;">
        {m[1]}
        <div style='font-size:11px;color:gray'>{m[3]}</div>
        </div>
        """, unsafe_allow_html=True
    )

    if m[2]:
        st.image(m[2], width=220)

    if st.session_state.admin:
        if st.button("❌ 질문 삭제", key=f"del_{m[0]}"):
            c.execute("DELETE FROM messages WHERE id=?", (m[0],))
            c.execute("DELETE FROM replies WHERE message_id=?", (m[0],))
            conn.commit()
            st.rerun()

    replies = c.execute(
        "SELECT * FROM replies WHERE message_id=?",
        (m[0],)
    ).fetchall()

    for r in replies:
        st.markdown(
            f"""
            <div style="display:flex; margin:10px 0;">
            <img src="{r[6]}" width="38" style="border-radius:50%; margin-right:8px;">
            <div style="
            background:#dbeafe;
            padding:14px;
            border-radius:18px;
            max-width:70%;">
            <b>{r[5]}</b><br>
            {r[2]}
            <div style='font-size:11px;color:gray'>{r[3]}</div>
            </div>
            </div>
            """, unsafe_allow_html=True
        )

    if st.session_state.admin:
        reply = st.text_area("답변하기", key=f"r_{m[0]}")
        if st.button("답변 전송", key=f"b_{m[0]}"):
            if reply:
                a = st.session_state.admin
                c.execute(
                    "INSERT INTO replies VALUES (NULL,?,?,?,?,?,?)",
                    (
                        m[0], reply,
                        datetime.now().strftime("%Y-%m-%d %H:%M"),
                        a[0], a[2], a[3]
                    )
                )
                conn.commit()
                st.rerun()

    st.markdown("---")
