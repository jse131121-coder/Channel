import streamlit as st
import sqlite3
import os
from datetime import datetime

# ================= PAGE =================
st.set_page_config(page_title="Private-board", layout="wide")
st.markdown("# 🗂️ Private-board")

# ================= DB =================
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id TEXT PRIMARY KEY,
    pw TEXT,
    name TEXT,
    profile TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    image TEXT,
    pinned INTEGER,
    created TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    writer TEXT,
    content TEXT,
    is_admin INTEGER,
    parent_id INTEGER
)
""")

conn.commit()
os.makedirs("uploads", exist_ok=True)

# ================= SESSION =================
if "admin" not in st.session_state:
    st.session_state.admin = None
if "login_open" not in st.session_state:
    st.session_state.login_open = False

# ================= TOP LOGIN =================
top = st.columns([8, 2])

with top[1]:
    if st.session_state.admin is None:
        if st.button("Login"):
            st.session_state.login_open = True
    else:
        st.markdown("🎤 **ARTIST**")
        st.write(st.session_state.admin[2])
        if st.button("Logout"):
            st.session_state.admin = None
            st.rerun()

# ================= LOGIN / ADMIN CREATE =================
if st.session_state.login_open:
    st.markdown("### 🔐 관리자 로그인 / 생성")
    tab_login, tab_create = st.tabs(["로그인", "관리자 생성"])

    with tab_login:
        login_id = st.text_input("ID", key="login_id")
        login_pw = st.text_input("PW", type="password", key="login_pw")

        if st.button("로그인 완료"):
            c.execute(
                "SELECT * FROM admins WHERE id=? AND pw=?",
                (login_id, login_pw)
            )
            admin = c.fetchone()

            if admin:
                st.session_state.admin = admin
                st.session_state.login_open = False
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 틀렸어요")

    with tab_create:
        new_id = st.text_input("새 관리자 ID")
        new_pw = st.text_input("새 관리자 PW", type="password")
        new_name = st.text_input("아티스트 이름")

        if st.button("관리자 생성"):
            if new_id and new_pw and new_name:
                try:
                    c.execute(
                        "INSERT INTO admins VALUES (?,?,?,?)",
                        (new_id, new_pw, new_name, "")
                    )
                    conn.commit()
                    st.success("✅ 관리자 계정 생성 완료")
                except sqlite3.IntegrityError:
                    st.error("이미 존재하는 ID입니다")
            else:
                st.warning("모든 칸을 입력해주세요")

# ================= WRITE =================
st.markdown("---")
st.markdown("## ✍️ 글쓰기")

title = st.text_input("제목")
content = st.text_area("내용")
img = st.file_uploader("이미지 업로드", type=["jpg", "jpeg", "png"])

if st.button("글 등록"):
    if title and content:
        img_path = None
        if img:
            img_path = f"uploads/{img.name}"
            with open(img_path, "wb") as f:
                f.write(img.getbuffer())

        c.execute(
            "INSERT INTO posts VALUES (NULL,?,?,?,?,?)",
            (title, content, img_path, 0, datetime.now().isoformat())
        )
        conn.commit()
        st.rerun()
    else:
        st.warning("제목과 내용을 입력해주세요")

# ================= POSTS =================
st.markdown("---")
posts = c.execute(
    "SELECT * FROM posts ORDER BY pinned DESC, created DESC"
).fetchall()

for p in posts:
    st.markdown(f"## {'📌 ' if p[4] else ''}{p[1]}")

    if p[3]:
        st.image(p[3])

    st.write(p[2])

    # ----- admin pin -----
    if st.session_state.admin:
        if st.button("📌 고정", key=f"pin_{p[0]}"):
            c.execute("UPDATE posts SET pinned=1 WHERE id=?", (p[0],))
            conn.commit()
            st.rerun()

    # ----- comments -----
    comments = c.execute(
        "SELECT * FROM comments WHERE post_id=? AND parent_id IS NULL",
        (p[0],)
    ).fetchall()

    for cm in comments:
        st.write(f"💬 **{cm[2]}**: {cm[3]}")

        # ----- admin reply -----
        if st.session_state.admin:
            reply = st.text_input(
                "관리자 대댓글",
                key=f"reply_{cm[0]}"
            )
            if st.button("답글 등록", key=f"reply_btn_{cm[0]}"):
                if reply:
                    c.execute(
                        "INSERT INTO comments VALUES (NULL,?,?,?,?,?)",
                        (p[0], st.session_state.admin[2], reply, 1, cm[0])
                    )
                    conn.commit()
                    st.rerun()

    # ----- user comment -----
    writer = st.text_input("닉네임", key=f"writer_{p[0]}")
    text = st.text_input("댓글 내용", key=f"text_{p[0]}")

    if st.button("댓글 작성", key=f"comment_btn_{p[0]}"):
        if writer and text:
            c.execute(
                "INSERT INTO comments VALUES (NULL,?,?,?,?,NULL)",
                (p[0], writer, text, 0)
            )
            conn.commit()
            st.rerun()
        else:
            st.warning("닉네임과 댓글을 입력해주세요")

    st.markdown("---")

