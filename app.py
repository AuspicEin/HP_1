from flask import Flask, request, redirect, render_template, send_file, url_for, jsonify
import sqlite3
import random
import string
import qrcode
from io import BytesIO
import os
import datetime

app = Flask(__name__)

# データベース初期化
def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                short TEXT PRIMARY KEY,
                long TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

init_db()

# 既存のデータベースを更新（created_at カラムを追加）
def update_db():
    with sqlite3.connect("database.db") as conn:
        try:
            conn.execute("ALTER TABLE urls ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except sqlite3.OperationalError:
            pass  # すでにカラムがある場合はスキップ

update_db()

# ランダムな短縮コード生成
def generate_short_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# ホームページ（トップページ）
@app.route("/")
def home():
    return render_template("index.html")

# URL短縮機能ページ
@app.route("/url-shortener", methods=["GET", "POST"])
def url_shortener():
    if request.method == "POST":
        long_url = request.form["long_url"]
        custom_code = request.form.get("custom_code", "").strip()

        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()

            # カスタムコードが指定されている場合、既存のものと衝突しないか確認
            if custom_code:
                cur.execute("SELECT short FROM urls WHERE short=?", (custom_code,))
                if cur.fetchone():
                    return "このカスタムコードは既に使用されています。別のコードを選んでください。", 400
                short_code = custom_code
            else:
                short_code = generate_short_code()
                while True:
                    cur.execute("SELECT short FROM urls WHERE short=?", (short_code,))
                    if not cur.fetchone():
                        break
                    short_code = generate_short_code()

            # データベースに保存（作成日時 included）
            created_at = datetime.datetime.now()
            try:
                cur.execute("INSERT INTO urls (short, long, created_at) VALUES (?, ?, ?)", 
                            (short_code, long_url, created_at))
                conn.commit()
            except sqlite3.IntegrityError:
                return "このカスタムコードは既に使用されています。", 400

        short_url = request.host_url + short_code
        qr_url = request.host_url + "qrcode/" + short_code

        return render_template("shortener.html", short_url=short_url, qr_url=qr_url)

    return render_template("shortener.html")

# 短縮URLリダイレクト
@app.route("/<short_code>")
def redirect_to_original(short_code):
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT long FROM urls WHERE short=?", (short_code,))
        result = cur.fetchone()
        if result:
            return redirect(result[0])
    return "URL not found", 404

# QRコード生成
@app.route("/qrcode/<short_code>")
def generate_qrcode(short_code):
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT long FROM urls WHERE short=?", (short_code,))
        result = cur.fetchone()
        if not result:
            return "URL not found", 404

    short_url = request.host_url + short_code
    qr = qrcode.make(short_url)

    img_io = BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png', as_attachment=False)

# 履歴取得API
@app.route("/history")
def get_history():
    limit = request.args.get("limit", default=5, type=int)
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT short, long, created_at FROM urls ORDER BY created_at DESC LIMIT ?", (limit,))
        data = cur.fetchall()
    return jsonify([{"short": row[0], "long": row[1], "created_at": row[2]} for row in data])

# ブログ機能
@app.route("/blog", methods=["GET"])
def blog():
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, title, created_at FROM blog_posts ORDER BY created_at DESC")
        posts = cur.fetchall()
    return render_template("blog.html", posts=posts)

@app.route("/blog/post", methods=["POST"])
def post_blog():
    title = request.form["title"]
    content = request.form["content"]
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO blog_posts (title, content) VALUES (?, ?)", (title, content))
        conn.commit()
    return redirect(url_for("blog"))

@app.route("/blog/<int:post_id>")
def view_blog(post_id):
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT title, content, created_at FROM blog_posts WHERE id = ?", (post_id,))
        post = cur.fetchone()
    if not post:
        return "記事が見つかりません", 404
    return render_template("blog_post.html", title=post[0], content=post[1], created_at=post[2])

# アプリ起動
port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=True)
