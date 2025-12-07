import streamlit as st
from datetime import datetime
import uuid
import os
import json
from PIL import Image

# ======================
# 기본 설정
# ======================
st.set_page_config(page_title="AOUSE", layout="centered")

DATA_FILE = "posts.json"
IMG_DIR = "images"
os.makedirs(IMG_DIR, exist_ok=True)

# ======================
# 데이터 저장 / 불러오기
# ======================
def load_posts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # likes는 set으로 복구
            for p in data:
                p["likes"] = set(p["likes"])
            return data
    return []

def save_posts(posts):
    data = []
    for p in posts:
        cp = p.copy()
        cp["likes"] = list(cp["likes"])
        data.append(cp)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================
# 세션 상태
# ======================
if "user" not in st.session_state:
    st.session_state.user = None

if "posts" not in st.session_state:
    st.session_state.posts = load_posts()

# ======================
# 로그인
# ======================
def login():
    st.title("AOUSE")
    st.caption("friends only space")

    username = st.text_input("username")
    if st.button("enter"):
        if username.strip():
            st.session_state.user = username.strip()
            st.experimental_rerun()

# ======================
# 타임라인
# ======================
def timeline():
    st.markdown(f"**@{st.session_state.user}**")
    if st.button("logout"):
        st.session_state.user = None
        st.experimental_rerun()

    st.divider()

    # 새 글 작성
    with st.form("new_post"):
        text = st.text_area("Write something...", height=80)
        image = st.file_uploader("Photo", type=["png","jpg","jpeg"])
        submitted = st.form_submit_button("Post")

        if submitted and (text or image):
            filename = None
            if image:
                filename = f"{uuid.uuid4()}.png"
                Image.open(image).save(f"{IMG_DIR}/{filename}")

            post = {
                "id": str(uuid.uuid4()),
                "user": st.session_state.user,
                "text": text,
                "image": filename,
                "time": datetime.now().strftime("%Y.%m.%d %H:%M"),
                "likes": set(),
                "comments": []
            }
            st.session_state.posts.insert(0, post)
            save_posts(st.session_state.posts)
            st.experimental_rerun()

    st.divider()

    # 포스트 출력
    for post in st.session_state.posts:
        st.markdown(f"**@{post['user']}**")
        if post["text"]:
            st.write(post["text"])
        if post["image"]:
            st.image(f"{IMG_DIR}/{post['image']}", use_column_width=True)

        # 좋아요
        if st.button(
            f"❤️ {len(post['likes'])}",
            key=f"like_{post['id']}"
        ):
            if st.session_state.user in post["likes"]:
                post["likes"].remove(st.session_state.user)
            else:
                post["likes"].add(st.session_state.user)
            save_posts(st.session_state.posts)
            st.experimental_rerun()

        st.caption(post["time"])

        # 댓글
        st.markdown("**Comments**")
        for c in post["comments"]:
            st.markdown(f"- **@{c['user']}** {c['text']}  \n_{c['time']}_")

            # 답글
            for r in c["replies"]:
                st.markdown(
                    f"　↳ **@{r['user']}** {r['text']}  \n　_{r['time']}_"
                )

            reply_text = st.text_input(
                "reply",
                key=f"reply_{c['id']}"
            )
            if st.button("reply", key=f"btn_reply_{c['id']}"):
                if reply_text.strip():
                    c["replies"].append({
                        "user": st.session_state.user,
                        "text": reply_text,
                        "time": datetime.now().strftime("%H:%M")
                    })
                    save_posts(st.session_state.posts)
                    st.experimental_rerun()

        # 댓글 작성
        comment_text = st.text_input(
            "Add a comment",
            key=f"comment_{post['id']}"
        )
        if st.button("comment", key=f"btn_comment_{post['id']}"):
            if comment_text.strip():
                post["comments"].append({
                    "id": str(uuid.uuid4()),
                    "user": st.session_state.user,
                    "text": comment_text,
                    "time": datetime.now().strftime("%H:%M"),
                    "replies": []
                })
                save_posts(st.session_state.posts)
                st.experimental_rerun()

        st.divider()

# ======================
# 실행
# ======================
if st.session_state.user is None:
    login()
else:
    timeline()

