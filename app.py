from flask import Flask, request, redirect, render_template
import sqlite3
import random
import string

app = Flask(__name__)

# データベース初期化
def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS urls (short TEXT, long TEXT)")
init_db()

# ランダムな短縮コード生成
def generate_short_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# 短縮URL作成
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        long_url = request.form["long_url"]
        short_code = generate_short_code()

        with sqlite3.connect("database.db") as conn:
            conn.execute("INSERT INTO urls (short, long) VALUES (?, ?)", (short_code, long_url))

        short_url = request.host_url + short_code
        return render_template("index.html", short_url=short_url)

    return render_template("index.html")

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

import os

port = int(os.environ.get("PORT", 10000))  # 環境変数PORTを取得、なければ10000

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)

