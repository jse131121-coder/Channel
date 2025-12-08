import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Privcht", layout="centered")

# ================== STYLE ==================
st.markdown("""
<style>
body { background:#f7f7f7; }

.bubble-right {
    display: inline-block;
    background: white;
    padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    max-width: 70%;
    float: right;
    clear: both;
    margin: 8px 0;
    word-wrap: break-word;
}

.bubble-left {
    display: inline-block;
    background: white;
    padding: 12px 16px;
    border-radius: 18px 18px 18px 4px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    max-width: 70%;
    float: left;
    clear: both;
    margin: 8px 0;
    word-wrap: break-word;
}

.time {
    font-size: 11px;
    color: #999;
    margin-top: 4px;
}
</style>
""", unsafe_allow_html=True)

# ================== DB ==================
conn = sqlite3.connect("privcht.db", check_same_thread=False)
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
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    image TEXT,
    time TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER,
    admin_id TEXT,
    content TEXT,
    time TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS reactions (
    message_id INTEGER,
    emoji TEXT,
    count INTEGER,
    PRIMARY KEY(message_id, emoji)
)
""")

conn.commit()

# ================== SESSION ==================
if "admin" not in st.session_state:
    st.session_state.admin = None

# ================== HEADER ==================
st.markdown("<h2 style='text-align:center'>💬 Privcht</h2>", unsafe_allow_html=True)

# ================== LOGIN ==================
with st.expander("🔐 Admin Login"):
    aid = st.text_input("ID")
    apw = st.text_input("PW", type="password")
    if st.button("Login"):
        a = c.execute(
            "SELECT * FROM admins WHERE id=? AND pw=?",
            (aid, apw)
        ).fetchone()
        if a:
            st.session_state.admin = a
            st.success("로그인 성공")
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
st.markdown("---")

msgs = c.execute("SELECT * FROM messages ORDER BY id").fetchall()

for m in msgs:
    # USER MESSAGE
    st.markdown(f"""
    <div class="bubble-right">
        {m[1].replace("\\n","<br>")}
        <div class="time">{m[3]}</div>
    </div>
    """, unsafe_allow_html=True)

    if m[2]:
        st.image(m[2], width=200)

    # REACTIONS
    emojis = ["❤️","😂","😮","😢"]
    cols = st.columns(len(emojis))
    for i,e in enumerate(emojis):
        with cols[i]:
            r = c.execute(
                "SELECT count FROM reactions WHERE message_id=? AND emoji=?",
                (m[0],e)
            ).fetchone()
            cnt = r[0] if r else 0
            if st.button(f"{e} {cnt}", key=f"{m[0]}{e}"):
                if r:
                    c.execute(
                        "UPDATE reactions SET count=count+1 WHERE message_id=? AND emoji=?",
                        (m[0],e)
                    )
                else:
                    c.execute(
                        "INSERT INTO reactions VALUES (?,?,1)",
                        (m[0],e)
                    )
                conn.commit()
                st.rerun()

    # REPLIES
    replies = c.execute(
        "SELECT * FROM replies WHERE message_id=?",
        (m[0],)
    ).fetchall()

    for r in replies:
        admin = c.execute(
            "SELECT name FROM admins WHERE id=?",
            (r[2],)
        ).fetchone()

        st.markdown(f"""
        <div class="bubble-left">
            <b>🎤 {admin[0]}</b><br>
            {r[3].replace("\\n","<br>")}
            <div class="time">{r[4]}</div>
        </div>
        """, unsafe_allow_html=True)

    # ADMIN TOOLS
    if st.session_state.admin:
        with st.expander("↩ 답변 / 관리"):
            reply = st.text_area("답변", key=f"r{m[0]}", height=100)
            if st.button("Send", key=f"s{m[0]}"):
                c.execute(
                    "INSERT INTO replies VALUES (NULL,?,?,?,?)",
                    (m[0], st.session_state.admin[0],
                     reply, datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
                conn.commit()
                st.rerun()

            if st.button("❌ 질문 삭제", key=f"d{m[0]}"):
                c.execute("DELETE FROM messages WHERE id=?", (m[0],))
                c.execute("DELETE FROM replies WHERE message_id=?", (m[0],))
                conn.commit()
                st.rerun()

# ================== INPUT ==================
st.markdown("---")
with st.form("send"):
    msg = st.text_area(
        "질문",
        placeholder="질문을 입력하세요…",
        height=60
    )
    img = st.text_input("이미지 URL (선택)")
    if st.form_submit_button("Send"):
        if msg.strip():
            c.execute(
                "INSERT INTO messages VALUES (NULL,?,?,?)",
                (msg, img,
                 datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()
            st.rerun()



