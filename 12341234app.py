# app.py
import streamlit as st
import sqlite3
import os
from datetime import datetime
from uuid import uuid4

# ---------- config ----------
st.set_page_config(page_title="Privcht", layout="centered")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- helpers ----------
def save_file(uploaded_file):
    if uploaded_file is None:
        return None
    ext = uploaded_file.name.split(".")[-1]
    fname = f"{uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, fname)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

def safe_get_tuple(tpl, idx, default=None):
    try:
        return tpl[idx]
    except Exception:
        return default

# ---------- DB setup ----------
conn = sqlite3.connect("privcht.db", check_same_thread=False)
c = conn.cursor()

# messages: id, content, image, audio, time
c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    image TEXT,
    audio TEXT,
    time TEXT
)
""")

# replies: id, message_id, admin_id, content, time
c.execute("""
CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER,
    admin_id TEXT,
    content TEXT,
    time TEXT
)
""")

# admins: id, pw, name, profile
c.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id TEXT PRIMARY KEY,
    pw TEXT,
    name TEXT,
    profile TEXT
)
""")

conn.commit()

# ---------- ensure initial admin (optional convenience) ----------
c.execute("INSERT OR IGNORE INTO admins VALUES (?,?,?,?)", ("admin", "1234", "Master", None))
conn.commit()

# ---------- session ----------
if "admin" not in st.session_state:
    st.session_state.admin = None
if "show_attach" not in st.session_state:
    st.session_state.show_attach = False

