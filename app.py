# app.py
import streamlit as st
import sqlite3
import pathlib
from datetime import datetime
import time
import traceback

st.set_page_config(page_title="My Channel - Chat Ready", layout="wide")

# ---------------------------
# DB 안전 연결 / 초기화
# ---------------------------
DB_PATH = str(pathlib.Path("channel.db").resolve())

def init_conn(path):
    conn = sqlite3.connect(path, check_same_thread=False, timeout=30)
    cur = conn.cursor()
    # use WAL for concurrency stability
    try:
        cur.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    return conn, cur

def create_tables(cur):
    # profile
    cur.execute("""
    CREATE TABLE IF NOT EXISTS profile (
        username TEXT PRIMARY KEY,
        bio TEXT,
        profile_url TEXT,
        password TEXT
    )
    """)
    # admin & fan feeds
    cur.execute("""
    CREATE TABLE IF NOT EXISTS feed_admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        image_b64 TEXT,
        likes INTEGER DEFAULT 0,
        writer TEXT,
        time TEXT,
        pinned INTEGER DEFAULT 0
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS feed_fan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        image_b64 TEXT,
        likes INTEGER DEFAULT 0,
        writer TEXT,
        time TEXT
    )
    """)
    # comments
    cur.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feed_type TEXT,
        feed_id INTEGER,
        nickname TEXT,
        comment TEXT,
        time TEXT
    )
    """)
    # chat
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT,
        message TEXT,
        time TEXT
    )
    """)
    # chat theme
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_theme (
        id INTEGER PRIMARY KEY,
        bg_color TEXT,
        user_color TEXT,
        admin_color TEXT,
        text_color TEXT
    )
    """)
    # likes (alternative)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feed_type TEXT,
        feed_id INTEGER,
        nickname TEXT
    )
    """)

# Try to connect and create tables; if DB is corrupted, backup and reset
def safe_init_db(path):
    try:
        conn, cur = init_conn(path)
        create_tables(cur)
        conn.commit()
        return conn, cur
    except Exception as e:
        # backup corrupted DB
        try:
            backup = path + ".bak." + datetime.now().strftime("%Y%m%d%H%M%S")
            pathlib.Path(path).rename(backup)
        except Exception:
            pass
        # create fresh DB
        conn, cur = init_conn(path)
        create_tables(cur)
        conn.commit()
        return conn, cur

conn, c = safe_init_db(DB_PATH)

# Ensure default admin and chat theme exist
def ensure_defaults():
    try:
        if not c.execute("SELECT * FROM profile WHERE username='admin'").fetchone():
            c.execute("INSERT INTO profile VALUES (?,?,?,?)",
                      ("admin", "안녕하세요! 관리자 프로필입니다.", None, "1234"))
        if not c.execute("SELECT * FROM chat_theme WHERE id=1").fetchone():
            c.execute("INSERT INTO chat_theme VALUES (1, ?, ?, ?, ?)",
                      ("#F2F2F2", "#FFFFFF", "#FFE812", "#000000"))
        conn.commit()
    except Exception:
        conn.rollback()

ensure_defaults()

# ---------------------------
# Utilities
# ---------------------------
def now_hm():
    return datetime.now().strftime("%H:%M")

def now_full():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

# safe execute wrapper
def db_execute(query, params=(), fetch=False):
    try:
        cur = c
        cur.execute(query, params)
        conn.commit()
        if fetch:
            return cur.fetchall()
    except Exception:
        # log and reinit DB if fatal
        st.error("데이터베이스 오류가 발생했습니다. 자동 복구를 시도합니다.")
        traceback.print_exc()
        conn.rollback()
        # try reinit
        global conn, c
        conn.close()
        conn, c = safe_init_db(DB_PATH)
        ensure_defaults()
        return []

# ---------------------------
# Sidebar: admin login
# ---------------------------
st.sidebar.title("관리자 로그인")
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    sid = st.sidebar.text_input("아이디", key="sid")
    spw = st.sidebar.text_input("비밀번호", type="password", key="spw")
    if st.sidebar.button("로그인"):
        row = db_execute("SELECT * FROM profile WHERE username=? AND password=?", (sid, spw), fetch=True)
        if row:
            st.session_state.admin_logged_in = True
            st.sidebar.success("로그인 성공")
            st.experimental_rerun()
        else:
            st.sidebar.error("로그인 실패")
else:
    st.sidebar.success("관리자 로그인 중")
    if st.sidebar.button("로그아웃"):
        st.session_state.admin_logged_in = False
        st.experimental_rerun()

# ---------------------------
# Page layout (tabs)
# ---------------------------
tab_profile, tab_home, tab_admin, tab_fan, tab_chat = st.tabs(
    ["👤 프로필", "🏠 홈", "📝 관리자 피드", "📝 팬/친구 피드", "💬 채팅"]
)

