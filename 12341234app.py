import streamlit as st
import sqlite3, os
from datetime import datetime

st.set_page_config(page_title="rocade", layout="wide")

# ================= CSS =================
st.markdown("""
<style>
.chat-wrap { max-width: 900px; margin: auto; }

.bubble-right {
    background: #f1f1f1;
    padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    max-width: 70%;
    margin-left: auto;
    margin-bottom: 6px;
    word-break: break-word;
}

.bubble-left {
    background: #dbeafe;
    padding: 12px 16px;
    border-radius: 18px 18px 18px 4px;
    max-width: 70%;
    word-break: break-word;
}

.time {
    font-size: 11px;
    color: gray;
    margin-top: 2px;
}

.reply-row {
    display: flex;
    gap: 8px;
    margin: 8px 0;
}

.reply-row img {
    width: 38px;
    height: 38px;
    border-radius: 50%;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center;'>💬 rocade</h2>", unsafe_allow_html=True)

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

# ================= HEADER =================
top = st.columns([8,2])
with top[1]:
    if not st.session_state.admin:
        if st.button("Admin Login"):
            st.session_state.login = True
    else:
        st.image(st.session_state.admin[3], width=40)
        st.write(st.session_state.admin[2])
        if st.button("Logout"):
            st.session_state.admin = None
            st.rerun()

# ================= LOGIN =================
if st.session_state.get("login"):
    i = st.text_input("ID")
    p = st.text_input("PW", type="password")
    if st.button("Login"):
        c.execute("SELECT * FROM admin WHERE id=? AND pw=?", (i,p))
        a = c.fetchone()
        if a:
            st.session_state.admin = a
            st.session_state.login = False
            st.rerun()
        else:
            st.error("로그인 실패")

# ================= CHAT =================
st.markdown("<div class='chat-wrap'>", unsafe_allow_html=True)

messages = c.execute(
    "SELECT * FROM messages ORDER BY id ASC"
).fetchall()

for m in messages:
    st.markdown(
        f"""
        <div class="bubble-right">
            {m[1]}
            <div class="time">{m[3]}</div>
        </div>
        """, unsafe_allow_html=True
    )

    if m[2]:
        st.image(m[2], width=220)

    replies = c.execute(
        "SELECT * FROM replies WHERE message_id=?",
        (m[0],)
    ).fetchall()

    for r in replies:
        st.markdown(
            f"""
            <div class="reply-row">
                <img src="{r[6]}">
                <div class="bubble-left">
                    <b>{r[5]}</b><br>
                    {r[2]}
                    <div class="time">{r[3]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True
        )

    if st.session_state.admin:
        reply = st.text_input("답변", key=f"r_{m[0]}")
        if st.button("답변 전송", key=f"b_{m[0]}"):
            if reply:
                a = st.session_state.admin
                c.execute(
                    "INSERT INTO replies VALUES (NULL,?,?,?,?,?,?)",
                    (m[0], reply, datetime.now().strftime("%Y-%m-%d %H:%M"),
                     a[0], a[2], a[3])
                )
                conn.commit()
                st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ================= BOTTOM INPUT =================
st.markdown("---")
with st.form("send"):
    cols = st.columns([6,1,1])
    msg = cols[0].text_input("메시지", placeholder="질문을 입력하세요…", label_visibility="collapsed")
    img = cols[1].file_uploader("📷", label_visibility="collapsed", type=["png","jpg"])
    send = cols[2].form_submit_button("➤")

    if send and (msg or img):
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

