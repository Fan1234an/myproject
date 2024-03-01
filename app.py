import sqlite3
from flask import Flask, redirect, url_for, request, render_template, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Mail, Message
import os
from package.aa import main
from package.bb import maina
from apscheduler.schedulers.background import BackgroundScheduler
import base64
import psycopg2
import urllib.parse as urlparse
app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key')
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'asd31564616@gmail.com'
app.config['MAIL_PASSWORD'] = 'kjotvuhfsxdjqxcx'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = 'asd31564616@gmail.com'

mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

def send_email(to, subject, body):
    msg = Message(subject, recipients=[to], body=body)
    mail.send(msg)

def job_function():
    with app.app_context():
        main()
        maina()
scheduler = BackgroundScheduler()
scheduler.add_job(job_function, 'interval', days=7)
scheduler.start()
job_function() # 開發測試用

@app.route("/post")
def newpost():
    with sqlite3.connect('images.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, data FROM images ORDER BY id DESC")
        images_info = cursor.fetchall()
    return render_template('post.html',images_info=images_info)

@app.route("/post2")
def newpost2():
    with sqlite3.connect('images.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, image FROM acg_info ORDER BY id DESC")
        images_info1 = cursor.fetchall()
    return render_template('post2.html',images_info1=images_info1)

@app.route("/post3")
def newpost3():
    return render_template('post3.html')
# 接收使用者發佈訊息
@app.route('/submit_post', methods=['POST'])
def submit_post():
    if request.method == 'POST':
        if "user_info" in session:
            name = session['user_info']['name']
            forum = request.form['post_forum']  # 这是图片的ID
            tags = request.form['post_list']
            title = request.form['post_title']
            content = request.form['post_content']
            # 从 images 表中获取选择的图片数据
            with sqlite3.connect('images.db') as conn:
                cursor = conn.cursor()
                # 根据图片ID查询数据
                cursor.execute("SELECT data FROM images WHERE id = ?", (forum,))
                image_data = cursor.fetchone()
            if image_data:
                # 将图片数据和其他表单数据一起插入 user_activities 表中
                with sqlite3.connect('account.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO user_activities (forum, tags, user, title, content, image_data) VALUES (?, ?, ?, ?, ?, ?)", 
                                   (forum, tags, name, title, content, image_data[0]))
                    conn.commit()

            flash('Post submitted successfully!')
            return redirect(url_for('home'))
        
@app.route('/submit_post2', methods=['POST'])
def submit_post2():
    if request.method == 'POST':
        if "user_info" in session:
            name = session['user_info']['name']
            forum = request.form['post_forum']  # 这是图片的ID
            tags = request.form['post_list']
            title = request.form['post_title']
            content = request.form['post_content']
            # 从 images 表中获取选择的图片数据
            with sqlite3.connect('images.db') as conn:
                cursor = conn.cursor()
                # 根据图片ID查询数据
                cursor.execute("SELECT image FROM acg_info WHERE id = ?", (forum,))
                image_data = cursor.fetchone()
            if image_data:
                # 将图片数据和其他表单数据一起插入 user_activities 表中
                with sqlite3.connect('account.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO animation_activities (forum, tags, user, title, content, image_data) VALUES (?, ?, ?, ?, ?, ?)", 
                                   (forum, tags, name, title, content, image_data[0]))
                    conn.commit()
            flash('Post submitted successfully!')
            return redirect(url_for('home'))

@app.route('/submit_post3', methods=['POST'])
def submit_post3():
    if request.method == 'POST':
        if "user_info" in session:
            name = session['user_info']['name']
            tags = request.form['post_list']
            title = request.form['post_title']
            content = request.form['post_content']
            with sqlite3.connect('account.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO message_activities ( tags, user, title, content) VALUES ( ?, ?, ?, ?)", ( tags, name, title, content))
                    conn.commit()
        flash('Post submitted successfully!')
        return redirect(url_for('home'))

# 刪除貼文
@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    with sqlite3.connect('account.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_activities WHERE id = ?", (post_id,))
        conn.commit()
        flash("貼文刪除成功！")
        return redirect(url_for('home'))
@app.route('/delete_post1/<int:post_id>', methods=['POST'])
def delete_post1(post_id):
    with sqlite3.connect('account.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM animation_activities WHERE id = ?", (post_id,))
        conn.commit()
        flash("貼文刪除成功！")
        return redirect(url_for('home'))
@app.route('/delete_post2/<int:post_id>', methods=['POST'])
def delete_post2(post_id):
    with sqlite3.connect('account.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM message_activities WHERE id = ?", (post_id,))
        conn.commit()
        flash("貼文刪除成功！")
        return redirect(url_for('home'))
    
@app.route("/home")
def home():
    if "user_info" in session:
        user_info = session['user_info']
        
        with sqlite3.connect('account.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, forum, tags, title, user, content, image_data FROM user_activities ORDER BY id DESC")
            posts = [{
                'id': row[0],
                'forum': row[1],
                'tags': row[2],
                'title': row[3],
                'user': row[4],
                'content': row[5],
                'image_data': base64.b64encode(row[6]).decode('ascii') if row[6] else None
            } for row in cursor.fetchall()]
            
        with sqlite3.connect('account.db') as conn:
            cursor1 = conn.cursor()
            cursor1.execute("SELECT id, forum, tags, title, user, content, image_data FROM animation_activities ORDER BY id DESC")
            posts1 = [{
                'id': row[0],
                'forum': row[1],
                'tags': row[2],
                'title': row[3],
                'user': row[4],
                'content': row[5],
                'image_data': base64.b64encode(row[6]).decode('ascii') if row[6] else None
            } for row in cursor1.fetchall()]

        with sqlite3.connect('account.db') as conn:
            cursor2 = conn.cursor()
            cursor2.execute("SELECT id, tags, title, user, content FROM message_activities ORDER BY id DESC")
            posts2 = cursor2.fetchall()
            
        with sqlite3.connect('images.db') as conn:
            games = conn.cursor()
            games.execute("SELECT title, url, score, popularity, data FROM images ORDER BY id DESC")
            games = [{
                'title': row[0],
                'url': row[1],
                'score': row[2],
                'popularity': row[3],
                'data': base64.b64encode(row[4]).decode('ascii') if row[4] else None
            } for row in games.fetchall()]
        
        with sqlite3.connect('images.db') as conn:
            animations = conn.cursor()
            animations.execute("SELECT title, url, score, popularity, image FROM acg_info ORDER BY id DESC")
            animations = [{
                'title': row[0],
                'url': row[1],
                'score': row[2],
                'popularity': row[3],
                'image': base64.b64encode(row[4]).decode('ascii') if row[4] else None
            } for row in animations.fetchall()]
        return render_template('index.html', user_info=user_info, posts=posts, posts1=posts1, posts2=posts2, games=games, animations=animations)
    else:
        return redirect("/login")

@app.route("/")
def signup():
    if "user_info" in session:  
        user_info = session['user_info']
        return render_template('index.html', user_info=user_info)
    else:
        return redirect(url_for("login"))
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        passwd = request.form['password']
        
        with sqlite3.connect('account.db') as conn:
            cursor = conn.cursor()
            # 從資料庫檢索密碼、姓名、電子郵件和確認狀態
            cursor.execute("SELECT passwd, name, email, confirmed FROM lccnet WHERE user=?", (user,))
            data = cursor.fetchone()
        
        if data is None:
            flash("帳號不存在")
            return redirect(url_for('login'))
        
        if not check_password_hash(data[0], passwd):
            flash("密碼錯誤")
            return redirect(url_for('login'))
        
        if not data[3]:  # 檢查確認列是否為 False (0)(1為驗證過
            flash("請先透過電子郵件確認您的帳戶")
            return redirect(url_for('login'))  
        
        # 通過繼續登錄
        session['user_info'] = {
            'username': user,
            'name': data[1],
            'email': data[2]
        }
        return redirect(url_for('home'))
    else:
        return render_template('signin.html')

def initialize_db():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lccnet (
        id SERIAL PRIMARY KEY,
        user TEXT NOT NULL UNIQUE,
        passwd TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        confirmed INTEGER DEFAULT 0
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_tokens (
        id SERIAL PRIMARY KEY,
        user TEXT NOT NULL,
        token TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_activities (
        id SERIAL PRIMARY KEY,
        forum TEXT NOT NULL,
        tags TEXT NOT NULL,
        user TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        image_data BYTEA,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user) REFERENCES lccnet(user)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS animation_activities (
        id SERIAL PRIMARY KEY,
        forum TEXT NOT NULL,
        tags TEXT NOT NULL,
        user TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        image_data BYTEA,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user) REFERENCES lccnet(user)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS message_activities (
        id SERIAL PRIMARY KEY,
        tags TEXT NOT NULL,
        user TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user) REFERENCES lccnet(user)
    )
    ''')
    conn.commit()
    cursor.close()
initialize_db()

@app.route('/reg', methods=['POST', 'GET'])
def reg():
    if request.method == 'POST':
        try:
            name = request.form['fullname']
            user = request.form['username']
            passwd = generate_password_hash(request.form['password'])
            email = request.form['email']
            token = s.dumps(email, salt='email-confirm')
            link = url_for('confirm_email', token=token, _external=True)
            send_email(email, '確認您的電子郵件', '請點擊連結確認您的電子郵件: ' + link)
            
            with sqlite3.connect('account.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO lccnet (user, passwd, name, email) VALUES (?, ?, ?, ?)", (user, passwd, name, email))
                cursor.execute("INSERT INTO email_tokens (user, token) VALUES (?, ?)", (user, token))
                conn.commit()

            return "註冊成功，請前往信箱驗證<b><a href = '/login'>點選這裡登錄</a></b>"
        except sqlite3.IntegrityError:
            return "註冊失敗帳號已存在"
        except Exception as e:
            return "註冊失敗，錯誤：{}".format(e)
    else:
        return render_template('reg.html')
    
@app.route('/resend_confirmation', methods=['GET', 'POST'])
def resend_confirmation():
    if request.method == 'POST':
        email = request.form['email']
        try:
            token = s.dumps(email, salt='email-confirm')
            link = url_for('confirm_email', token=token, _external=True)
            send_email(email, '確認您的電子郵件', '請點擊連結確認您的電子郵件: ' + link)
            flash('新的確認電子郵件已發送.')
        except Exception as e:
            flash("重新發送確認電子郵件時發生錯誤: {}".format(e))
        return redirect(url_for('login'))
    else:
        return render_template('resend_confirmation.html')
    
@app.route('/confirm_email/<token>')
def confirm_email(token):
    email = None
    try:
        email = s.loads(token, salt='email-confirm', max_age=600)
    except SignatureExpired:
        flash("您的確認連結已過期。")
        return redirect(url_for('resend_confirmation'))
    except BadSignature:
        flash("確認連結無效。")
        return redirect(url_for('signup'))
    with sqlite3.connect('account.db') as conn:
        cursor = conn.cursor()
        # 檢查電子郵件是否已確認
        cursor.execute("SELECT confirmed FROM lccnet WHERE email=?", (email,))
        user = cursor.fetchone()
        if user and user[0]:
            flash("以確認")
            return redirect(url_for('login'))
        # 更新用戶的確認狀態
        cursor.execute("UPDATE lccnet SET confirmed = 1 WHERE email=?", (email,))
        conn.commit()
    flash("已通過驗證")
    return redirect(url_for('login'))

@app.route('/logout', methods=['POST'])
def logout():
    # 登出帳戶
    session.clear()
    return redirect(url_for('login'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_info' in session:
        username = session['user_info']['username']
        with sqlite3.connect('account.db') as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM lccnet WHERE user=?", (username,))
            cursor.execute("DELETE FROM email_tokens WHERE user=?", (username,))
            conn.commit()
        session.clear()  
        flash('您的帳戶已成功刪除。')
    else:
        flash('你沒有登入。')
    return redirect(url_for('login'))

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 8000))
        app.run(host='0.0.0.0', debug=True, port=port, use_reloader=False)  # use_reloader=False是重要的
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        # 當 Flask 應用退出時，關閉調度器
        scheduler.shutdown()