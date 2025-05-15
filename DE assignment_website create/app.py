import os
import sqlite3
import pandas as pd
from datetime import datetime
from random import randint
import plotly.express as px
import json
from flask import Flask, render_template, session, request

# --- App Setup ---
app = Flask(__name__)
app.secret_key = 'your-fixed-secret-key'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'cleaned_data.db')  # Unified DB path

# --- Database Connection ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Page View Table Setup ---
def initialize_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS PageView (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            page TEXT NOT NULL,
            time_spent REAL,
            start_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

# --- Session Management ---
@app.before_request
def assign_session_id():
    if "id" not in session:
        session["id"] = randint(1_000_000, 9_999_999)
        session["start_time"] = datetime.now()
        session["previous_path"] = request.path

def get_session_info():
    if all(k in session for k in ("id", "start_time", "previous_path")):
        return session["id"], session["start_time"], session["previous_path"]
    return None

# --- Logging ---
def log_page_view(session_id, page, time_spent):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO PageView (session_id, page, time_spent, start_time) VALUES (?, ?, ?, ?)",
            (session_id, page, time_spent, str(datetime.now()))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging page view: {e}")

def log_data():
    session_info = get_session_info()
    if session_info:
        session_id, start_time, previous_path = session_info
        try:
            time_spent = (datetime.now() - start_time).total_seconds()
        except:
            time_spent = 0
        log_page_view(session_id, previous_path, time_spent)

@app.after_request
def track_time(response):
    path_map = {
        "/": "Home",
        "/Access_data": "Access_data",
        "/Introduction": "Introduction",
        "/Contact": "Contact"
    }
    if request.path in path_map:
        log_data()
        session["start_time"] = datetime.now()
        session["previous_path"] = path_map[request.path]
    return response

# --- Map Generation ---
def make_continent_choropleth():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT continent, emission_rate, quarter FROM emissions", conn)
    conn.close()

    # Filter only for the latest quarter, e.g. 2024Q2
    latest_quarter = df['quarter'].max()
    df_latest = df[df['quarter'] == latest_quarter]

    fig = px.choropleth(
        df_latest,
        locations="continent",
        locationmode="continent names",
        color="emission_rate",
        projection="natural earth",
        color_continuous_scale="OrRd",
        title=f"CO₂ Emissions by Continent – {latest_quarter}",
        labels={"emission_rate": "MtCO₂e"}
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})
    return fig.to_json()

# --- Routes ---
@app.route("/")
def home():
    return render_template("Website.html")

@app.route("/Access_data")
def access_data():
    choropleth_json = make_continent_choropleth()
    return render_template(
        "access_data.html",
        choropleth_json=choropleth_json,
        barchart="barchart.png",
        heatmap="heatmap.png"
    )

@app.route("/Introduction")
def introduction():
    return render_template("Introduction.html")

@app.route("/Contact")
def contact():
    return render_template("contact.html")

# --- Main ---
if __name__ == "__main__":
    initialize_db()
    app.run(debug=True, port=5000)
