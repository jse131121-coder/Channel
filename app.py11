import streamlit as st
import json, os, uuid
from PIL import Image

# ======================
# 기본 세팅
# ======================
st.set_page_config(page_title="AOUSE", layout="centered")

DATA_FILE = "data.json"
IMAGE_DIR = "images"

ADMIN_NAME = "ARTIST"   # 관리자 이름

if not os.path.exists(IMAGE_DIR):
    os.mkdir(IMAGE_DIR)

# ======================
# 데이터 로드 / 저장
# ======================
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

posts = load_data()

# ======================
# 세션 (로그인 대체)
# ======================
if "name" not in st.session_state:
    st.session_state.name = ""

# ======================
# 프로필 설정
# ======================
st.title("AOUSE")

if st.session_state.name == "":
    name = st.text_input("닉네임")
    if st.button("입장"):
        st.session_state.name = name
        st.experimental_rerun()
    st.stop()

is_admin = st.session_state.name == ADMIN_NAME

st.caption(
    "⭐ ARTIST" if is_admin else "FRIEND"
)

st.divider()

# ======================
# 글 작성
# ======================
with st.form("post_form"):
    content = st.text_area("게시글")
    img = st.file_uploader("사진", ["png","jpg"])
    ok = st.form_submit_button("업로드")

    if ok:
        img_path = None
        if img:
            image = Image.open(img)
            path = f"{IMAGE_DIR}/{uuid.uuid4()}.png"
            image.save(path)
            img_path = path

        posts.insert(0, {
            "id": str(uuid.uuid4()),
            "author": st.session_state.name,
            "text": content,
            "image": img_path,
            "likes": [],
            "comments": []
        })
        save_data(posts)
        st.experimental_rerun()

# ======================
# 타임라인
# ======================
for post in posts:
    st.subheader(
        f"{post['author']} {'⭐ ARTIST' if post['author']==ADMIN_NAME else ''}"
    )

    if post["text"]:
        st.write(post["text"])
    if post["image"]:
        st.image(post["image"], use_column_width=True)

    # 좋아요
    like_count = len(post["likes"])
    if st.button(f"❤️ {like_count}", key=post["id"]):
        if st.session_state.name in post["likes"]:
            post["likes"].remove(st.session_state.name)
        else:
            post["likes"].append(st.session_state.name)
        save_data(posts)
        st.experimental_rerun()

    # 댓글
    for c in post["comments"]:
        st.markdown(f"**{c['author']}** {c['text']}")
        for r in c["replies"]:
            st.markdown(f"> ⭐ ARTIST {r}")

    # 댓글 입력
    comment = st.text_input("댓글", key=post["id"]+"_c")
    if st.button("전송", key=post["id"]+"_s"):
        post["comments"].append({
            "author": st.session_state.name,
            "text": comment,
            "replies": []
        })
        save_data(posts)
        st.experimental_rerun()

    # 관리자 대댓글
    if is_admin and post["comments"]:
        reply = st.text_input("관리자 대댓글", key=post["id"]+"_r")
        if st.button("답글", key=post["id"]+"_rb"):
            post["comments"][-1]["replies"].append(reply)
            save_data(posts)
            st.experimental_rerun()

    st.divider()
