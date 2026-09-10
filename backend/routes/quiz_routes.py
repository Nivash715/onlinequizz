import json
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from backend.models import question_model, result_model
from backend.services import quiz_service

bp = Blueprint('quiz', __name__)


@bp.get('/')
def index():
    questions = question_model.get_all()
    return render_template('index.html', question_count=len(questions),
                           category_count=len({q['category'] for q in questions}),
                           stats=result_model.stats(), results=result_model.recent())


@bp.route('/quiz/start', methods=['GET', 'POST'])
def start():
    count = len(question_model.get_all())
    if request.method == 'POST':
        name = request.form.get('user_name', '').strip()
        if not name or len(name) > 80:
            flash('Enter your name using 1 to 80 characters.', 'error')
        else:
            try:
                session['attempt_token'] = quiz_service.start_attempt(name)
                return redirect(url_for('quiz.take'))
            except ValueError as error:
                flash(str(error), 'error')
        return render_template('quiz/start.html', count=count, name=name), 400
    return render_template('quiz/start.html', count=count, name='')


def current_attempt():
    return result_model.get_attempt(session.get('attempt_token', ''))


@bp.get('/quiz')
def take():
    attempt = current_attempt()
    if not attempt:
        flash('Enter your name to start a quiz.', 'info')
        return redirect(url_for('quiz.start'))
    if attempt['result_id']:
        return redirect(url_for('quiz.result', result_id=attempt['result_id']))
    return render_template('quiz/quiz.html', attempt=attempt,
                           questions=json.loads(attempt['questions_json']), answers={})


@bp.post('/quiz/submit')
def submit():
    attempt = current_attempt()
    if not attempt:
        flash('Please start a quiz before submitting answers.', 'error')
        return redirect(url_for('quiz.start'))
    if request.form.get('attempt_token') != attempt['token']:
        flash('This form belongs to an older quiz. Please use your current quiz.', 'error')
        return redirect(url_for('quiz.take'))
    try:
        result_id = quiz_service.submit_attempt(attempt, request.form)
    except ValueError as error:
        flash(str(error), 'error')
        return render_template('quiz/quiz.html', attempt=attempt,
                               questions=json.loads(attempt['questions_json']),
                               answers=request.form), 400
    return redirect(url_for('quiz.result', result_id=result_id))


@bp.get('/quiz/result/<int:result_id>')
def result(result_id):
    saved = result_model.get_by_id(result_id)
    if saved is None:
        abort(404)
    return render_template('quiz/result.html', result=saved)
