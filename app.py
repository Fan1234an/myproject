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
from authlib.integrations.flask_client import OAuth
print('LINE_CHANNEL_ID:', os.environ.get('LINE_CHANNEL_ID'))
print('LINE_CHANNEL_SECRET:', os.environ.get('LINE_CHANNEL_SECRET'))
print('LINE_CALLBACK_URL:', os.environ.get('LINE_CALLBACK_URL'))
print(os.environ)

app = Flask(__name__)
app.config['PREFERRED_URL_SCHEME'] = 'https'
oauth = OAuth(app)
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

oauth.register(
    'line',
    client_id=os.environ.get('LINE_CHANNEL_ID'),
    client_secret=os.environ.get('LINE_CHANNEL_SECRET'),
    authorize_url='https://access.line.me/oauth2/v2.1/authorize',
    authorize_params=None,
    access_token_url='https://api.line.me/oauth2/v2.1/token',
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri=os.environ.get('LINE_CALLBACK_URL'),
    client_kwargs={'scope': 'openid profile email'},
)

def send_email(to, subject, body):
    msg = Message(subject, recipients=[to], body=body)
    mail.send(msg)

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
        "user" TEXT NOT NULL UNIQUE,
        passwd TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        confirmed INTEGER DEFAULT 0
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_tokens (
        id SERIAL PRIMARY KEY,
        "user" TEXT NOT NULL,
        token TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_activities (
        id SERIAL PRIMARY KEY,
        forum TEXT NOT NULL,
        tags TEXT NOT NULL,
        "user" TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        image_data BYTEA,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS animation_activities (
        id SERIAL PRIMARY KEY,
        forum TEXT NOT NULL,
        tags TEXT NOT NULL,
        "user" TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        image_data BYTEA,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS message_activities (
        id SERIAL PRIMARY KEY,
        tags TEXT NOT NULL,
        "user" TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id SERIAL PRIMARY KEY,
        title TEXT,
        url TEXT,
        score TEXT,
        popularity TEXT,
        data BYTEA
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS acg_info (
        id SERIAL PRIMARY KEY,
        title TEXT,
        url TEXT,
        score TEXT,
        popularity TEXT,
        image BYTEA
    )
    ''')
    conn.commit()
    conn.close()
initialize_db()

def job_function():
    with app.app_context():
        main()
        maina()
scheduler = BackgroundScheduler()
scheduler.add_job(job_function, 'interval', days=7)
scheduler.start()
job_function() # 開發測試用

def get_db_connection():
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
    return conn

def execute_query(query):
    results = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
    except Exception as e:
        print(f"發生錯誤： {e}")
    finally:
        cursor.close()
        conn.close()
    return results

@app.route('/login/line')
def login_line():
    # 重定向到LINE授權頁面
    redirect_uri = url_for('authorize', _external=True)
    print("Redirect URI:", redirect_uri)
    return oauth.line.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    # 獲取授權token
    token = oauth.line.authorize_access_token()
    # 使用token獲取用戶資訊
    user_info = oauth.line.parse_id_token(token)
    # 假设user_info字典中有line_id, name和email
    line_id = user_info.get('sub')  # LINE用户的唯一标识符
    name = user_info.get('name')
    email = user_info.get('email')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM lccnet WHERE line_id = %s', (line_id,))
    user = cursor.fetchone()

    if user is None:
        # 用户不存在，插入新记录
        cursor.execute('INSERT INTO lccnet (user, passwd, name, email, line_id, confirmed) VALUES (%s, %s, %s, %s, %s, %s)',
                       (line_id, 'default_password', name, email, line_id, 1))
    else:
        # 用户已存在，更新记录
        cursor.execute('UPDATE lccnet SET name = %s, email = %s WHERE line_id = %s',
                       (name, email, line_id))

    conn.commit()
    cursor.close()
    conn.close()

    # 将用户信息保存到session
    session['user_info'] = {
        'line_id': line_id,
        'name': name,
        'email': email
    }

    # 然后重定向到主页或其他页面
    return redirect(url_for('home'))

@app.route("/post")
def newpost():
    conn=get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, data FROM images ORDER BY id DESC")
    images_info = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('post.html',images_info=images_info)

@app.route("/post2")
def newpost2():
    conn=get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, image FROM acg_info ORDER BY id DESC")
    images_info1 = cursor.fetchall()
    cursor.close()
    conn.close()
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
            conn=get_db_connection()
            cursor = conn.cursor()
            # 根据图片ID查询数据
            cursor.execute("SELECT data FROM images WHERE id = %s", (forum,))
            image_data = cursor.fetchone()
            cursor.close()
            conn.close()
            if image_data:
                # 将图片数据和其他表单数据一起插入 user_activities 表中
                conn=get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO user_activities (forum, tags, \"user\", title, content, image_data) VALUES (%s, %s, %s, %s, %s, %s)", 
                                (forum, tags, name, title, content, image_data[0]))
                conn.commit()
                cursor.close()
                conn.close()
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
            conn=get_db_connection()
            cursor = conn.cursor()
            # 根据图片ID查询数据
            cursor.execute("SELECT image FROM acg_info WHERE id = %s", (forum,))
            image_data = cursor.fetchone()
            cursor.close()
            conn.close()
            if image_data:
                # 将图片数据和其他表单数据一起插入 user_activities 表中
                conn=get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO animation_activities (forum, tags, \"user\", title, content, image_data) VALUES (%s, %s, %s, %s, %s, %s)", 
                                (forum, tags, name, title, content, image_data[0]))
                conn.commit()
                cursor.close()
                conn.close()
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
            conn=get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO message_activities ( tags, \"user\", title, content) VALUES ( %s, %s, %s, %s)", ( tags, name, title, content))
            conn.commit()
            cursor.close()
            conn.close()
        flash('Post submitted successfully!')
        return redirect(url_for('home'))

# 刪除貼文
@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    conn=get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_activities WHERE id = %s", (post_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("貼文刪除成功！")
    return redirect(url_for('home'))
@app.route('/delete_post1/<int:post_id>', methods=['POST'])
def delete_post1(post_id):
    conn=get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM animation_activities WHERE id = %s", (post_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("貼文刪除成功！")
    return redirect(url_for('home'))
@app.route('/delete_post2/<int:post_id>', methods=['POST'])
def delete_post2(post_id):
    conn=get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM message_activities WHERE id = %s", (post_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("貼文刪除成功！")
    return redirect(url_for('home'))

# 首頁
@app.route("/home")
def home():
    if "user_info" in session:
        user_info = session['user_info']
        
        # 執行查詢並處理結果
        results = execute_query("SELECT id, forum, tags, title, \"user\", content, image_data FROM user_activities ORDER BY id DESC")
        posts = [
            {
                'id': row[0],
                'forum': row[1],
                'tags': row[2],
                'title': row[3],
                'user': row[4],
                'content': row[5],
                'image_data': base64.b64encode(row[6]).decode('ascii') if row[6] else None
            } for row in results
        ] if results is not None else []

        results1 = execute_query("SELECT id, forum, tags, title, \"user\", content, image_data FROM animation_activities ORDER BY id DESC")
        posts1 = [
            {
                'id': row[0],
                'forum': row[1],
                'tags': row[2],
                'title': row[3],
                'user': row[4],
                'content': row[5],
                'image_data': base64.b64encode(row[6]).decode('ascii') if row[6] else None
            } for row in results1
        ] if results1 is not None else []

        results2 = execute_query("SELECT id, tags, title, \"user\", content FROM message_activities ORDER BY id DESC")
        posts2 = [
            {
                'id': row[0],
                'tags': row[1],
                'title': row[2],
                'user': row[3],
                'content': row[4],
            } for row in results2
        ] if results2 is not None else []

        games_results = execute_query("SELECT title, url, score, popularity, data FROM images ORDER BY id DESC")
        games = [
            {
                'title': row[0],
                'url': row[1],
                'score': row[2],
                'popularity': row[3],
                'data': base64.b64encode(row[4]).decode('ascii') if row[4] else None
            } for row in games_results
        ] if games_results is not None else []

        animations_results = execute_query("SELECT title, url, score, popularity, image FROM acg_info ORDER BY id DESC")
        animations = [
            {
                'title': row[0],
                'url': row[1],
                'score': row[2],
                'popularity': row[3],
                'image': base64.b64encode(row[4]).decode('ascii') if row[4] else None
            } for row in animations_results
        ] if animations_results is not None else []

        # 使用處理好的數據渲染模板
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
        
        conn=get_db_connection()
        cursor = conn.cursor()
        # 從資料庫檢索密碼、姓名、電子郵件和確認狀態
        cursor.execute("SELECT passwd, name, email, confirmed FROM lccnet WHERE \"user\"=%s", (user,))
        data = cursor.fetchone()
        cursor.close()
        conn.close()
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
            
            conn=get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO lccnet (\"user\", passwd, name, email) VALUES (%s, %s, %s, %s)", (user, passwd, name, email))
            cursor.execute("INSERT INTO email_tokens (\"user\", token) VALUES (%s, %s)", (user, token))
            conn.commit()
            cursor.close()
            conn.close()
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
    conn=get_db_connection()
    cursor = conn.cursor()
        # 檢查電子郵件是否已確認
    cursor.execute("SELECT confirmed FROM lccnet WHERE email=%s", (email,))
    user = cursor.fetchone()
    if user and user[0]:
        flash("以確認")
        return redirect(url_for('login'))
        # 更新用戶的確認狀態  
    cursor.execute("UPDATE lccnet SET confirmed = 1 WHERE email=%s", (email,))
    conn.commit()
    cursor.close()
    conn.close()
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
        conn=get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lccnet WHERE \"user\"=%s", (username,))
        cursor.execute("DELETE FROM email_tokens WHERE \"user\"=%s", (username,))
        conn.commit()
        cursor.close()
        conn.close()
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
        pass
        # scheduler.shutdown()