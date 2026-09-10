# Simple Online Quiz Management System

A beginner-friendly local quiz application built with Python, Flask, Jinja2,
HTML, CSS, and Python's built-in SQLite support. The interface is branded
**Quizcraft**. No frontend framework, ORM, or JavaScript is required.

## Hosting on Vercel and Render

See [DEPLOYMENT.md](DEPLOYMENT.md) for the complete setup. Render runs Flask
on the free plan with temporary SQLite storage; Vercel serves static assets and proxies the
server-rendered pages and forms. Deployment configuration is included in
`render.yaml` and `frontend/vercel.json`. Free Render loses hosted questions
and results on restart, redeploy, or idle spin-down. Run locally with `python app.py`.

## Features

- Create, list, view, edit, and delete multiple-choice questions.
- Search questions and categories, and filter by difficulty.
- Confirm deletions on a separate page; only POST actually deletes a question.
- Enter a participant name and answer all available questions at your own pace.
- Calculate scores on the server and store results with UTC timestamps.
- View percentage, correct answers, wrong answers, and recent results.
- Server-side validation, flash messages, CSRF-protected forms, escaped output,
  parameterized SQL, and friendly error pages.
- Responsive dashboard, accessible labels, keyboard focus, and mobile layouts.
- Snapshot each quiz in SQLite so question edits/deletions during a quiz do not
  affect its content or scoring. Repeated submission saves only one result.

## Requirements

- Python 3.10 or newer (verified with Python 3.12).
- pip and a web browser.
- Flask; Gunicorn is installed on non-Windows systems for production hosting.

## Installation and running

Open a terminal in `online_quiz_system`, the folder containing `app.py`.

```powershell
cd "E:\Dvein Python\Example Projects\template5\online_quiz_system"
python -m venv venv
```

Activate the virtual environment in Windows Command Prompt:

```bat
venv\Scripts\activate
```

Or in Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source venv/bin/activate
```

Install and run:

```bash
python -m pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**. Stop the server with **Ctrl+C**.
If PowerShell blocks activation, you can use the virtual environment directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe app.py
```

The application creates `database/quiz.db` and its tables automatically. No
manual SQL commands or database server are needed. Existing data is preserved
on restart. The initial database is empty: choose **Manage Questions**, then
**Add New Question** to create the first question. The quiz start page explains
what to do when no questions are available.

Google Fonts optionally enhances the typography; system fonts are used when
offline. All quiz functionality, styling, and data storage work locally.

## Folder structure

```text
online_quiz_system/
├── backend/
│   ├── __init__.py
│   ├── app.py                  # App factory, configuration, CSRF, error pages
│   ├── config.py               # Paths and environment-based secret key
│   ├── models/
│   │   ├── __init__.py
│   │   ├── question_model.py   # Parameterized question CRUD queries
│   │   └── result_model.py     # Result and attempt persistence
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── question_routes.py  # Question HTTP handlers and form validation
│   │   └── quiz_routes.py      # Dashboard and quiz HTTP handlers
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py               # Connection lifecycle and automatic schema
│   └── services/
│       ├── __init__.py
│       └── quiz_service.py     # Quiz creation, answer validation, scoring
├── frontend/
│   ├── templates/
│   │   ├── base.html           # Shared navigation, messages, footer
│   │   ├── index.html
│   │   ├── error.html
│   │   ├── questions/
│   │   │   ├── _form.html      # Shared create/edit form partial
│   │   │   ├── list.html
│   │   │   ├── create.html
│   │   │   ├── edit.html
│   │   │   ├── view.html
│   │   │   └── delete.html     # Confirmation page
│   │   └── quiz/
│   │       ├── start.html
│   │       ├── quiz.html
│   │       └── result.html
│   └── static/
│       └── css/
│           └── style.css      # All styling and responsive breakpoints
├── database/
│   └── quiz.db                # Automatically initialized SQLite database
├── tests/
│   └── test_app.py            # Integration tests with temporary databases
├── .gitignore
├── requirements.txt
├── README.md
└── app.py
```

All complete pages extend `base.html`. `_form.html` is an included partial,
shared by the create and edit pages. Python lives in the backend; templates and
CSS live in the frontend. `app.py` is the entry point.

## How the frontend communicates with the backend

This is a server-rendered application. Browser links make GET requests to Flask
routes. Forms send URL-encoded POST data, including a hidden CSRF token. Flask
validates the submitted data, calls models or the quiz service, and renders a
Jinja2 template or redirects to the resulting page. Jinja2 loops generate the
question cards and table rows and automatically escape user-supplied content.
`url_for()` generates links and the CSS URL. No AJAX or JSON API is used.

Question routes handle forms and call the question model. Quiz routes delegate
business logic to the quiz service, which calls the models. Models use
parameterized SQLite queries through a request-scoped connection that closes
after the request.

## Route reference

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/` | Dashboard with question count, quiz count, average score, recent results |
| GET | `/questions` | List questions; optional `q` search and `difficulty` filter |
| GET | `/questions/create` | Show the new-question form |
| POST | `/questions/create` | Validate and save a question, then redirect to its details |
| GET | `/questions/<id>` | View all fields, options, correct answer, and timestamp |
| GET | `/questions/<id>/edit` | Show a prefilled edit form |
| POST | `/questions/<id>/edit` | Validate and save changes, then redirect to details |
| GET | `/questions/<id>/delete` | Show deletion confirmation without changing data |
| POST | `/questions/<id>/delete` | Delete the confirmed question, then redirect to the list |
| GET | `/quiz/start` | Show the name form and quiz instructions |
| POST | `/quiz/start` | Validate the name, snapshot questions, and start an attempt |
| GET | `/quiz` | Render all questions for the active attempt |
| POST | `/quiz/submit` | Validate all answers, score the attempt, save the result |
| GET | `/quiz/result/<id>` | Display the persisted result |
| GET | `/static/css/style.css` | Serve the stylesheet |

