from backend.database.db import get_db

FIELDS = ('question', 'option_a', 'option_b', 'option_c', 'option_d',
          'correct_answer', 'category', 'difficulty')


def get_all():
    return get_db().execute('SELECT * FROM questions ORDER BY id').fetchall()


def get_by_id(question_id):
    return get_db().execute('SELECT * FROM questions WHERE id = ?', (question_id,)).fetchone()


def create(data):
    db = get_db()
    with db:
        cursor = db.execute('''INSERT INTO questions
            (question, option_a, option_b, option_c, option_d, correct_answer, category, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', tuple(data[field] for field in FIELDS))
    return cursor.lastrowid


def update(question_id, data):
    db = get_db()
    with db:
        db.execute('''UPDATE questions SET question=?, option_a=?, option_b=?,
            option_c=?, option_d=?, correct_answer=?, category=?, difficulty=? WHERE id=?''',
            tuple(data[field] for field in FIELDS) + (question_id,))


def delete(question_id):
    db = get_db()
    with db:
        db.execute('DELETE FROM questions WHERE id = ?', (question_id,))
