import sqlite3
from pathlib import Path
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(error=None):
    connection = g.pop('db', None)
    if connection is not None:
        connection.close()


def init_db():
    Path(current_app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)
    get_db().executescript('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL, option_b TEXT NOT NULL,
            option_c TEXT NOT NULL, option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL CHECK(correct_answer IN ('A','B','C','D')),
            category TEXT NOT NULL,
            difficulty TEXT NOT NULL CHECK(difficulty IN ('Easy','Medium','Hard')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            score INTEGER NOT NULL CHECK(score >= 0),
            total_questions INTEGER NOT NULL CHECK(total_questions > 0),
            percentage REAL NOT NULL CHECK(percentage BETWEEN 0 AND 100),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK(score <= total_questions)
        );
        CREATE TABLE IF NOT EXISTS attempts (
            token TEXT PRIMARY KEY,
            user_name TEXT NOT NULL,
            questions_json TEXT NOT NULL,
            result_id INTEGER REFERENCES results(id),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    ''')
