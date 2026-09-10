from backend.database.db import get_db


def get_by_id(result_id):
    return get_db().execute('SELECT * FROM results WHERE id = ?', (result_id,)).fetchone()


def recent(limit=5):
    return get_db().execute('SELECT * FROM results ORDER BY id DESC LIMIT ?', (limit,)).fetchall()


def stats():
    return get_db().execute('''SELECT COUNT(*) AS total,
        COALESCE(ROUND(AVG(percentage), 1), 0) AS average FROM results''').fetchone()


def create_attempt(token, user_name, questions_json):
    db = get_db()
    with db:
        db.execute('INSERT INTO attempts (token, user_name, questions_json) VALUES (?, ?, ?)',
                   (token, user_name, questions_json))


def get_attempt(token):
    return get_db().execute('SELECT * FROM attempts WHERE token = ?', (token,)).fetchone()


def save_for_attempt(token, score, total, percentage):
    # A transaction makes repeat submissions return the same saved result.
    db = get_db()
    with db:
        db.execute('BEGIN IMMEDIATE')
        attempt = get_attempt(token)
        if attempt['result_id'] is not None:
            return attempt['result_id']
        cursor = db.execute('''INSERT INTO results
            (user_name, score, total_questions, percentage) VALUES (?, ?, ?, ?)''',
            (attempt['user_name'], score, total, percentage))
        db.execute('UPDATE attempts SET result_id = ? WHERE token = ?', (cursor.lastrowid, token))
        return cursor.lastrowid