# ---------------------------
# Profile tab
# ---------------------------
with tab_profile:
    st.header("👤 프로필")
    row = db_execute("SELECT username, bio, profile_url FROM profile WHERE username='admin'", fetch=True)
    if row:
        username, bio, profile_url = row[0]
    else:
        username, bio, profile_url = "admin", "안녕하세요!", None

    col1, col2 = st.columns([1,3])
    with col1:
        if profile_url:
            st.image(profile_url, width=150)
        else:
            st.image("https://via.placeholder.com/150", width=150)
    with col2:
        st.subheader(username)
        st.write(bio)

    if st.session_state.admin_logged_in:
        st.markdown("---")
        new_bio = st.text_area("자기소개", value=bio)
        new_img_url = st.text_input("프로필 이미지 URL (빈칸 유지 시 변경 없음)", value=profile_url or "")
        if st.button("프로필 저장"):
            db_execute("UPDATE profile SET bio=?, profile_url=? WHERE username='admin'",
                       (new_bio, new_img_url if new_img_url.strip() else None))
            st.success("프로필 저장됨")
            st.experimental_rerun()

# ---------------------------
# Home tab
# ---------------------------
with tab_home:
    st.header("🏠 링크 모음")
    st.markdown("""
- [YouTube](https://youtube.com)
- [Instagram](https://instagram.com)
- 팬카페 (예시)
    """)

# ---------------------------
# Admin feed tab
# ---------------------------
with tab_admin:
    st.header("📝 관리자 피드 (관리자 전용 작성)")
    posts = db_execute("SELECT id, content, likes, writer, time, pinned FROM feed_admin ORDER BY pinned DESC, id DESC", fetch=True) or []
    for pid, content, likes, writer, time_str, pinned in posts:
        st.markdown(f"**{writer} · {time_str}** {'📌' if pinned else ''}")
        st.write(content)
        cols = st.columns([1, 5])
        if cols[0].button(f"❤️ {likes}", key=f"admin_like_{pid}"):
            db_execute("UPDATE feed_admin SET likes=likes+1 WHERE id=?", (pid,))
            db_execute("INSERT INTO likes (feed_type, feed_id, nickname) VALUES ('admin', ?, ?)", (pid, 'anon'))
            st.experimental_rerun()
        # comments display
        comments = db_execute("SELECT nickname, comment, time FROM comments WHERE feed_type='admin' AND feed_id=? ORDER BY id", (pid,), fetch=True) or []
        for nick, cm_text, cm_time in comments:
            st.markdown(f"> **{nick}**: {cm_text}  \n<sub>{cm_time}</sub>")
        # admin-only actions
        if st.session_state.admin_logged_in:
            if st.button("고정/해제", key=f"pin_{pid}"):
                new_pin = 0 if pinned else 1
                db_execute("UPDATE feed_admin SET pinned=? WHERE id=?", (new_pin, pid))
                st.experimental_rerun()
            comment_input = st.text_input("댓글 (관리자)", key=f"adm_c_{pid}")
            if st.button("댓글 등록", key=f"adm_submit_{pid}") and comment_input.strip():
                db_execute("INSERT INTO comments (feed_type, feed_id, nickname, comment, time) VALUES ('admin', ?, ?, ?, ?)",
                           (pid, "관리자", comment_input.strip(), now_full()))
                st.experimental_rerun()
        st.markdown("---")

    if st.session_state.admin_logged_in:
        st.subheader("➕ 관리자 게시글 작성")
        content = st.text_area("내용")
        if st.button("게시"):
            if content.strip():
                db_execute("INSERT INTO feed_admin (content, writer, time) VALUES (?, ?, ?)",
                           (content.strip(), "admin", now_full()))
                st.success("게시됨")
                st.experimental_rerun()

# ---------------------------
# Fan feed tab
# ---------------------------
with tab_fan:
    st.header("📝 팬/친구 피드")
    posts = db_execute("SELECT id, content, likes, writer, time FROM feed_fan ORDER BY id DESC", fetch=True) or []
    for pid, content, likes, writer, time_str in posts:
        st.markdown(f"**{writer} · {time_str}**")
        st.write(content)
        cols = st.columns([1, 5])
        if cols[0].button(f"❤️ {likes}", key=f"fan_like_{pid}"):
            db_execute("UPDATE feed_fan SET likes=likes+1 WHERE id=?", (pid,))
            db_execute("INSERT INTO likes (feed_type, feed_id, nickname) VALUES ('fan', ?, ?)", (pid, 'anon'))
            st.experimental_rerun()
        comments = db_execute("SELECT nickname, comment, time FROM comments WHERE feed_type='fan' AND feed_id=? ORDER BY id", (pid,), fetch=True) or []
        for nick, cm_text, cm_time in comments:
            st.markdown(f"> **{nick}**: {cm_text}  \n<sub>{cm_time}</sub>")
        nick_input = st.text_input("닉네임", key=f"fan_nick_{pid}")
        cm_input = st.text_input("댓글", key=f"fan_c_{pid}")
        if st.button("댓글 작성", key=f"fan_post_c_{pid}") and cm_input.strip() and nick_input.strip():
            db_execute("INSERT INTO comments (feed_type, feed_id, nickname, comment, time) VALUES ('fan', ?, ?, ?, ?)",
                       (pid, nick_input.strip(), cm_input.strip(), now_full()))
            st.experimental_rerun()
        st.markdown("---")

    st.subheader("✍ 게시글 작성 (팬/친구)")
    writer = st.text_input("이름", key="fan_writer_input")
    content = st.text_area("내용", key="fan_content_input")
    if st.button("게시글 업로드"):
        if writer.strip() and content.strip():
            db_execute("INSERT INTO feed_fan (content, writer, time) VALUES (?, ?, ?)", (content.strip(), writer.strip(), now_full()))
            st.success("업로드 완료")
            st.experimental_rerun()

