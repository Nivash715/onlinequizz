"""End-to-end HTTP tests using an isolated temporary SQLite database."""
import tempfile
import os
from unittest.mock import patch
import unittest
from pathlib import Path
from backend.app import create_app
from backend.database.db import get_db
from backend.services.quiz_service import calculate_score


class QuizSystemTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'test-only',
                               'DATABASE': str(Path(self.directory.name) / 'quiz.db')})
        self.client = self.app.test_client()
        self.client.get('/')
        self.question = dict(question='What is 2 + 2?', option_a='3', option_b='4',
                             option_c='5', option_d='6', correct_answer='B',
                             category='Mathematics', difficulty='Easy')

    def tearDown(self):
        self.directory.cleanup()

    def post(self, path, data=None, follow=True):
        with self.client.session_transaction() as session:
            token = session['csrf_token']
        return self.client.post(path, data={**(data or {}), 'csrf_token': token},
                                follow_redirects=follow)

    def add_question(self, **changes):
        response = self.post('/questions/create', {**self.question, **changes}, follow=False)
        self.assertEqual(response.status_code, 302)
        return int(response.location.rsplit('/', 1)[1])

    def attempt_data(self):
        with self.client.session_transaction() as session:
            return {'attempt_token': session['attempt_token']}

    def test_health_and_cache_policy(self):
        client = self.app.test_client()
        response = client.get('/healthz')
        self.assertEqual(response.json, {'status': 'ok'})
        self.assertNotIn('Set-Cookie', response.headers)
        for path in ['/', '/questions', '/missing-page']:
            self.assertEqual(client.get(path).headers['Cache-Control'], 'private, no-store')
        with self.app.test_client().get('/static/css/style.css') as response:
            self.assertNotIn('Set-Cookie', response.headers)

    def test_production_configuration_and_session_restart(self):
        with patch.dict(os.environ, {'APP_ENV': 'production', 'SECRET_KEY': '',
                                     'DATABASE_PATH': self.app.config['DATABASE']}):
            with self.assertRaisesRegex(RuntimeError, 'SECRET_KEY'):
                create_app()
        with patch.dict(os.environ, {'APP_ENV': 'production', 'SECRET_KEY': 'a' * 64,
                                     'DATABASE_PATH': ''}):
            with self.assertRaisesRegex(RuntimeError, 'DATABASE_PATH'):
                create_app()
        with patch.dict(os.environ, {'APP_ENV': 'production', 'SECRET_KEY': 'a' * 64,
                                     'DATABASE_PATH': self.app.config['DATABASE']}):
            first = create_app().test_client()
            response = first.get('/', base_url='https://quiz.example')
            self.assertIn('Secure;', response.headers['Set-Cookie'])
            cookie = first.get_cookie('session', domain='quiz.example')
            second = create_app().test_client()
            second.set_cookie('session', cookie.value, domain='quiz.example')
            with first.session_transaction(base_url='https://quiz.example') as session:
                token = session['csrf_token']
            response = second.post('/questions/create',
                                   data={**self.question, 'csrf_token': token},
                                   base_url='https://quiz.example')
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.location.startswith('/questions/'))

    def test_full_crud_and_quiz_flow(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        question_id = self.add_question()
        for path in ['/questions', f'/questions/{question_id}', f'/questions/{question_id}/edit']:
            self.assertEqual(self.client.get(path).status_code, 200)
        response = self.post(f'/questions/{question_id}/edit',
                             {**self.question, 'question': 'What is two plus two?'})
        self.assertIn(b'Question updated successfully', response.data)
        self.assertIn(b'What is two plus two?', response.data)
        doomed = self.add_question(question='Delete this question')
        self.assertIn(b'Delete this question?', self.client.get(f'/questions/{doomed}/delete').data)
        self.assertEqual(self.client.get(f'/questions/{doomed}').status_code, 200)
        self.assertIn(b'Question deleted successfully', self.post(f'/questions/{doomed}/delete').data)
        self.assertEqual(self.client.get(f'/questions/{doomed}').status_code, 404)
        second = self.add_question(question='What is 3 + 1?')
        self.assertEqual(self.post('/quiz/start', {'user_name': 'Alex'}).status_code, 200)
        payload = {**self.attempt_data(), f'answer_{question_id}': 'B', f'answer_{second}': 'A'}
        result = self.post('/quiz/submit', payload)
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'Quiz Completed', result.data)
        self.assertIn(b'1 / 2 points', result.data)
        self.assertIn(b'50<small>%', result.data)
        with self.app.app_context():
            saved = get_db().execute('SELECT * FROM results').fetchone()
            self.assertEqual((saved['user_name'], saved['score'], saved['percentage']), ('Alex', 1, 50))
        self.assertEqual(self.post('/quiz/submit', payload).status_code, 200)
        with self.app.app_context():
            self.assertEqual(get_db().execute('SELECT COUNT(*) FROM results').fetchone()[0], 1)

    def test_validation_and_security(self):
        self.assertEqual(self.post('/questions/create', {}).status_code, 400)
        self.assertEqual(self.post('/questions/create', {**self.question, 'difficulty': 'Impossible'}).status_code, 400)
        self.assertEqual(self.post('/questions/create', {**self.question, 'correct_answer': 'Z'}).status_code, 400)
        self.assertEqual(self.client.post('/questions/create', data=self.question).status_code, 400)
        self.assertEqual(self.client.post('/questions/create', data={'csrf_token': 'Ã©'}).status_code, 400)
        self.assertEqual(self.post('/quiz/start', {'user_name': ' '}).status_code, 400)
        self.assertEqual(self.post('/quiz/start', {'user_name': 'x' * 81}).status_code, 400)
        for path in ['/questions/999', '/questions/999/edit', '/questions/999/delete',
                     '/questions/not-an-id', '/quiz/result/999']:
            self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.get('/quiz/submit').status_code, 405)
        self.assertEqual(self.post('/questions/999/delete').status_code, 404)
        question_id = self.add_question(question='<script>alert(1)</script>')
        response = self.client.get(f'/questions/{question_id}')
        self.assertIn(b'&lt;script&gt;', response.data)
        self.assertNotIn(b'<script>alert', response.data)

    def test_empty_quiz_and_missing_session(self):
        self.assertEqual(calculate_score([], {}), (0, 0, 0.0))
        self.assertIn(b'no questions yet', self.client.get('/quiz/start').data)
        self.assertEqual(self.post('/quiz/start', {'user_name': 'Alex'}).status_code, 400)
        self.assertEqual(self.client.get('/quiz').status_code, 302)
        self.assertEqual(self.post('/quiz/submit', follow=False).status_code, 302)
        with self.app.app_context():
            self.assertEqual(get_db().execute('SELECT COUNT(*) FROM results').fetchone()[0], 0)

    def test_answers_are_required_and_ids_are_validated(self):
        question_id = self.add_question()
        self.post('/quiz/start', {'user_name': 'Alex'})
        base = self.attempt_data()
        for answers in [{}, {f'answer_{question_id}': 'Z'}, {f'answer_{question_id}': ''},
                        {f'answer_{question_id}': ['A', 'B']},
                        {f'answer_{question_id}': 'B', 'answer_999': 'A'}]:
            self.assertEqual(self.post('/quiz/submit', {**base, **answers}).status_code, 400)
        with self.app.app_context():
            self.assertEqual(get_db().execute('SELECT COUNT(*) FROM results').fetchone()[0], 0)
        self.assertIn(b'100<small>%', self.post('/quiz/submit', {**base, f'answer_{question_id}': 'B'}).data)

    def test_snapshot_survives_edits_and_deletion(self):
        question_id = self.add_question()
        self.post('/quiz/start', {'user_name': 'Snapshot'})
        payload = {**self.attempt_data(), f'answer_{question_id}': 'B'}
        self.post(f'/questions/{question_id}/edit', {**self.question, 'correct_answer': 'A'})
        self.post(f'/questions/{question_id}/delete')
        self.assertIn(b'What is 2 + 2?', self.client.get('/quiz').data)
        self.assertIn(b'100<small>%', self.post('/quiz/submit', payload).data)

    def test_old_tab_cannot_submit_new_attempt(self):
        question_id = self.add_question()
        self.post('/quiz/start', {'user_name': 'First'})
        old = self.attempt_data()
        self.post('/quiz/start', {'user_name': 'Second'})
        response = self.post('/quiz/submit', {**old, f'answer_{question_id}': 'B'})
        self.assertIn(b'older quiz', response.data)
        with self.app.app_context():
            self.assertEqual(get_db().execute('SELECT COUNT(*) FROM results').fetchone()[0], 0)

    def test_search_and_database_persistence(self):
        self.add_question()
        self.assertIn(b'What is 2 + 2?', self.client.get('/questions?q=math&difficulty=Easy').data)
        self.assertIn(b'No matching questions', self.client.get('/questions?q=missing').data)
        app_again = create_app({'TESTING': True, 'DATABASE': self.app.config['DATABASE']})
        self.assertIn(b'What is 2 + 2?', app_again.test_client().get('/questions').data)


if __name__ == '__main__':
    unittest.main()
