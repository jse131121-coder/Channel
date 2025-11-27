import streamlit as st
from datetime import datetime
import json
import os
import base64

st.set_page_config(page_title="My Channel", layout="wide")
DATA_FILE = "channel_data.json"

# ----------------- JSON 로드 / 초기화 -----------------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
except json.JSONDecodeError:
    data = {
        "profile": {"admin": {"bio": "안녕하세요! 관리자 프로필입니다.", "profile_b64": None, "password": "1234"}},
        "feed_admin": [],
        "feed_fan": [],
        "chat": [],
        "chat_theme": {"bg_color": "#DCF8C6", "user_color": "#FFFFFF", "admin_color": "#E1F0FF", "text_color": "#000000"}
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ----------------- 세션 초기화 -----------------
for key in ["admin_logged_in", "show_admin_feed_form", "show_fan_feed_form", "chat_nick", "chat_msg"]:
    if key not in st.session_state:
        st.session_state[key] = False if "show" in key or "logged" in key else ""

# ----------------- 사이드바 로그인 -----------------
st.sidebar.subheader("관리자 로그인")
if not st.session_state.admin_logged_in:
    username = st.sidebar.text_input("아이디")
    password = st.sidebar.text_input("비밀번호", type="password")
    if st.sidebar.button("로그인"):
        admin_data = data["profile"].get(username)
        if admin_data and password == admin_data["password"]:
            st.session_state.admin_logged_in = True
            st.sidebar.success(f"{username}님 로그인 성공")
            st.rerun()
        else:
            st.sidebar.error("아이디 또는 비밀번호 틀림")
else:
    st.sidebar.success("관리자 로그인 상태 ✅")
    if st.sidebar.button("로그아웃"):
        st.session_state.admin_logged_in = False
        st.rerun()

# ----------------- 탭 -----------------
tab_profile, tab_home, tab_feed_admin, tab_feed_fan, tab_chat = st.tabs(
    ["👤 프로필", "🏠 홈", "📝 관리자 피드", "📝 팬/친구 피드", "💬 채팅"]
)

# ----------------- 프로필 -----------------
with tab_profile:
    st.subheader("👤 프로필")
    profile = data["profile"]["admin"]
    if profile.get("profile_b64"):
        st.image(base64.b64decode(profile["profile_b64"]), width=150)
    else:
        st.image("https://via.placeholder.com/150", width=150)
    st.markdown("**admin**")
    st.write(profile["bio"])
    if st.session_state.admin_logged_in:
        st.markdown("---")
        st.subheader("프로필 수정 (관리자)")
        new_bio = st.text_area("자기소개", value=profile["bio"])
        uploaded_file = st.file_uploader("프로필 사진 업로드", type=["png","jpg","jpeg"])
        if st.button("저장"):
            data["profile"]["admin"]["bio"] = new_bio
            if uploaded_file:
                img_b64 = base64.b64encode(uploaded_file.read()).decode("utf-8")
                data["profile"]["admin"]["profile_b64"] = img_b64
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            st.success("프로필 업데이트 완료!")
            st.rerun()

# ----------------- 홈 -----------------
with tab_home:
    st.subheader("🏠 링크 모음")
    st.markdown("""
- [유튜브](https://youtube.com)
- [인스타그램](https://instagram.com)
- [팬 카페](https://example.com)
""")
    st.info("링크를 추가/편집 가능")

# ----------------- 관리자 피드 -----------------
with tab_feed_admin:
    st.subheader("📝 관리자 피드")
    for post in reversed(data["feed_admin"]):
        text = f"**{post['writer']} · {post['time']}**"
        st.markdown(text)
        st.write(post["content"])
        if post.get("image_b64"):
            st.image(base64.b64decode(post["image_b64"]), width=300)
        # 댓글/좋아요
        post.setdefault("comments", [])
        post.setdefault("likes", 0)
        st.markdown(f"❤️ {post['likes']}  💬 {len(post['comments'])}")
        for c in post["comments"]:
            st.markdown(f"> **{c['nickname']}**: {c['comment']}")
        if st.session_state.admin_logged_in:
            # 댓글 작성
            c_text = st.text_input(f"{post['writer']} 댓글 작성", key=f"admin_comment_{post['time']}")
            if st.button("댓글 추가", key=f"admin_comment_btn_{post['time']}") and c_text.strip():
                post["comments"].append({"nickname":"관리자","comment":c_text})
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                st.rerun()

    if st.session_state.admin_logged_in:
        if st.button("➕ 고정 게시글 추가 (관리자)"):
            st.session_state.show_admin_feed_form = True
        if st.session_state.show_admin_feed_form:
            content = st.text_area("내용", key="admin_content")
            uploaded_file = st.file_uploader("이미지 업로드", type=["png","jpg","jpeg"], key="admin_feed_img")
            if st.button("게시", key="admin_post"):
                if content:
                    img_b64 = base64.b64encode(uploaded_file.read()).decode("utf-8") if uploaded_file else None
                    data["feed_admin"].append({"writer":"admin","content":content,"image_b64":img_b64,"time":datetime.now().strftime("%Y-%m-%d %H:%M")})
                    with open(DATA_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    st.session_state.show_admin_feed_form = False
                    st.rerun()

# ----------------- 팬/친구 피드 -----------------
with tab_feed_fan:
    st.subheader("📝 팬/친구 피드")
    for post in reversed(data["feed_fan"]):
        st.markdown(f"**{post['writer']} · {post['time']}**")
        st.write(post["content"])
        if post.get("image_b64"):
            st.image(base64.b64decode(post["image_b64"]), width=300)
        # 댓글/좋아요
        post.setdefault("comments", [])
        post.setdefault("likes", 0)
        st.markdown(f"❤️ {post['likes']}  💬 {len(post['comments'])}")
        for c in post["comments"]:
            st.markdown(f"> **{c['nickname']}**: {c['comment']}")
        # 팬 댓글/좋아요
        c_text = st.text_input(f"{post['writer']} 댓글 작성", key=f"fan_comment_{post['time']}")
        if st.button("댓글 추가", key=f"fan_comment_btn_{post['time']}") and c_text.strip():
            nickname = st.text_input("닉네임", value="팬", key=f"fan_name_{post['time']}")
            post["comments"].append({"nickname":nickname,"comment":c_text})
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            st.rerun()
        if st.button("좋아요 ❤️", key=f"fan_like_{post['time']}"):
            post["likes"] +=1
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            st.rerun()

    if st.button("➕ 게시물 작성 (팬/친구)"):
        st.session_state.show_fan_feed_form = True
    if st.session_state.show_fan_feed_form:
        writer = st.text_input("작성자 이름", key="fan_writer")
        content = st.text_area("내용", key="fan_content")
        uploaded_file = st.file_uploader("이미지 업로드", type=["png","jpg","jpeg"], key="fan_feed_img")
        if st.button("게시", key="fan_post"):
            if writer and content:
                img_b64 = base64.b64encode(uploaded_file.read()).decode("utf-8") if uploaded_file else None
                data["feed_fan"].append({"writer":writer,"content":content,"image_b64":img_b64,"time":datetime.now().strftime("%Y-%m-%d %H:%M")})
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                st.session_state.show_fan_feed_form = False
                st.rerun()

# ----------------- 채팅 -----------------
with tab_chat:
    st.subheader("💬 오픈 채팅")
    theme = data["chat_theme"]
    for chat in reversed(data["chat"][-100:]):
        color = theme["admin_color"] if chat.get("is_admin") else theme["user_color"]
        sender = "관리자" if chat.get("is_admin") else chat.get("nickname","팬")
        st.markdown(
            f"<div style='background-color:{color}; color:{theme['text_color']}; padding:8px; margin:4px; border-radius:10px; max-width:70%; float:left; clear:both;'>"
            f"<b>{sender}</b> [{chat['time']}]: {chat['message']}</div><div style='clear:both;'></div>",
            unsafe_allow_html=True
        )

    st.subheader("메시지 작성")
    if not st.session_state.admin_logged_in:
        st.session_state.chat_nick = st.text_input("닉네임", value=st.session_state.chat_nick)
    st.session_state.chat_msg = st.text_input("메시지 입력...", value=st.session_state.chat_msg)
    if st.button("전송"):
        msg = st.session_state.chat_msg.strip()
        if st.session_state.admin_logged_in:
            if msg:
                data["chat"].append({"nickname":"관리자","message":msg,"time":datetime.now().strftime("%H:%M"),"is_admin":True})
                st.session_state.chat_msg=""
                with open(DATA_FILE,"w",encoding="utf-8") as f:
                    json.dump(data,f,ensure_ascii=False,indent=4)
                st.rerun()
        else:
            nick = st.session_state.chat_nick.strip()
            if msg and nick:
                data["chat"].append({"nickname":nick,"message":msg,"time":datetime.now().strftime("%H:%M"),"is_admin":False})
                st.session_state.chat_msg=""
                with open(DATA_FILE,"w",encoding="utf-8") as f:
                    json.dump(data,f,ensure_ascii=False,indent=4)
                st.rerun()

    if st.session_state.admin_logged_in:
        st.markdown("---")
        st.subheader("🎨 채팅 테마 변경 (관리자)")
        new_bg = st.color_picker("전체 배경색", value=theme["bg_color"])
        new_user = st.color_picker("팬 메시지 배경색", value=theme["user_color"])
        new_admin = st.color_picker("관리자 메시지 배경색", value=theme["admin_color"])
        new_text = st.color_picker("글자색", value=theme["text_color"])
        if st.button("테마 적용"):
            data["chat_theme"].update({"bg_color":new_bg,"user_color":new_user,"admin_color":new_admin,"text_color":new_text})
            with open(DATA_FILE,"w",encoding="utf-8") as f:
                json.dump(data,f,ensure_ascii=False,indent=4)
            st.success("채팅 테마 적용 완료")
            st.rerun()
