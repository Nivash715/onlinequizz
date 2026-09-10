from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from backend.models import question_model

bp = Blueprint('questions', __name__, url_prefix='/questions')


def find_question(question_id):
    question = question_model.get_by_id(question_id)
    if question is None:
        abort(404)
    return question


def validate(form):
    data = {field: form.get(field, '').strip() for field in question_model.FIELDS}
    errors = []
    for field in question_model.FIELDS:
        if not data[field]:
            errors.append(f'{field.replace("_", " ").capitalize()} is required.')
        elif len(data[field]) > (2000 if field == 'question' else 300):
            errors.append(f'{field.replace("_", " ").capitalize()} is too long.')
    if data['correct_answer'] not in ('A', 'B', 'C', 'D'):
        errors.append('Correct answer must be A, B, C, or D.')
    if data['difficulty'] not in ('Easy', 'Medium', 'Hard'):
        errors.append('Difficulty must be Easy, Medium, or Hard.')
    return data, errors


@bp.get('')
def list_questions():
    questions = question_model.get_all()
    query = request.args.get('q', '').strip()
    difficulty = request.args.get('difficulty', '')
    filtered = [q for q in questions if
                (not query or query.casefold() in (q['question'] + ' ' + q['category']).casefold())
                and (not difficulty or q['difficulty'] == difficulty)]
    return render_template('questions/list.html', questions=filtered, total=len(questions),
                           query=query, difficulty=difficulty)


@bp.route('/create', methods=['GET', 'POST'])
def create():
    data = {}
    if request.method == 'POST':
        data, errors = validate(request.form)
        if not errors:
            question_id = question_model.create(data)
            flash('Question added successfully.', 'success')
            return redirect(url_for('questions.view', question_id=question_id))
        for error in errors:
            flash(error, 'error')
        return render_template('questions/create.html', data=data), 400
    return render_template('questions/create.html', data=data)


@bp.get('/<int:question_id>')
def view(question_id):
    return render_template('questions/view.html', question=find_question(question_id))


@bp.route('/<int:question_id>/edit', methods=['GET', 'POST'])
def edit(question_id):
    data = dict(find_question(question_id))
    if request.method == 'POST':
        data, errors = validate(request.form)
        if not errors:
            question_model.update(question_id, data)
            flash('Question updated successfully.', 'success')
            return redirect(url_for('questions.view', question_id=question_id))
        for error in errors:
            flash(error, 'error')
        return render_template('questions/edit.html', data=data, question_id=question_id), 400
    return render_template('questions/edit.html', data=data, question_id=question_id)


@bp.route('/<int:question_id>/delete', methods=['GET', 'POST'])
def delete(question_id):
    question = find_question(question_id)
    if request.method == 'POST':
        question_model.delete(question_id)
        flash('Question deleted successfully.', 'success')
        return redirect(url_for('questions.list_questions'))
    # GET only displays confirmation; only POST mutates the database.
    return render_template('questions/delete.html', question=question)