# ---------------------------
# Chat tab (Kakao-like)
# ---------------------------
with tab_chat:
    st.header("💬 카톡 스타일 채팅")

    # Try to use streamlit-autorefresh if available; otherwise fallback to JS reload.
    use_autorefresh = False
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=1500, key="autorefresh")
        use_autorefresh = True
    except Exception:
        # JS fallback (reload every 1500ms) — keeps form state
        st.markdown(
            """
            <script>
            // If page has focus, don't force reload (to avoid interrupting typing)
            setInterval(()=> {
                if (!document.hasFocus()) {
                    window.location.reload();
                }
            }, 1500);
            </script>
            """,
            unsafe_allow_html=True,
        )

    # chat theme
    theme = db_execute("SELECT bg_color, user_color, admin_color, text_color FROM chat_theme WHERE id=1", fetch=True)
    if theme and len(theme)>0:
        bg_color, user_color, admin_color, text_color = theme[0]
    else:
        bg_color, user_color, admin_color, text_color = "#F2F2F2", "#FFFFFF", "#FFE812", "#000000"

    # nickname stored once
    if "nickname" not in st.session_state or not st.session_state.nickname:
        st.session_state.nickname = st.text_input("닉네임을 입력하세요 (한 번만)", key="nick_login")
        if st.button("입장"):
            if st.session_state.nickname.strip():
                st.experimental_rerun()
        st.stop()

    my_nick = st.session_state.nickname

    # CSS for kakao-like bubbles
    st.markdown(f"""
    <style>
    .chat-area {{ max-width:900px; margin:auto; display:flex; flex-direction:column; gap:8px; }}
    .bubble-left {{ align-self:flex-start; background:{user_color}; color:{text_color}; padding:10px; border-radius:12px; max-width:75%; }}
    .bubble-right {{ align-self:flex-end; background:{admin_color}; color:{text_color}; padding:10px; border-radius:12px; max-width:75%; }}
    .nick {{ font-weight:600; font-size:13px; color:#444; margin-bottom:4px; }}
    .time {{ font-size:10px; color:#666; text-align:right; margin-top:6px; }}
    .chat-wrap {{ height:500px; overflow:auto; padding:10px; border:1px solid #eee; border-radius:8px; background:{bg_color}; }}
    </style>
    """, unsafe_allow_html=True)

    # display messages
    st.markdown("<div class='chat-area'>", unsafe_allow_html=True)
    st.markdown("<div class='chat-wrap'>", unsafe_allow_html=True)

    rows = db_execute("SELECT nickname, message, time FROM chat ORDER BY id DESC LIMIT 300", fetch=True) or []
    rows = rows[::-1]  # oldest first
    for nick, message, t in rows:
        if nick == my_nick:
            st.markdown(f"<div class='bubble-right'>{message}<div class='time'>{t}</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='bubble-left'><div class='nick'>{nick}</div>{message}<div class='time'>{t}</div></div>", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # Input form -> Enter submits
    with st.form(key="chat_form", clear_on_submit=True):
        msg = st.text_input("메시지 입력...", key="chat_input")
        submitted = st.form_submit_button("전송")
        if submitted and msg.strip():
            db_execute("INSERT INTO chat (nickname, message, time) VALUES (?, ?, ?)",
                       (my_nick, msg.strip(), now_hm()))
            st.experimental_rerun()

    if st.session_state.get("admin_logged_in"):
        st.subheader("🎨 채팅 테마 (관리자 전용)")
        nb = st.color_picker("전체 배경색", value=bg_color)
        uc = st.color_picker("왼쪽(팬) 말풍선색", value=user_color)
        ac = st.color_picker("오른쪽(내) 말풍선색", value=admin_color)
        tc = st.color_picker("글자색", value=text_color)
        if st.button("테마 적용"):
            db_execute("UPDATE chat_theme SET bg_color=?, user_color=?, admin_color=?, text_color=? WHERE id=1", (nb, uc, ac, tc))
            st.success("테마 적용됨")
            st.experimental_rerun()