# ---------- styles ----------
st.markdown("""
<style>
body { background:#f7f7f7; }
.container { max-width:900px; margin:auto; padding-bottom:140px; }
.bubble-right {
    background:white;
    padding:12px 16px;
    border-radius:18px 18px 4px 18px;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
    max-width:70%;
    margin-left:auto;
    margin-bottom:8px;
    word-break:break-word;
}
.bubble-left {
    background:white;
    padding:12px 16px;
    border-radius:18px 18px 18px 4px;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
    max-width:70%;
    margin-bottom:8px;
    word-break:break-word;
}
.admin-row { display:flex; gap:8px; align-items:flex-start; }
.admin-img { width:36px; height:36px; border-radius:50%; object-fit:cover; }
.time { font-size:11px; color:#999; margin-top:6px; }
.bottom-bar { position: fixed; bottom:0; left:0; width:100%; background:white; padding:10px; border-top:1px solid #eee; }
.reaction-btn { background:#fff; border:1px solid #eee; border-radius:16px; padding:4px 8px; cursor:pointer; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='container'>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center'>💬 Privcht</h2>", unsafe_allow_html=True)

# ---------- sidebar / admin login ----------
if st.session_state.admin:
    with st.sidebar:
        st.markdown("### 🎤 관리자 계정")
        st.image(safe_get_tuple(st.session_state.admin, 3, None) or "https://dummyimage.com/100x100/ddd/000&text=🎤", width=80)
        st.markdown(f"**{safe_get_tuple(st.session_state.admin,2,'Admin')}**")
        if st.button("Logout"):
            st.session_state.admin = None
            st.experimental_rerun()
        st.markdown("---")
        st.markdown("➕ 관리자 추가")
        with st.form("create_admin_sidebar"):
            new_id = st.text_input("ID", key="new_admin_id")
            new_pw = st.text_input("PW", type="password", key="new_admin_pw")
            new_name = st.text_input("Name", key="new_admin_name")
            new_profile_file = st.file_uploader("Profile image (optional)", type=["png","jpg","jpeg"], key="new_admin_profile")
            if st.form_submit_button("Create admin"):
                if not (new_id and new_pw and new_name):
                    st.warning("ID, PW, Name 모두 입력하세요.")
                else:
                    ppath = save_file(new_profile_file) if new_profile_file else None
                    try:
                        c.execute("INSERT INTO admins VALUES (?,?,?,?)", (new_id, new_pw, new_name, ppath))
                        conn.commit()
                        st.success("관리자 생성 완료")
                    except sqlite3.IntegrityError:
                        st.error("이미 존재하는 ID")
else:
    with st.expander("🔐 Admin Login / Create"):
        with st.form("login_form"):
            aid = st.text_input("ID", key="login_id")
            apw = st.text_input("PW", type="password", key="login_pw")
            if st.form_submit_button("Login"):
                admin = c.execute("SELECT * FROM admins WHERE id=? AND pw=?", (aid, apw)).fetchone()
                if admin:
                    st.session_state.admin = admin
                    st.success("로그인 성공")
                    st.experimental_rerun()
                else:
                    st.error("로그인 실패")
        st.markdown("---")
        st.subheader("관리자 생성")
        with st.form("create_admin"):
            nid = st.text_input("New ID", key="nid")
            npw = st.text_input("New PW", type="password", key="npw")
            nname = st.text_input("Name", key="nname")
            nprofile = st.file_uploader("Profile image (optional)", type=["png","jpg","jpeg"], key="nprofile")
            if st.form_submit_button("Create"):
                if not (nid and npw and nname):
                    st.warning("모두 입력하세요.")
                else:
                    p = save_file(nprofile) if nprofile else None
                    try:
                        c.execute("INSERT INTO admins VALUES (?,?,?,?)", (nid, npw, nname, p))
                        conn.commit()
                        st.success("관리자 생성 완료")
                    except sqlite3.IntegrityError:
                        st.error("이미 존재하는 ID")

# ---------- reactions helper ----------
def get_reaction_count(message_id, emoji):
    r = c.execute("SELECT count FROM reactions WHERE message_id=? AND emoji=?", (message_id, emoji)).fetchone()
    return r[0] if r else 0

def inc_reaction(message_id, emoji):
    r = c.execute("SELECT count FROM reactions WHERE message_id=? AND emoji=?", (message_id, emoji)).fetchone()
    if r:
        c.execute("UPDATE reactions SET count=count+1 WHERE message_id=? AND emoji=?", (message_id, emoji))
    else:
        c.execute("INSERT OR REPLACE INTO reactions VALUES (?,?,?)", (message_id, emoji, 1))
    conn.commit()

# ensure reactions table exists (safe)
c.execute("""
CREATE TABLE IF NOT EXISTS reactions (
    message_id INTEGER,
    emoji TEXT,
    count INTEGER,
    PRIMARY KEY(message_id, emoji)
)
""")
conn.commit()

# ---------- fetch messages safely ----------
msgs = c.execute("SELECT * FROM messages ORDER BY id").fetchall()

# show messages
for m in msgs:
    # robust unpack with defaults
    mid = safe_get_tuple(m, 0)
    content = safe_get_tuple(m, 1, "") or ""
    image = safe_get_tuple(m, 2, None)
    audio = safe_get_tuple(m, 3, None)
    time = safe_get_tuple(m, 4, "") or ""

    # user message (right bubble)
    st.markdown(f"""
    <div class="bubble-right">
      {content.replace('\\n','<br>')}
      <div class="time">{time}</div>
    </div>
    """, unsafe_allow_html=True)

    if image:
        try:
            st.image(image, width=240)
        except Exception:
            st.write("(이미지 로드 실패)")

    if audio:
        try:
            st.audio(audio)
        except Exception:
            st.write("(오디오 로드 실패)")

    # reactions (simple)
    emojis = ["❤️", "😂", "😮", "😢", "👍"]
    cols = st.columns(len(emojis))
    for i, e in enumerate(emojis):
        with cols[i]:
            cnt = get_reaction_count(mid, e)
            if st.button(f"{e} {cnt}", key=f"react_{mid}_{e}"):
                inc_reaction(mid, e)
                st.experimental_rerun()

    # replies (left bubbles)
    replies = c.execute("SELECT * FROM replies WHERE message_id=? ORDER BY id", (mid,)).fetchall()
    for r in replies:
        rid = safe_get_tuple(r, 0)
        r_message_id = safe_get_tuple(r, 1)
        r_admin_id = safe_get_tuple(r, 2)
        r_content = safe_get_tuple(r, 3, "") or ""
        r_time = safe_get_tuple(r, 4, "") or ""

        admin_info = c.execute("SELECT name, profile FROM admins WHERE id=?", (r_admin_id,)).fetchone()
        admin_name = safe_get_tuple(admin_info, 0, "Artist")
        admin_profile = safe_get_tuple(admin_info, 1, None) or "https://dummyimage.com/100x100/ddd/000&text=🎤"

        # reply bubble with admin image + content
        st.markdown(f"""
        <div class="bubble-left">
          <div class="admin-row">
            <img src="{admin_profile}" class="admin-img">
            <div>
              <b>{admin_name} · ARTIST</b><br>
              {r_content.replace('\\n','<br>')}
              <div class="time">{r_time}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # admin controls for replies: edit / delete (only visible to logged-in admins)
        if st.session_state.admin:
            # show edit/delete inside an expander to avoid clutter
            with st.expander("✏️ Edit / Delete Reply", expanded=False):
                # edit form
                new_text = st.text_area("Edit reply", value=r_content, key=f"edit_{rid}")
                if st.button("Save Edit", key=f"save_{rid}"):
                    if new_text.strip():
                        c.execute("UPDATE replies SET content=?, time=? WHERE id=?", (new_text, datetime.now().strftime("%Y-%m-%d %H:%M"), rid))
                        conn.commit()
                        st.success("답변 수정완료")
                        st.experimental_rerun()
                    else:
                        st.warning("내용을 입력하세요.")
                if st.button("Delete Reply", key=f"delreply_{rid}"):
                    c.execute("DELETE FROM replies WHERE id=?", (rid,))
                    conn.commit()
                    st.success("답변 삭제됨")
                    st.experimental_rerun()

    # admin actions for each message
    if st.session_state.admin:
        with st.expander("↩ 답변 / 관리", expanded=False):
            reply_txt = st.text_area("답변", key=f"replybox_{mid}")
            if st.button("Send Reply", key=f"sendreply_{mid}"):
                if reply_txt.strip():
                    admin_id = st.session_state.admin[0]
                    c.execute("INSERT INTO replies (message_id, admin_id, content, time) VALUES (?,?,?,?)",
                              (mid, admin_id, reply_txt, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    st.experimental_rerun()
                else:
                    st.warning("답변을 입력하세요.")
            # message delete
            if st.button("❌ Delete Message", key=f"deletemsg_{mid}"):
                # delete message and its replies
                c.execute("DELETE FROM messages WHERE id=?", (mid,))
                c.execute("DELETE FROM replies WHERE message_id=?", (mid,))
                conn.commit()
                st.experimental_rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ---------- bottom input bar ----------
st.markdown("<div class='bottom-bar'>", unsafe_allow_html=True)
with st.form("send_form", clear_on_submit=True):
    cols = st.columns([0.7, 7, 1.2])
    with cols[0]:
        # toggle attach: use a checkbox/button to show attach inputs
        attach = st.form_submit_button("➕", key="attach_btn")
    with cols[1]:
        txt = st.text_area("msg", placeholder="메시지를 입력하세요… (엔터로 줄바꿈)", height=60, label_visibility="collapsed")
    with cols[2]:
        send = st.form_submit_button("Send", key="send_btn")

    # handle attachments UI: if attach button was pressed, show new small form below
    if attach:
        st.info("첨부: 이미지 / 음성 업로드")
        a_img = st.file_uploader("이미지 업로드 (선택)", type=["png","jpg","jpeg"], key="attach_img")
        a_audio = st.file_uploader("음성 업로드 (선택)", type=["mp3","wav","m4a"], key="attach_audio")
        # persist these files in session to be used when Send is clicked
        st.session_state._attach_img = a_img
        st.session_state._attach_audio = a_audio

    else:
        # if not pressed, keep previous attachments if any (user may have attached then sent)
        a_img = st.session_state.get("_attach_img", None)
        a_audio = st.session_state.get("_attach_audio", None)

    # when send clicked
    if send:
        if not txt.strip() and not a_img and not a_audio:
            st.warning("메시지 또는 첨부파일을 입력하세요.")
        else:
            img_path = save_file(a_img) if a_img else None
            audio_path = save_file(a_audio) if a_audio else None
            c.execute("INSERT INTO messages (content, image, audio, time) VALUES (?,?,?,?)",
                      (txt, img_path, audio_path, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            # clear attachments from session
            if "_attach_img" in st.session_state: st.session_state.pop("_attach_img")
            if "_attach_audio" in st.session_state: st.session_state.pop("_attach_audio")
            st.experimental_rerun()

st.markdown("</div>", unsafe_allow_html=True)

     




