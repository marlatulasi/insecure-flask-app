from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

# Insecure web app for learning purposes
# Passwords stored in plaintext, no CSRF protection, etc.

app = Flask(__name__)
app.secret_key = 'supersecret'  # insecure default
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DATABASE = 'app.db'

# Database helpers

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # users table stores plaintext passwords
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            image TEXT
        )
    ''')
    # posts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()
init_db()




@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username,password) VALUES (?,?)', (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('Username already taken')
            return redirect(url_for('register'))
        conn.close()
        flash('Registration successful, please log in')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Logged in successfully')
            return redirect(url_for('profile'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out')
    return redirect(url_for('index'))


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        newpw = request.form['newpassword']
        conn = get_db_connection()
        conn.execute('UPDATE users SET password = ? WHERE id = ?', (newpw, session['user_id']))
        conn.commit()
        conn.close()
        flash('Password updated')
        return redirect(url_for('profile'))
    return render_template('change_password.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files['image']
        if file:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            conn = get_db_connection()
            conn.execute('UPDATE users SET image = ? WHERE id = ?', (filename, session['user_id']))
            conn.commit()
            conn.close()
            flash('Image uploaded')
            return redirect(url_for('gallery'))
    return render_template('upload.html')


@app.route('/gallery')
def gallery():
    conn = get_db_connection()
    users = conn.execute('SELECT username, image FROM users WHERE image IS NOT NULL').fetchall()
    conn.close()
    return render_template('gallery.html', users=users)


@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        content = request.form['content']
        conn = get_db_connection()
        conn.execute('INSERT INTO posts (user_id, content) VALUES (?,?)', (session['user_id'], content))
        conn.commit()
        conn.close()
        flash('Post created')
        return redirect(url_for('posts'))
    return render_template('create_post.html')


@app.route('/posts')
def posts():
    conn = get_db_connection()
    posts = conn.execute('SELECT p.id, p.content, u.username FROM posts p JOIN users u ON p.user_id = u.id').fetchall()
    conn.close()
    return render_template('posts.html', posts=posts)


@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    if request.method == 'POST':
        query = request.form['query']
        conn = get_db_connection()
        results = conn.execute("SELECT p.content,u.username FROM posts p JOIN users u ON p.user_id=u.id WHERE p.content LIKE '%" + query + "%'").fetchall()
        conn.close()
    return render_template('search.html', results=results)


if __name__ == '__main__':
    app.run(debug=True)
