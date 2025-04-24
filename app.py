from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import itertools

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route("/", methods=["GET"])
def home():
    return redirect(url_for('predict'))

@app.route("/predict", methods=["GET", "POST"])
def predict():
    if not session.get('logged_in'):
        return render_template("index.html", logged_in=False)

    # CSV読み込み
    input_df = pd.read_csv("競艇AI予算サンプルデータ.csv")
    
    # ★ 列名の空白削除
    input_df.columns = input_df.columns.str.strip()

    # 処理ロジック（着順、3連単候補）
    input_df['艇'] = input_df['枠番'].astype(int)
    prob_df = input_df[['艇', '着順']].sort_values(by='着順', ascending=True)
    combo = list(itertools.permutations(prob_df['艇'].tolist(), 3))
    combo_str = ', '.join(['-'.join(map(str, c)) for c in combo])
    input_df['3連単候補'] = combo_str if len(input_df) == 6 else 'N/A'

    # 表示用HTMLテーブル作成
    table_html = input_df[['枠番', '勝率', 'ST平均', '展示タイム', '風速', '着順', 'オッズ']].to_html(index=False)

    return render_template("index.html", logged_in=True, table=table_html)

@app.route("/login", methods=["POST"])
def login():
    if request.form['password'] == 'password123':
        session['logged_in'] = True
    return redirect(url_for('predict'))

@app.route("/logout", methods=["POST"])
def logout():
    session['logged_in'] = False
    return redirect(url_for('predict'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", logged_in=False)
