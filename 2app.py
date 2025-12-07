from flask import Flask, request, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

# =====================
# 기본 설정
# =====================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'friends-only-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aouse.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# =====================
# DB 모델
# =====================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    image = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =====================
# HTML 템플릿 (inline)
# =====================
BASE = """
<!doctype html>
<title>AOUSE friends</title>
<style>
body{font-family:sans-serif;max-width:500px;margin:auto}
.post{border-bottom:1px solid #ddd;padding:10px 0}
img{max-width:100%;border-radius:8px}
a{margin-right:10px}
</style>
{% if current_user.is_authenticated %}
<p>
  {{ current_user.username }} |
  <a href="/post">New</a>
  <a href="/logout">Logout</a>
</p>
{% else %}
<p>
  <a href="/login">Login</a>
  <a href="/register">Register</a>
</p>
{% endif %}
<hr>
{% block content %}{% endblock %}
"""

# =====================
# 라우트
# =====================
@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template_string(
        "{% extends base %}{% block content %}" +
        "".join([
            "<div class='post'><b>User {{p.user_id}}</b><p>{{p.content}}</p>" +
            ("<img src='/static/uploads/{{p.image}}'>" if p.image else "") +
            "<small>{{p.created_at}}</small></div>"
            for p in posts
        ]) +
        "{% endblock %}",
        posts=posts, base=BASE
    )

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            password=generate_password_hash(request.form['password'])
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template_string("""
    <form method="post">
      <input name="username" placeholder="username"><br>
      <input name="password" type="password" placeholder="password"><br>
      <button>Register</button>
    </form>
    """)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
    return render_template_string("""
    <form method="post">
      <input name="username"><br>
      <input name="password" type="password"><br>
      <button>Login</button>
    </form>
    """)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/post', methods=['GET','POST'])
@login_required
def post():
    if request.method == 'POST':
        image = request.files.get('image')
        filename = None
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        post = Post(
            content=request.form['content'],
            image=filename,
            user_id=current_user.id
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template_string("""
    <form method="post" enctype="multipart/form-data">
      <textarea name="content" placeholder="Write something..."></textarea><br>
      <input type="file" name="image"><br>
      <button>Post</button>
    </form>
    """)

# =====================
# 실행
# =====================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
