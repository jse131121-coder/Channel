import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Privcht", layout="centered")

# ================== STYLE ==================
st.markdown("""
<style>
body { background:#f7f7f7; }

.chat-wrap { overflow:auto; padding-bottom:100px; }

.bubble-right {
    display:inline-block;
    background:#ffffff;
    padding:12px 16px;
    border-radius:18px 18px 4px 18px;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
    max-width:70%;
    float:right;
    clear:both;
    margin:8px 0;
    word-break:break-word;
}

.bubble-left {
    display:inline-block;
    background:#ffffff;
    padding:12px 16px;
    border-radius:18px 18px 18px 4px;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
    max-width:70%;
    float:left;
    clear:both;
    margin:8px 0;
    word-break:break-word;
}

.admin-row {
    display:flex;
    align-items:flex-start;
    gap:8px;
}

.admin-img {
    width:34px;
    height:34px;
    border-radius:50%;
    object-fit:cover;
}

.time {
    font-size:11px;
    color:#999;
    margin-top:4px;
}
</style>
""", unsafe_allow_html=True)

# ================== DB ==================
conn = sqlite3.connect("privcht.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS admins (
    id TEXT PRIMARY KEY,
    pw TEXT,
    name TEXT,
    profile TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    image TEXT,
    time TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER,
    admin_id TEXT,
    content TEXT,
    time TEXT
)""")

conn.commit()

# ================== SESSION ==================
if "admin" not in st.session_state:
    st.session_state.admin = None

# ================== HEADER ==================
st.markdown("<h2 style='text-align:center'>💬 Privcht</h2>", unsafe_allow_html=True)

# ================== SIDEBAR (ADMIN) ==================
if st.session_state.admin:
    with st.sidebar:
        st.markdown("### 🎤 관리자")
        st.markdown(f"**{st.session_state.admin[2]}**")
        if st.button("Logout"):
            st.session_state.admin = None
            st.rerun()

else:
    with st.expander("🔐 Admin Login"):
        aid = st.text_input("ID")
        apw = st.text_input("PW", type="password")

        if st.button("Login"):
            admin = c.execute(
                "SELECT * FROM admins WHERE id=? AND pw=?",
                (aid, apw)
            ).fetchone()
            if admin:
                st.session_state.admin = admin
                st.rerun()
            else:
                st.error("로그인 실패")

        st.markdown("### ➕ 관리자 생성")
        nid = st.text_input("New ID")
        npw = st.text_input("New PW", type="password")
        name = st.text_input("Artist Name")
        profile = st.text_input("Profile Image URL (선택)")

        if st.button("Create Admin"):
            try:
                c.execute(
                    "INSERT INTO admins VALUES (?,?,?,?)",
                    (nid, npw, name, profile)
                )
                conn.commit()
                st.success("관리자 생성 완료")
            except:
                st.error("이미 존재하는 ID")

# ================== CHAT ==================
st.markdown("<div class='chat-wrap'>", unsafe_allow_html=True)

messages = c.execute("SELECT * FROM messages ORDER BY id").fetchall()

for m in messages:
    # USER MESSAGE
    st.markdown(f"""
    <div class="bubble-right">
        {m[1].replace("\\n","<br>")}
        <div class="time">{m[3]}</div>
    </div>
    """, unsafe_allow_html=True)

    if m[2]:
        st.image(m[2], width=200)

    # REPLIES
    replies = c.execute(
        "SELECT * FROM replies WHERE message_id=?",
        (m[0],)
    ).fetchall()

    for r in replies:
        admin = c.execute(
            "SELECT name, profile FROM admins WHERE id=?",
            (r[2],)
        ).fetchone()

        profile_img = admin[1] if admin[1] else "https://dummyimage.com/100x100/ddd/000&text=🎤"

        st.markdown(f"""
        <div class="bubble-left">
            <div class="admin-row">
                <img src="{profile_img}" class="admin-img">
                <div>
                    <b>{admin[0]} · ARTIST</b><br>
                    {r[3].replace("\\n","<br>")}
                    <div class="time">{r[4]}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ADMIN REPLY
    if st.session_state.admin:
        with st.expander("↩ 답변 / 관리"):
            reply = st.text_area("답변", key=f"r{m[0]}", height=100)
            if st.button("Send", key=f"s{m[0]}"):
                c.execute(
                    "INSERT INTO replies VALUES (NULL,?,?,?,?)",
                    (
                        m[0],
                        st.session_state.admin[0],
                        reply,
                        datetime.now().strftime("%Y-%m-%d %H:%M")
                    )
                )
                conn.commit()
                st.rerun()

            if st.button("❌ 질문 삭제", key=f"d{m[0]}"):
                c.execute("DELETE FROM messages WHERE id=?", (m[0],))
                c.execute("DELETE FROM replies WHERE message_id=?", (m[0],))
                conn.commit()
                st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ================== INPUT ==================
st.markdown("---")
with st.form("send"):
    msg = st.text_area("질문", placeholder="질문을 입력하세요…", height=60)
    img = st.text_input("이미지 URL (선택)")
    if st.form_submit_button("Send"):
        if msg.strip():
            c.execute(
                "INSERT INTO messages VALUES (NULL,?,?,?)",
                (msg, img, datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()
            st.rerun()




