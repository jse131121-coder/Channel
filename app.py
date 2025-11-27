import streamlit as st
from datetime import datetime
import sqlite3

st.set_page_config(page_title="My Channel", layout="wide")

# ================= DB =================
conn = sqlite3.connect("channel.db", check_same_thread=False)
c = conn.cursor()

# ---------- tables ----------
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
    image_url TEXT,
    likes INTEGER DEFAULT 0,
    writer TEXT,
    time TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS feed_fan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    image_url TEXT,
    likes INTEGER DEFAULT 0,
    writer TEXT,
    time TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_type TEXT,
    feed_id INTEGER,
    nickname TEXT,
    comment TEXT,
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
    bg_color TEXT,
    text_color TEXT
)
""")
conn.commit()

# ---------- default admin ----------
c.execute("SELECT * FROM profile WHERE username='admin'")
if not c.fetchone():
    c.execute(
        "INSERT INTO profile VALUES (?,?,?,?)",
        ("admin", "안녕하세요! 관리자입니다.", "https://via.placeholder.com/150", "1234")
    )

c.execute("SELECT * FROM chat_theme WHERE id=1")
if not c.fetchone():
    c.execute("INSERT INTO chat_theme VALUES (1,'#FFFFFF','#000000')")
conn.commit()

# ================= SESSION =================
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# ================= SIDEBAR =================
st.sidebar.subheader("🔐 관리자 로그인")

if not st.session_state.admin_logged_in:
    uid = st.sidebar.text_input("아이디")
    upw = st.sidebar.text_input("비밀번호", type="password")
    if st.sidebar.button("로그인"):
        c.execute(
            "SELECT * FROM profile WHERE username=? AND password=?",
            (uid, upw)
        )
        if c.fetchone():
            st.session_state.admin_logged_in = True
            st.sidebar.success("로그인 성공")
            st.rerun()
        else:
            st.sidebar.error("실패")
else:
    st.sidebar.success("관리자 로그인 중")
    if st.sidebar.button("로그아웃"):
        st.session_state.admin_logged_in = False
        st.rerun()

# ================= TABS =================
tab_profile, tab_home, tab_admin, tab_fan, tab_chat = st.tabs(
    ["👤 소개", "🏠 홈", "📝 관리자 피드", "📝 친구들 피드", "💬 채팅"]
)

# ================= PROFILE =================
with tab_profile:
    profile = c.execute("SELECT * FROM profile WHERE username='admin'").fetchone()
    st.image(profile[2], width=150)
    st.markdown(f"### {profile[0]}")
    st.write(profile[1])

    if st.session_state.admin_logged_in:
        st.markdown("---")
        bio = st.text_area("소개", profile[1])
        img = st.text_input("프로필 이미지 URL", profile[2])
        if st.button("프로필 저장"):
            c.execute(
                "UPDATE profile SET bio=?, profile_url=? WHERE username='admin'",
                (bio, img)
            )
            conn.commit()
            st.rerun()

# ================= HOME =================
with tab_home:
    st.markdown("""
