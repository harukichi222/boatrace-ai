
from flask import Flask, request, render_template, redirect, url_for, session
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
import os
import itertools
import numpy as np

app = Flask(__name__)
app.secret_key = 'secret_key_for_session'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

df = pd.read_csv("競艇AI予算サンプルデータ.csv")
df['1着か'] = (df['着順'] == 1).astype(int)
features = ['枠番', '勝率', 'ST平均', '展示タイム', '風速']
X = df[features]
y = df['1着か']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = LGBMClassifier()
model.fit(X_train, y_train)

@app.route("/", methods=["GET", "POST"])
def predict():
    table_html = None
    logged_in = session.get('logged_in', False)
    if not logged_in:
        return render_template("index.html", logged_in=False, table=None)

    if request.method == "POST":
        file = request.files['file']
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            input_df = pd.read_csv(filepath)
            if not all(f in input_df.columns for f in features + ['オッズ']):
                return render_template("index.html", logged_in=True, table="<p>必要なカラム（+オッズ）が含まれていません</p>")

            preds = model.predict_proba(input_df[features])[:, 1]
            input_df['1着確率（％）'] = (preds * 100).round(1)
            input_df['荒れ度'] = abs(preds - 0.5).round(2)
            input_df['期待値'] = (input_df['オッズ'] * preds).round(2)

            input_df['艇'] = input_df['枠番'].astype(int)
            prob_df = input_df[['艇', '1着確率（％）']].sort_values(by='1着確率（％）', ascending=False).head(3)
            combo = list(itertools.permutations(prob_df['艇'].tolist(), 3))
            combo_str = ', '.join(['-'.join(map(str, c)) for c in combo])
            input_df['3連単候補'] = combo_str if len(input_df) == 6 else 'N/A'

            table_html = input_df[['枠番', '勝率', 'ST平均', '展示タイム', '風速', 'オッズ', '1着確率（％）', '荒れ度', '期待値', '3連単候補']].to_html(index=False)

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
    return redirect(url_for('predict'))
