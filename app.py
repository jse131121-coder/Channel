import streamlit as st
from datetime import datetime
import sqlite3

st.set_page_config(page_title="My Channel", layout="wide")

# ================= DB =================
conn = sqlite3.connect("channel.db", check_same_thread=False)
c = conn.cursor()

# ---------- tables ----------
c.execute("""
CREATE TABLE IF NOT EXISTS profile (
    username TEXT PRIMARY KEY,
    bio TEXT,
    profile_url TEXT,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS feed_admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    image_url TEXT,
    likes INTEGER DEFAULT 0,
    writer TEXT,
    time TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS feed_fan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    image_url TEXT,
    likes INTEGER DEFAULT 0,
    writer TEXT,
    time TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_type TEXT,
    feed_id INTEGER,
    nickname TEXT,
    comment TEXT,
    time TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS chat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nickname TEXT,
    message TEXT,
    time TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS chat_theme (
    id INTEGER PRIMARY KEY,
    bg_color TEXT,
    text_color TEXT
)
