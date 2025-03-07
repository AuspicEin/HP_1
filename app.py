from flask import Flask, request, redirect, render_template, send_file, url_for
import sqlite3
import random
import string
import qrcode
from io import BytesIO
import os

app = Flask(__name__)

# データベース初期化
def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS urls (short TEXT PRIMARY KEY, long TEXT)")
init_db()

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

            # データベースに保存
            try:
                cur.execute("INSERT INTO urls (short, long) VALUES (?, ?)", (short_code, long_url))
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

# アプリ起動
port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=True)
