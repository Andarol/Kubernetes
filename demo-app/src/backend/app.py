import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

VERSION = os.getenv("APP_VERSION", "1.0.0")

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "demo-app-db"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "appdb"),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASSWORD", "apppass"),
    )

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            done BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route("/api/health")
def health():
    try:
        conn = get_db()
        conn.close()
        return jsonify({"status": "ok", "version": VERSION})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/version")
def version():
    return jsonify({"version": VERSION})

@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, title, done, created_at FROM tasks ORDER BY id DESC")
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{**t, "created_at": str(t["created_at"])} for t in tasks])

@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    if not data or not data.get("title"):
        return jsonify({"error": "title is required"}), 400
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "INSERT INTO tasks (title) VALUES (%s) RETURNING id, title, done, created_at",
        (data["title"],),
    )
    task = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({**task, "created_at": str(task["created_at"])}), 201

@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def toggle_task(task_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "UPDATE tasks SET done = NOT done WHERE id = %s RETURNING id, title, done, created_at",
        (task_id,),
    )
    task = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if not task:
        return jsonify({"error": "not found"}), 404
    return jsonify({**task, "created_at": str(task["created_at"])})

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return "", 204

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