Missing records and malformed IDs return 404. Invalid forms return 400 with
useful messages and entered values preserved. Error templates also handle 405,
413, and 500 without displaying database internals.

## Question CRUD

1. Select **Manage Questions** or **Question bank**.
2. Select **Add New Question**. Enter the question, four options, correct letter,
   category, and difficulty. All fields are required.
3. Select **View** to inspect the complete question, or **Edit** to update it.
4. Select **Delete**, review the confirmation, then select **Delete Question**.
   **Keep Question** cancels the action.

The correct answer must be `A`, `B`, `C`, or `D`; difficulty must be `Easy`,
`Medium`, or `Hard`. Questions allow up to 2,000 characters; options and category
allow up to 300. Whitespace-only values are rejected on the server.

Example question: `What is 2 + 2?`, options `3`, `4`, `5`, `6`, correct answer
`B`, category `Mathematics`, difficulty `Easy`.

## Quiz flow and scoring

1. Select **Start Quiz** and enter a name (1–80 characters).
2. The service copies all current questions into an `attempts` record. Only a
   random attempt token is stored in the signed browser session; answer keys
   remain on the server.
3. The quiz template loops over the snapshot. Each question has four radio
   buttons sharing a name such as `answer_12`, where `12` is the question ID.
4. Select one answer for every question and select **Submit Quiz**. Missing,
   duplicated, invalid, or unknown question answers are rejected server-side.
5. The service compares each submitted answer with its stored correct answer:

   ```python
   if selected_answer == correct_answer:
       score += 1
   percentage = round((score / total_questions) * 100, 2)
   ```

6. The model saves the result and links it to the attempt in one transaction.
   Repeat submissions return that same result. A stale form from an older
   attempt cannot submit a newly started attempt.
7. The result page shows score, percentage, correct answers, wrong answers,
   **Try Again**, and **Back to Home**.

There is no time limit or negative marking. Empty quizzes cannot start or
submit; the scoring helper also explicitly returns zero for an empty list so
division by zero cannot occur. Wrong answers equal `total_questions - score`.

## Database and configuration

`backend/database/db.py` defines the schema with `CREATE TABLE IF NOT EXISTS`.

- `questions`: integer primary key, question/options/category text, constrained
  correct answer and difficulty, creation timestamp.
- `results`: integer primary key, name, integer score and total, real percentage,
  creation timestamp, and score bounds.
- `attempts`: an additional internal table containing a random token, name,
  JSON question snapshot, optional result reference, and creation timestamp.

SQLite `CURRENT_TIMESTAMP` is UTC. Each request gets its own connection.
Foreign keys are enabled. The actual database is ignored by Git because it
contains local data; it is recreated on startup if absent. To back up your
data, stop the application and copy `database/quiz.db` to a safe location.

Set `SECRET_KEY` before starting the application if sessions should survive
restarts. For example, generate a value with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Then assign the generated value in your terminal (PowerShell):

```powershell
$env:SECRET_KEY = 'your-generated-value'
python app.py
```

Without that environment variable, the app generates a random key on startup;
restarting then requires beginning a new browser session/quiz. Saved questions
and results remain intact. No `.env` loader is required.

This deliberately has no authentication: question management, correct-answer
details, and saved results are available to anyone using this local app. It is
suited to a trusted local learning/demo environment, not private exam delivery.
The entry point binds to `127.0.0.1` with debug mode disabled.

## Tests

Run from `online_quiz_system`:

```bash
python -m unittest discover -s tests -v
```

The integration tests create isolated temporary SQLite databases and
exercise home, create, list, view, edit, delete confirmation, deletion, quiz
start, answers, scoring, saved results, repeated submission, validation, CSRF,
HTML escaping, invalid IDs, empty quizzes, search, persistence, stale forms,
and edits/deletion during active quizzes. They do not modify your quiz data.

Verified: all seven tests pass and the real application starts successfully on
port 5000. Browser visual verification was unavailable in the build environment;
the templates and forms were exercised through Flask's HTTP test client.

## Troubleshooting

- **ModuleNotFoundError for Flask:** install requirements using the same Python
  interpreter you use to run the application.
- **Port 5000 in use:** stop the other local process or an earlier app instance.
- **Expired form message:** reload the page and submit again, especially after
  restarting the server without a persistent `SECRET_KEY`.
- **Unable to open database:** make sure your user can write to the project's
  `database` folder and that the database is not read-only.
- **No questions available:** add at least one question in the question bank.