- 🔗 유튜브  
- 🔗 인스타그램  
- 🔗 팬카페
    """)

# ================= ADMIN FEED =================
with tab_admin:
    st.subheader("📌 관리자 피드")

    rows = c.execute("SELECT * FROM feed_admin ORDER BY id DESC").fetchall()

    for fid, content, img, likes, writer, tm in rows:
        st.markdown(f"**{writer} · {tm}**")
        st.write(content)
        if img:
            st.image(img, width=300)

        col1, col2 = st.columns([1,4])
        if col1.button(f"❤️ {likes}", key=f"admin_like_{fid}"):
            c.execute("UPDATE feed_admin SET likes=likes+1 WHERE id=?", (fid,))
            conn.commit()
            st.rerun()

        comments = c.execute(
            "SELECT nickname, comment FROM comments WHERE feed_type='admin' AND feed_id=?",
            (fid,)
        ).fetchall()

        for n, cm in comments:
            st.write(f"💬 **{n}**: {cm}")

        nick = st.text_input("닉네임", key=f"an_{fid}")
        cm = st.text_input("댓글", key=f"ac_{fid}")
        if st.button("댓글 등록", key=f"ab_{fid}"):
            if nick and cm:
                c.execute(
                    "INSERT INTO comments VALUES (NULL,'admin',?,?,?,?)",
                    (fid, nick, cm, datetime.now().strftime("%H:%M"))
                )
                conn.commit()
                st.rerun()

        st.divider()

    if st.session_state.admin_logged_in:
        st.markdown("### ➕ 게시글 추가")
        text = st.text_area("내용")
        img = st.text_input("이미지 URL (선택)")
        if st.button("게시"):
            c.execute(
                "INSERT INTO feed_admin VALUES (NULL,?,?,0,'admin',?)",
                (text, img, datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()
            st.rerun()

# ================= FAN FEED =================
with tab_fan:
    st.subheader("🫶 친구들 피드")

    rows = c.execute("SELECT * FROM feed_fan ORDER BY id DESC").fetchall()

    for fid, content, img, likes, writer, tm in rows:
        st.markdown(f"**{writer} · {tm}**")
        st.write(content)
        if img:
            st.image(img, width=300)

        if st.button(f"❤️ {likes}", key=f"fan_like_{fid}"):
            c.execute("UPDATE feed_fan SET likes=likes+1 WHERE id=?", (fid,))
            conn.commit()
            st.rerun()

        comments = c.execute(
            "SELECT nickname, comment FROM comments WHERE feed_type='fan' AND feed_id=?",
            (fid,)
        ).fetchall()

        for n, cm in comments:
            st.write(f"💬 **{n}**: {cm}")

        nick = st.text_input("닉네임", key=f"fn_{fid}")
        cm = st.text_input("댓글", key=f"fc_{fid}")
        if st.button("댓글 등록", key=f"fb_{fid}"):
            if nick and cm:
                c.execute(
                    "INSERT INTO comments VALUES (NULL,'fan',?,?,?,?)",
                    (fid, nick, cm, datetime.now().strftime("%H:%M"))
                )
                conn.commit()
                st.rerun()

        st.divider()

    st.markdown("### ✍ 팬 게시글 작성")
    writer = st.text_input("이름")
    text = st.text_area("내용")
    img = st.text_input("이미지 URL")
    if st.button("게시"):
        if writer and text:
            c.execute(
                "INSERT INTO feed_fan VALUES (NULL,?,?,0,?,?)",
                (text, img, writer, datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()
            st.rerun()

# ================= CHAT =================
with tab_chat:
    theme = c.execute("SELECT bg_color, text_color FROM chat_theme WHERE id=1").fetchone()

    rows = c.execute("SELECT nickname,message,time FROM chat ORDER BY id DESC LIMIT 50").fetchall()
    for n, m, t in rows[::-1]:
        st.markdown(
            f"<div style='background:{theme[0]};color:{theme[1]};padding:6px;border-radius:6px;margin:4px'>[{t}] <b>{n}</b>: {m}</div>",
            unsafe_allow_html=True
        )

    nick = st.text_input("닉네임")
    msg = st.text_input("메시지")
    if st.button("전송"):
        if nick and msg:
            c.execute(
                "INSERT INTO chat VALUES (NULL,?,?,?)",
                (nick, msg, datetime.now().strftime("%H:%M"))
            )
            conn.commit()
            st.rerun()

    if st.session_state.admin_logged_in:
        st.markdown("### 🎨 채팅 테마")
        bg = st.color_picker("배경", theme[0])
        tc = st.color_picker("글자", theme[1])
        if st.button("테마 변경"):
            c.execute(
                "UPDATE chat_theme SET bg_color=?, text_color=? WHERE id=1",
                (bg, tc)
            )
            conn.commit()
            st.rerun()

