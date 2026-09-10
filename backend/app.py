import secrets
from flask import Flask, abort, render_template, request, session
from backend.config import Config, ROOT, environment_config
from backend.database.db import close_db, get_db, init_db
from backend.routes import question_routes, quiz_routes


def create_app(test_config=None):
    app = Flask(__name__, template_folder=str(ROOT / 'frontend' / 'templates'),
                static_folder=str(ROOT / 'frontend' / 'static'))
    app.config.from_object(Config)
    app.config.update(environment_config())
    if test_config:
        app.config.update(test_config)
    app.teardown_appcontext(close_db)
    app.register_blueprint(question_routes.bp)
    app.register_blueprint(quiz_routes.bp)

    @app.get('/healthz')
    def health():
        get_db().execute('SELECT 1').fetchone()
        return {'status': 'ok'}

    @app.after_request
    def prevent_page_caching(response):
        # HTML contains participant data and per-session CSRF tokens.
        if request.endpoint != 'static':
            response.headers['Cache-Control'] = 'private, no-store'
        return response

    @app.before_request
    def protect_forms():
        if request.endpoint in ('health', 'static'):
            return
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        if request.method == 'POST':
            token = request.form.get('csrf_token', '')
            if not secrets.compare_digest(token.encode(), session['csrf_token'].encode()):
                abort(400, description='Your form expired. Reload the page and try again.')

    @app.context_processor
    def form_helpers():
        return {'csrf_token': lambda: session.get('csrf_token', '')}

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(405)
    @app.errorhandler(413)
    @app.errorhandler(500)
    def friendly_error(error):
        messages = {400: 'Your form could not be processed. Reload the page and try again.',
                    404: 'We could not find that page or record.',
                    405: 'That action is not available using this request method.',
                    413: 'That submission is too large. Please shorten your answers.',
                    500: 'Something went wrong. Please try again in a moment.'}
        return render_template('error.html', code=error.code, message=messages[error.code]), error.code

    with app.app_context():
        init_db()
    return app
