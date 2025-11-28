import streamlit as st
import sqlite3
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ==================================================
# 기본 설정
# ==================================================
st.set_page_config(page_title="My Channel", layout="wide")

# ==================================================
# DB 연결
# ==================================================
conn = sqlite3.connect("channel.db", check_same_thread=False)
c = conn.cursor()

# ==================================================
# 테이블 생성
# ==================================================
c.execute("""
CREATE TABLE IF NOT EXISTS profile (
    username TEXT PRIMARY KEY,
    bio TEXT,
    profile_url TEXT,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS feed_admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    writer TEXT,
    time TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS feed_fan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    writer TEXT,
    time TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS chat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nickname TEXT,
    message TEXT,
    time TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS chat_theme (
    id INTEGER PRIMARY KEY,
    bg TEXT,
    text TEXT
)
""")
conn.commit()

# ==================================================
# 기본 값
# ==================================================
if not c.execute("SELECT * FROM profile WHERE username='admin'").fetchone():
    c.execute(
        "INSERT INTO profile VALUES (?,?,?,?)",
        ("admin", "안녕하세요! 관리자입니다.", "", "1234")
    )

if not c.execute("SELECT * FROM chat_theme WHERE id=1").fetchone():
    c.execute("INSERT INTO chat_theme VALUES (1,'#ffffff','#000000')")

conn.commit()

# ==================================================
# 세션
# ==================================================
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "nickname" not in st.session_state:
    st.session_state.nickname = ""

# ==================================================
# 사이드바 로그인
# ==================================================
st.sidebar.subheader("🔐 관리자 로그인")

if not st.session_state.admin_logged_in:
    u = st.sidebar.text_input("아이디")
    p = st.sidebar.text_input("비밀번호", type="password")
    if st.sidebar.button("로그인"):
        if c.execute(
            "SELECT * FROM profile WHERE username=? AND password=?",
            (u, p)
        ).fetchone():
            st.session_state.admin_logged_in = True
            st.sidebar.success("로그인 성공")
            st.rerun()
        else:
            st.sidebar.error("로그인 실패")
else:
    st.sidebar.success("관리자 로그인됨 ✅")
    if st.sidebar.button("로그아웃"):
        st.session_state.admin_logged_in = False
        st.rerun()

# ==================================================
# 탭
# ==================================================
tab_profile, tab_home, tab_admin, tab_fan, tab_chat = st.tabs(
    ["👤 프로필", "🏠 홈", "📝 관리자 피드", "📝 팬 피드", "💬 채팅"]
)

# ==================================================
# 프로필
# ==================================================
with tab_profile:
    prof = c.execute("SELECT * FROM profile WHERE username='admin'").fetchone()
    st.subheader("👤 관리자 프로필")
    st.write(prof[1])

    if st.session_state.admin_logged_in:
        bio = st.text_area("자기소개 수정", prof[1])
        if st.button("저장"):
            c.execute("UPDATE profile SET bio=? WHERE username='admin'", (bio,))
            conn.commit()
            st.success("저장됨")
            st.rerun()

# ==================================================
# 홈
# ==================================================
with tab_home:
    st.subheader("🏠 링크 모음")
    st.markdown("""
- 유튜브  
- 인스타그램  
- 팬카페  
""")

# ==================================================
# 관리자 피드
# ==================================================
with tab_admin:
    st.subheader("📝 관리자 피드")

    for ctt, w, t in c.execute(
        "SELECT content, writer, time FROM feed_admin ORDER BY id DESC"
    ):
        st.markdown(f"**{w} · {t}**")
        st.write(ctt)
        st.divider()

    if st.session_state.admin_logged_in:
        content = st.text_area("관리자 글 작성")
        if st.button("게시"):
            c.execute(
                "INSERT INTO feed_admin VALUES (NULL,?,?,?)",
                (content, "admin", datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()
            st.rerun()

# ==================================================
# 팬 피드
# ==================================================
with tab_fan:
    st.subheader("📝 팬 피드")

    for ctt, w, t in c.execute(
        "SELECT content, writer, time FROM feed_fan ORDER BY id DESC"
    ):
        st.markdown(f"**{w} · {t}**")
        st.write(ctt)
        st.divider()

    name = st.text_input("이름")
    content = st.text_area("글 내용")
    if st.button("게시"):
        if name and content:
            c.execute(
                "INSERT INTO feed_fan VALUES (NULL,?,?,?)",
                (content, name, datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()
            st.rerun()

# ==================================================
# 💬 카톡 채팅
# ==================================================
with tab_chat:
    st_autorefresh(interval=1500, key="chat")

    theme = c.execute("SELECT bg, text FROM chat_theme WHERE id=1").fetchone()
    bg, text = theme

    if not st.session_state.nickname:
        nick = st.text_input("닉네임")
        if st.button("입장"):
            st.session_state.nickname = nick
            st.rerun()
        st.stop()

    st.markdown("""
    <style>
    .left {background:#f1f1f1;padding:8px;border-radius:10px;max-width:60%;}
    .right {background:#ffe812;padding:8px;border-radius:10px;max-width:60%;margin-left:auto;}
    </style>
    """, unsafe_allow_html=True)

    for n, m, t in c.execute(
        "SELECT nickname,message,time FROM chat ORDER BY id"
    ):
        if n == st.session_state.nickname:
            st.markdown(f"<div class='right'>{m}<br><small>{t}</small></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='left'><b>{n}</b><br>{m}<br><small>{t}</small></div>", unsafe_allow_html=True)

    msg = st.text_input("메시지")
    if st.button("전송"):
        c.execute(
            "INSERT INTO chat VALUES (NULL,?,?,?)",
            (st.session_state.nickname, msg, datetime.now().strftime("%H:%M"))
        )
        conn.commit()
        st.rerun()

    if st.session_state.admin_logged_in:
        st.subheader("🎨 채팅 테마")
        new_bg = st.color_picker("배경", bg)
        new_txt = st.color_picker("글자", text)
        if st.button("테마 적용"):
            c.execute("UPDATE chat_theme SET bg=?, text=? WHERE id=1", (new_bg, new_txt))
            conn.commit()
            st.success("적용 완료")



