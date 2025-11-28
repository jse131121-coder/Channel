import streamlit as st
from datetime import datetime
import sqlite3

st.set_page_config(page_title="Mini Chat Stable", layout="wide")

# ================= DB 연결 =================
def get_connection():
    conn = sqlite3.connect("chat.db", check_same_thread=False)
    return conn

conn = get_connection()
c = conn.cursor()

# ---------- 테이블 생성 ----------
c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nickname TEXT,
    message TEXT,
    likes INTEGER DEFAULT 0,
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
# 기본 테마
c.execute("INSERT OR IGNORE INTO chat_theme VALUES (1, '#FFFFFF', '#000000')")
conn.commit()

# ================= SESSION =================
if "nickname" not in st.session_state:
    st.session_state.nickname = ""

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if "new_msg" not in st.session_state:
    st.session_state.new_msg = ""

# ================= SIDEBAR =================
st.sidebar.title("💬 Mini Chat Login")

if not st.session_state.nickname:
    st.session_state.nickname = st.sidebar.text_input("닉네임 입력")
    if st.sidebar.button("입장"):
        if st.session_state.nickname.strip() == "":
            st.sidebar.error("닉네임을 입력하세요!")
        else:
            if st.session_state.nickname.lower() == "admin":
                st.session_state.admin_logged_in = True
            st.sidebar.success(f"{st.session_state.nickname}님 환영합니다!")
else:
    st.sidebar.info(f"닉네임: {st.session_state.nickname}")
    if st.sidebar.button("로그아웃"):
        st.session_state.nickname = ""
        st.session_state.admin_logged_in = False
        st.session_state.new_msg = ""
        st.experimental_rerun()

# ================= 채팅 테마 =================
theme = c.execute("SELECT bg_color, text_color FROM chat_theme WHERE id=1").fetchone()
if st.session_state.admin_logged_in:
    st.sidebar.markdown("### 🎨 채팅 테마")
    bg_color = st.sidebar.color_picker("배경색", theme[0])
    text_color = st.sidebar.color_picker("글자색", theme[1])
    if st.sidebar.button("테마 변경"):
        c.execute("UPDATE chat_theme SET bg_color=?, text_color=? WHERE id=1", (bg_color, text_color))
        conn.commit()
        st.experimental_rerun()

# ================= 채팅 =================
st.title("📱 Mini Chat Stable")

# 메시지 입력
if st.session_state.nickname:
    st.session_state.new_msg = st.text_input("메시지 입력", st.session_state.new_msg, key="message_input")
    if st.button("전송"):
        msg = st.session_state.new_msg.strip()
        if msg != "":
            c.execute(
                "INSERT INTO messages (nickname, message, likes, time) VALUES (?,?,0,?)",
                (st.session_state.nickname, msg, datetime.now().strftime("%H:%M"))
            )
            conn.commit()
            st.session_state.new_msg = ""  # 입력창 초기화
            st.experimental_rerun()

# ================= 메시지 표시 =================
st.markdown("---")
st.subheader("채팅 기록")

rows = c.execute("SELECT id, nickname, message, likes, time FROM messages ORDER BY id DESC LIMIT 50").fetchall()
for mid, n, m, likes, t in reversed(rows):
    st.markdown(
        f"<div style='background:{theme[0]};color:{theme[1]};padding:6px;border-radius:6px;margin:4px'>[{t}] <b>{n}</b>: {m}</div>",
        unsafe_allow_html=True
    )
    col1, _ = st.columns([1,4])
    if col1.button(f"❤️ {likes}", key=f"like_{mid}"):
        c.execute("UPDATE messages SET likes = likes + 1 WHERE id = ?", (mid,))
        conn.commit()
        st.experimental_rerun()

