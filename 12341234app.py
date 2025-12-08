import streamlit as st
import sqlite3, os
from datetime import datetime

# ================= PAGE =================
st.set_page_config(page_title="Privcht", layout="wide")

# ================= CSS =================
st.markdown("""
<style>
body { background:#f6f6f6; }

.chat-wrap {
  max-width: 900px;
  margin: auto;
  padding-bottom: 140px;
}

/* ===== 말풍선 (질문 / 오른쪽) ===== */
.bubble-right {
  position: relative;
  background: #ffffff;
  border-radius: 20px;
  padding: 14px 18px;
  max-width: 70%;
  margin-left: auto;
  margin-bottom: 6px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.07);
}
.bubble-right:after {
  content: "";
  position: absolute;
  right: -8px;
  top: 18px;
  width: 16px;
  height: 16px;
  background: white;
  clip-path: polygon(0 0, 100% 50%, 0 100%);
}

/* ===== 말풍선 (답변 / 왼쪽) ===== */
.bubble-left {
  position: relative;
  background: #dbeafe;
  border-radius: 20px;
  padding: 14px 18px;
  max-width: 70%;
  box-shadow: 0 2px 6px rgba(0,0,0,0.07);
}
.bubble-left:after {
  content: "";
  position: absolute;
  left: -8px;
  top: 18px;
  width: 16px;
  height: 16px;
  background: #dbeafe;
  clip-path: polygon(100% 0, 0 50%, 100% 100%);
}

.time {
  font-size: 11px;
  color: #777;
  margin-top: 4px;
}

/* ===== reply row ===== */
.reply-row {
  display: flex;
  gap: 8px;
  margin: 8px 0;
  align-items: flex-start;
}
.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
}

/* ===== reactions ===== */
.reactions button {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 20px;
  padding: 2px 8px;
  margin-right: 4px;
  cursor: pointer;
}

/* ===== bottom input ===== */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  background: white;
  padding: 10px;
  border-top: 1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center;'>💬 Privcht</h2>", unsafe_allow_html=True)

# ================= DB =================
conn = sqlite3.connect("privcht.db", check_same_thread=False)
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

c.execute("""
CREATE TABLE IF NOT EXISTS reactions (
  message_id INTEGER,
  emoji TEXT,
  count INTEGER,
  PRIMARY KEY (message_id, emoji)
)
""")

conn.commit()
os.makedirs("uploads", exist_ok=True)

# 기본 관리자 (초기용)
c.execute("""
INSERT OR IGNORE INTO admin VALUES ('admin','1234','Master',NULL)
""")
conn.commit()

# ================= SESSION =================
if "admin" not in st.session_state:
  st.session_state.admin = None
if "login" not in st.session_state:
  st.session_state.login = False

# ================= HEADER =================
top = st.columns([8,2])
with top[1]:
  if st.session_state.admin:
    st.write(f"👑 {st.session_state.admin[2]}")
    if st.button("Logout"):
      st.session_state.admin = None
      st.rerun()
  else:
    if st.button("Admin Login"):
      st.session_state.login = True

# ================= LOGIN =================
if st.session_state.login:
  i = st.text_input("ID")
  p = st.text_input("PW", type="password")
  if st.button("Login"):
    a = c.execute(
      "SELECT * FROM admin WHERE id=? AND pw=?", (i,p)
    ).fetchone()
    if a:
      st.session_state.admin = a
      st.session_state.login = False
      st.rerun()
    else:
      st.error("로그인 실패")

# ================= 관리자 생성 =================
if st.session_state.admin:
  with st.expander("➕ 관리자 생성"):
    ni = st.text_input("ID")
    np = st.text_input("PW", type="password")
    nn = st.text_input("이름")
    img = st.file_uploader("프로필 사진", type=["jpg","png"])

    if st.button("생성"):
      try:
        path = None
        if img:
          path = f"uploads/{img.name}"
          with open(path,"wb") as f:
            f.write(img.getbuffer())
        c.execute("INSERT INTO admin VALUES (?,?,?,?)",
                  (ni,np,nn,path))
        conn.commit()
        st.success("관리자 생성 완료")
      except:
        st.error("이미 존재하는 관리자")

# ================= CHAT =================
st.markdown("<div class='chat-wrap'>", unsafe_allow_html=True)

msgs = c.execute(
  "SELECT * FROM messages ORDER BY id ASC"
).fetchall()

for m in msgs:
  st.markdown(f"""
  <div class="bubble-right">
    {m[1]}
    <div class="time">{m[3]}</div>
  </div>
  """, unsafe_allow_html=True)

  if m[2]:
    st.image(m[2], width=220)

  # reactions
  emojis = ["❤️","😂","😮","😢","👍"]
  cols = st.columns(len(emojis))
  for i,e in enumerate(emojis):
    r = c.execute(
      "SELECT count FROM reactions WHERE message_id=? AND emoji=?",
      (m[0],e)).fetchone()
    cnt = r[0] if r else 0
    if cols[i].button(f"{e} {cnt}", key=f"{m[0]}_{e}"):
      if r:
        c.execute(
          "UPDATE reactions SET count=count+1 WHERE message_id=? AND emoji=?",
          (m[0],e))
      else:
        c.execute(
          "INSERT INTO reactions VALUES (?,?,1)",
          (m[0],e))
      conn.commit()
      st.rerun()

  replies = c.execute(
    "SELECT * FROM replies WHERE message_id=?",
    (m[0],)
  ).fetchall()

  for r in replies:
    st.markdown(f"""
    <div class="reply-row">
      <img class="avatar" src="{r[6] or ''}">
      <div class="bubble-left">
        <b>{r[5]}</b><br>
        {r[2]}
        <div class="time">{r[3]}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

  if st.session_state.admin:
    reply = st.text_input("답변", key=f"r{m[0]}")
    if st.button("전송", key=f"b{m[0]}"):
      a = st.session_state.admin
      c.execute("""
        INSERT INTO replies VALUES (NULL,?,?,?,?,?,?)
      """,(m[0],reply,datetime.now().strftime("%Y-%m-%d %H:%M"),
           a[0],a[2],a[3]))
      conn.commit()
      st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ================= BOTTOM INPUT =================
st.markdown("<div class='bottom-bar'>", unsafe_allow_html=True)
with st.form("send", clear_on_submit=True):
  c1,c2,c3 = st.columns([6,1,1])
  msg = c1.text_input(
    "msg",
    placeholder="메시지를 입력하세요…",
    label_visibility="collapsed"
  )
  img = c2.file_uploader(
    "📷",
    type=["jpg","png"],
    label_visibility="collapsed"
  )
  send = c3.form_submit_button("➤")

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

st.markdown("</div>", unsafe_allow_html=True)


