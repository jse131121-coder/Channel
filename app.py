import streamlit as st
import sqlite3
import pathlib
from datetime import datetime

# ===============================
# DB 설정 (⭐ 핵심 수정 포인트)
# ===============================
DB_PATH = str(pathlib.Path("channel.db").resolve())
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
c.execute("PRAGMA foreign_keys = ON")
conn.commit()

# ===============================
# 테이블 생성
# ===============================
c.execute("""
CREATE TABLE IF NOT EXISTS admin_feed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    created_at TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS fan_feed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    created_at TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_type TEXT,
    feed_id INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_type TEXT,
    feed_id INTEGER,
    comment TEXT,
    created_at TEXT
)
""")
conn.commit()

# ===============================
# 기본 UI
# ===============================
st.set_page_config(page_title="CHANNEL", layout="centered")
st.title("📺 CHANNEL")

tab1, tab2 = st.tabs(["🛠 관리자 피드", "💬 팬 피드"])

# ===============================
# 관리자 피드
# ===============================
with tab1:
    st.subheader("관리자 피드 작성")

    admin_text = st.text_area("내용 입력")
    if st.button("업로드", key="admin_upload"):
        if admin_text.strip():
            c.execute(
                "INSERT INTO admin_feed (content, created_at) VALUES (?, ?)",
                (admin_text, datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()
            st.success("업로드 완료 ✅")
            st.rerun()

    st.divider()

    c.execute("SELECT * FROM admin_feed ORDER BY id DESC")
    posts = c.fetchall()

    for post in posts:
        st.markdown(f"### 📌 관리자")
        st.write(post[1])
        st.caption(post[2])

        # 좋아요
        like_count = c.execute(
            "SELECT COUNT(*) FROM likes WHERE feed_type='admin' AND feed_id=?",
            (post[0],)
        ).fetchone()[0]

        if st.button(f"❤️ {like_count}", key=f"admin_like_{post[0]}"):
            c.execute(
                "INSERT INTO likes (feed_type, feed_id) VALUES ('admin', ?)",
                (post[0],)
            )
            conn.commit()
            st.rerun()

        # 댓글
        comment = st.text_input(
            "댓글",
            key=f"admin_comment_{post[0]}"
        )
        if st.button("댓글 작성", key=f"admin_comment_btn_{post[0]}"):
            if comment.strip():
                c.execute(
                    "INSERT INTO comments (feed_type, feed_id, comment, created_at) VALUES (?, ?, ?, ?)",
                    ("admin", post[0], comment, datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
                conn.commit()
                st.rerun()

        comments = c.execute(
            "SELECT comment, created_at FROM comments WHERE feed_type='admin' AND feed_id=?",
            (post[0],)
        ).fetchall()

        for cm in comments:
            st.write(f"💬 {cm[0]}")
            st.caption(cm[1])

        st.divider()

# ===============================
# 팬 피드
# ===============================
with tab2:
    st.subheader("팬 피드 작성")

    fan_text = st.text_area("팬 메시지")
    if st.button("업로드", key="fan_upload"):
        if fan_text.strip():
            c.execute(
                "INSERT INTO fan_feed (content, created_at) VALUES (?, ?)",
                (fan_text, datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()
            st.success("업로드 완료 ✅")
            st.rerun()

    st.divider()

    c.execute("SELECT * FROM fan_feed ORDER BY id DESC")
    posts = c.fetchall()

    for post in posts:
        st.markdown("### 🙌 팬")
        st.write(post[1])
        st.caption(post[2])

        like_count = c.execute(
            "SELECT COUNT(*) FROM likes WHERE feed_type='fan' AND feed_id=?",
            (post[0],)
        ).fetchone()[0]

        if st.button(f"❤️ {like_count}", key=f"fan_like_{post[0]}"):
            c.execute(
                "INSERT INTO likes (feed_type, feed_id) VALUES ('fan', ?)",
                (post[0],)
            )
            conn.commit()
            st.rerun()

        comment = st.text_input(
            "댓글",
            key=f"fan_comment_{post[0]}"
        )
        if st.button("댓글 작성", key=f"fan_comment_btn_{post[0]}"):
            if comment.strip():
                c.execute(
                    "INSERT INTO comments (feed_type, feed_id, comment, created_at) VALUES (?, ?, ?, ?)",
                    ("fan", post[0], comment, datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
                conn.commit()
                st.rerun()

        comments = c.execute(
            "SELECT comment, created_at FROM comments WHERE feed_type='fan' AND feed_id=?",
            (post[0],)
        ).fetchall()

        for cm in comments:
            st.write(f"💬 {cm[0]}")
            st.caption(cm[1])

        st.divider()

