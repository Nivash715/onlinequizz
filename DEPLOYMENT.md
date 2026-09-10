# Free hosting: Render + Vercel

## How it runs

The existing `backend/app.py` is the entry point. Run locally with `python backend/app.py`.
Render runs Flask using Gunicorn (`app:create_app()`). Vercel serves static assets and
proxies pages/forms to Render, where Flask renders the existing Jinja templates.
Use the Vercel URL consistently so forms and session cookies share one domain.

## Render: free backend

Push the entire project to Git, then choose **New > Blueprint** in Render and
connect the repository. `render.yaml` selects `plan: free` with no paid disk
or database. Set Root Directory to `backend`. This folder includes the Python
code, Jinja templates, and static assets required to run independently.

For a manual **New > Web Service** deployment, use:

| Setting | Value |
| --- | --- |
| Runtime | Python 3 |
| Root directory | `backend` |
| Instance type | Free |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --access-logfile - --error-logfile - 'app:create_app()'` |
| Health check | `/healthz` |
| `APP_ENV` | `production` |
| `SECRET_KEY` | A random secret with at least 32 characters |
| `DATABASE_PATH` | `/tmp/quizcraft/quiz.db` |
| `PYTHON_VERSION` | `3.12.8` |

The Blueprint generates `SECRET_KEY` automatically. For manual setup, generate
one with `python -c "import secrets; print(secrets.token_hex(32))"` and save it
in Render's environment settings. Keep it unchanged across redeploys.

After deployment, open `https://onlinequizz-2.onrender.com/healthz` and confirm
it returns `{"status":"ok"}`. Copy the HTTPS origin for Vercel.

If you already created a paid service from the old configuration, changing the
repository does not by itself cancel its billing. Remove its disk and choose
Free in Render, or delete that unused paid service and create this free service.
Save any needed data before deleting an existing service or disk.

## Vercel: free frontend

1. Use the Hobby plan for this personal/demo project and import the same repo.
2. Set **Root Directory** to `frontend` and **Framework Preset** to **Other**.
3. Select Node.js 22.x. `frontend/vercel.json` sets `node build.mjs` as the build
   command; no npm dependencies are required.
4. Leave the Output Directory override disabled. Vercel detects the generated
   Build Output API directory `.vercel/output`.
5. Deploy. The build defaults to `https://onlinequizz-2.onrender.com`.
   `BACKEND_URL` is optional; if it already exists in Vercel settings, update it
   to this URL or remove it so the default applies.
6. Open the Vercel URL, add a question, and complete a quiz to verify the flow.

Redeploy Vercel when changing `BACKEND_URL`. Do not put Render's secret key or
database settings in Vercel. Preview deployments use the same default backend unless `BACKEND_URL` is
overridden; they share and can change its data.

## Free hosting limitations

The SQLite tables are created automatically, initially empty. On free Render,
questions, results, and quiz attempts are temporary: they are lost on restart,
redeploy, or idle spin-down. The service sleeps after 15 minutes without inbound
traffic; waking can take about a minute. A quiz left open through spin-down may
need to be started again. Local use still saves data in `database/quiz.db`.

This configuration has no paid resources. Free hosting remains subject to
platform usage limits. Durable hosted data would require adapting this SQLite
application to an external database; it is not provided by this configuration.

## Fix an existing deployment stuck scanning ports

In Render Settings, keep **Root Directory** set to `backend`, set
Build Command to `pip install -r requirements.txt`, and set Start
Command to `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 'app:create_app()'`.
Save the settings, push the latest code, and deploy the latest commit. A manually
created service does not automatically use commands from `render.yaml`.

The old `python app.py` command launched Flask on `127.0.0.1`, which Render
cannot expose. The direct Python entry point now defaults to `0.0.0.0` when
`RENDER` or `PORT` is set; Gunicorn remains the configured hosting command.
Remove an explicit `HOST=127.0.0.1` environment override if using direct Python.

## Checks and troubleshooting

```powershell
python -m unittest discover -s tests -v
$env:BACKEND_URL = 'https://onlinequizz-2.onrender.com'
node frontend/build.mjs
```

Verify CSS loads, searches work, question forms save, and quiz submission shows
a result. The generated static output includes assets only, not template source
or backend files. Dynamic pages use `Cache-Control: private, no-store` and
production session cookies use Secure, HttpOnly, and SameSite=Lax.

- Slow first request or proxy timeout: open Render's `/healthz`, allow it to
  wake, then reload Vercel. Check Render logs if the error continues.
- Wrong backend: update or remove an existing Vercel `BACKEND_URL` override,
  then redeploy. The default is `https://onlinequizz-2.onrender.com`.
- Missing CSS: verify the Vercel root directory and build command.
- Expired forms: reload; keep `SECRET_KEY` stable and restart a quiz if its
  temporary database disappeared.
- Missing questions/results after inactivity: expected on free SQLite hosting.
- Startup failure: check the environment variables above. `.env.example` is
  a reference; environment files are not loaded automatically.

The existing app has no authentication: question editing, answer keys, and
results are public. This setup is for a demo, not private exam delivery.

References: [Render free hosting](https://render.com/docs/free),
[Render Flask](https://render.com/docs/deploy-flask),
[Vercel Hobby](https://vercel.com/docs/plans/hobby), and
[Vercel Build Output API](https://vercel.com/docs/build-output-api/configuration).

Templates live in `backend/templates`. When editing CSS, update both
`frontend/static/css/style.css` (Vercel) and `backend/static/css/style.css`
(Render/local fallback) so the two deployments stay consistent.
