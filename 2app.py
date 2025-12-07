import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from datetime import datetime
from PIL import Image
import uuid, io

# ======================
# Firebase Init
# ======================
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        "storageBucket": "<YOUR_PROJECT_ID>.appspot.com"
    })

db = firestore.client()
bucket = storage.bucket()

# ======================
# Page / Dark UI
# ======================
st.set_page_config(page_title="AOUSE", layout="centered")

st.markdown("""
<style>
html, body { background:#0f0f0f; color:white; }
.block-container { max-width:420px; padding:1.2rem; }
input, textarea { background:#1a1a1a !important; color:white !important; }
button { border-radius:20px !important; }
hr { border:0; border-top:1px solid #222; }
.small { color:#888; font-size:12px; }
.reply { margin-left:20px; color:#aaa; font-size:14px; }
</style>
""", unsafe_allow_html=True)

# ======================
# Session
# ======================
if "uid" not in st.session_state:
    st.session_state.uid = None
if "profile" not in st.session_state:
    st.session_state.profile = None

# ======================
# Badge auto update
# ======================
def update_badge(uid):
    posts = list(db.collection("posts").where("user_id","==",uid).stream())
    c = len(posts)

    badge = "FRIEND"
    if c >= 5: badge = "ACTIVE"
    if c >= 15: badge = "CREATOR"
    if c >= 30: badge = "ICON"

    db.collection("users").document(uid).update({"badge": badge})
    st.session_state.profile["badge"] = badge

# ======================
# Login
# ======================
def login():
    st.title("AOUSE")
    st.caption("private space for friends")
    if st.button("enter"):
        user = auth.create_user(uid=str(uuid.uuid4()))
        st.session_state.uid = user.uid
        st.experimental_rerun()

# ======================
# Profile setup / edit
# ======================
def profile_setup(edit=False):
    st.subheader("Edit profile" if edit else "Set up profile")

    nickname = st.text_input(
        "Nickname",
        value=st.session_state.profile["nickname"] if edit else ""
    )
    image = st.file_uploader("Profile image", type=["png","jpg"])

    if st.button("Save"):
        img_url = st.session_state.profile["profile_image"] if edit else None

        if image:
            img = Image.open(image)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            blob = bucket.blob(f"profile/{st.session_state.uid}.png")
            blob.upload_from_string(buf.getvalue(), content_type="image/png")
            blob.make_public()
            img_url = blob.public_url

        profile = {
            "nickname": nickname,
            "profile_image": img_url,
            "badge": st.session_state.profile["badge"] if edit else "FRIEND"
        }

        db.collection("users").document(st.session_state.uid).set(profile)
        st.session_state.profile = profile
        st.experimental_rerun()

# ======================
# Timeline
# ======================
def timeline():
    st.markdown(
        f"**{st.session_state.profile['nickname']}** "
        f"<span class='small'>🏷 {st.session_state.profile['badge']}</span>",
        unsafe_allow_html=True
    )

    if st.button("Edit profile"):
        profile_setup(edit=True)
        st.stop()

    st.divider()

    # New post
    with st.form("post"):
        text = st.text_area("Write something")
        image = st.file_uploader("Image", type=["png","jpg"])
        send = st.form_submit_button("Post")

        if send:
            img_url = None
            if image:
                img = Image.open(image)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                blob = bucket.blob(f"posts/{uuid.uuid4()}.png")
                blob.upload_from_string(buf.getvalue(), content_type="image/png")
                blob.make_public()
                img_url = blob.public_url

            db.collection("posts").add({
                "user_id": st.session_state.uid,
                "nickname": st.session_state.profile["nickname"],
                "badge": st.session_state.profile["badge"],
                "text": text,
                "image": img_url,
                "time": datetime.now(),
                "likes": [],
                "comments": []
            })

            update_badge(st.session_state.uid)
            st.experimental_rerun()

    st.divider()

    # Posts
    posts = db.collection("posts").order_by("time", direction=firestore.Query.DESCENDING).stream()

    for p in posts:
        d = p.to_dict()

        st.markdown(
            f"**{d['nickname']}** <span class='small'>🏷 {d['badge']}</span>",
            unsafe_allow_html=True
        )
        if d["text"]:
            st.write(d["text"])
        if d["image"]:
            st.image(d["image"], use_column_width=True)

        # Like
        likes = d["likes"]
        if st.button(f"❤️ {len(likes)}", key=p.id):
            if st.session_state.uid in likes:
                likes.remove(st.session_state.uid)
            else:
                likes.append(st.session_state.uid)
            db.collection("posts").document(p.id).update({"likes": likes})
            st.experimental_rerun()

        # Comments + replies
        for c in d["comments"]:
            st.markdown(f"**{c['nickname']}** {c['text']}")

            for r in c["replies"]:
                st.markdown(
                    f"<div class='reply'>↳ {r['nickname']} {r['text']}</div>",
                    unsafe_allow_html=True
                )

            reply = st.text_input("reply", key=f"r_{p.id}_{c['id']}")
            if st.button("↳", key=f"rb_{p.id}_{c['id']}"):
                c["replies"].append({
                    "nickname": st.session_state.profile["nickname"],
                    "text": reply
                })
                db.collection("posts").document(p.id).update({"comments": d["comments"]})
                st.experimental_rerun()

        # New comment
        comment = st.text_input("comment", key=f"c_{p.id}")
        if st.button("send", key=f"s_{p.id}"):
            d["comments"].append({
                "id": str(uuid.uuid4()),
                "nickname": st.session_state.profile["nickname"],
                "text": comment,
                "replies": []
            })
            db.collection("posts").document(p.id).update({"comments": d["comments"]})
            st.experimental_rerun()

        st.divider()

# ======================
# Run
# ======================
if st.session_state.uid is None:
    login()
else:
    if st.session_state.profile is None:
        doc = db.collection("users").document(st.session_state.uid).get()
        if doc.exists:
            st.session_state.profile = doc.to_dict()
            timeline()
        else:
            profile_setup()
    else:
        timeline()



