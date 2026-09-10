import json
import secrets
from backend.models import question_model, result_model


def start_attempt(user_name):
    questions = [dict(row) for row in question_model.get_all()]
    if not questions:
        raise ValueError('There are no questions yet. Add a question before starting a quiz.')
    token = secrets.token_urlsafe(32)
    result_model.create_attempt(token, user_name, json.dumps(questions))
    return token


def calculate_score(questions, answers):
    total = len(questions)
    score = sum(answers.get(f'answer_{q["id"]}') == q['correct_answer'] for q in questions)
    return score, total, round(score / total * 100, 2) if total else 0.0


def submit_attempt(attempt, form):
    if attempt['result_id'] is not None:
        return attempt['result_id']
    questions = json.loads(attempt['questions_json'])
    if not questions:
        raise ValueError('This quiz has no questions. Please start a new quiz.')
    allowed = {f'answer_{q["id"]}' for q in questions}
    if any(key.startswith('answer_') and key not in allowed for key in form):
        raise ValueError('An unknown question was submitted. Please review your answers.')
    if any(len(form.getlist(key)) != 1 or form.get(key) not in 'ABCD' or
           len(form.get(key, '')) != 1 for key in allowed):
        raise ValueError('Please select one valid answer for every question.')
    score, total, percentage = calculate_score(questions, form)
    return result_model.save_for_attempt(attempt['token'], score, total, percentage)
