import streamlit as st
import sqlite3
from datetime import datetime
import os
from uuid import uuid4

st.set_page_config(page_title="Privcht", layout="centered")

# ================== FILE DIR ==================
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_file(file):
    ext = file.name.split(".")[-1]
    fname = f"{uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, fname)
    with open(path, "wb") as f:
        f.write(file.getbuffer())
    return path

# ================== STYLE ==================
st.markdown("""
<style>
body { background:#f7f7f7; }

.bubble-right {
    background:white;
    padding:12px 16px;
    border-radius:18px 18px 4px 18px;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
    max-width:70%;
    margin-left:auto;
    margin-bottom:8px;
}

.bubble-left {
    background:white;
    padding:12px 16px;
    border-radius:18px 18px 18px 4px;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
    max-width:70%;
    margin-bottom:8px;
}

.time {
    font-size:11px;
    color:#999;
}

.admin-row {
    display:flex;
    gap:8px;
}

.admin-img {
    width:36px;
    height:36px;
    border-radius:50%;
    object-fit:cover;
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
    audio TEXT,
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

# ================== SIDEBAR ==================
if st.session_state.admin:
    with st.sidebar:
        st.markdown(f"### 🎤 {st.session_state.admin[2]}")
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
        pfile = st.file_uploader("프로필 사진", type=["png","jpg","jpeg"])

        if st.button("Create Admin"):
            try:
                path = save_file(pfile) if pfile else None
                c.execute(
                    "INSERT INTO admins VALUES (?,?,?,?)",
                    (nid, npw, name, path)
                )
                conn.commit()
                st.success("관리자 생성 완료")
            except:
                st.error("이미 존재하는 ID")

# ================== CHAT ==================
msgs = c.execute("SELECT * FROM messages ORDER BY id").fetchall()

for m in msgs:
    st.markdown(f"""
    <div class="bubble-right">
        {m[1].replace("\\n","<br>")}
        <div class="time">{m[4]}</div>
    </div>
    """, unsafe_allow_html=True)

    if m[2]:
        st.image(m[2], width=200)
    if m[3]:
        st.audio(m[3])

    replies = c.execute(
        "SELECT * FROM replies WHERE message_id=?",
        (m[0],)
    ).fetchall()

    for r in replies:
        admin = c.execute(
            "SELECT name, profile FROM admins WHERE id=?",
            (r[2],)
        ).fetchone()

        st.markdown(f"""
        <div class="bubble-left">
            <div class="admin-row">
                <img src="{admin[1] if admin[1] else 'https://dummyimage.com/100x100/ddd/000&text=🎤'}" class="admin-img">
                <div>
                    <b>{admin[0]} · ARTIST</b><br>
                    {r[3].replace("\\n","<br>")}
                    <div class="time">{r[4]}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.admin:
        with st.expander("↩ 답변"):
            reply = st.text_area("답변", key=f"r{m[0]}")
            if st.button("Send", key=f"s{m[0]}"):
                c.execute(
                    "INSERT INTO replies VALUES (NULL,?,?,?,?)",
                    (m[0], st.session_state.admin[0], reply,
                     datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
                conn.commit()
                st.rerun()

# ================== INPUT BAR ==================
st.markdown("---")
with st.form("send"):
    cols = st.columns([1,6,2])

    with cols[0]:
        plus = st.form_submit_button("➕")

    with cols[1]:
        msg = st.text_area("메시지", height=50, placeholder="메시지를 입력하세요…")

    with cols[2]:
        send = st.form_submit_button("Send")

    if plus:
        with st.expander("첨부"):
            img = st.file_uploader("📷 이미지", type=["png","jpg","jpeg"])
            audio = st.file_uploader("🎤 음성", type=["mp3","wav","m4a"])
    else:
        img = None
        audio = None

    if send and msg.strip():
        img_path = save_file(img) if img else None
        audio_path = save_file(audio) if audio else None
        c.execute(
            "INSERT INTO messages VALUES (NULL,?,?,?,?)",
            (
                msg,
                img_path,
                audio_path,
                datetime.now().strftime("%Y-%m-%d %H:%M")
            )
        )
        conn.commit()
        st.rerun()





