# Clav

Clav (from the French *clavier*, "keyboard") is a small Flask web app. Paste any text and it shows how you'd type it on a US QWERTY keyboard:
- a heatmap of how often each key is pressed
- the most-pressed keys
- the left/right hand split
- how much typing stays on the home row
- how many times Shift is pressed

It models touch typing: each key belongs to a finger, and capitals and symbols count a press of the Shift key on the opposite hand.

The app is the workload for a **Jenkins CI/CD pipeline**. Every push to `main` is linted, tested, built into a Docker image and smoke-tested. If every step passes, the new image is deployed automatically.

## Pipeline

```
 GitHub push
     │  (Jenkins polls every ~2 min)
     ▼
┌──────────┐  ┌─────────┐  ┌──────┐  ┌──────────────────┐  ┌─────────────┐  ┌────────────┐  ┌──────────────┐
│ Checkout │→ │ Install │→ │ Lint │→ │ Test + coverage  │→ │ Build image │→ │ Smoke test │→ │ Deploy :5000 │
└──────────┘  └─────────┘  └──────┘  │ gate (≥ 80%)     │  │ clav:<build>│  │ /health +  │  │ health-wait, │
                                     │ JUnit + coverage │  └─────────────┘  │ /api/analyze│ │ auto rollback│
                                     │ reports          │                   └────────────┘  └──────────────┘
                                     └──────────────────┘
```

| Stage | What it proves |
|---|---|
| Lint | `flake8` keeps the code style clean. Any warning fails the build. |
| Test | `pytest` runs 34 unit and API tests. The build fails if coverage drops below 80%. Jenkins charts test results and coverage over time. |
| Build image | Builds a Docker image tagged with the Jenkins build number, e.g. `clav:14`. |
| Smoke test | Starts the new image in a throwaway container, then checks `/health` and a real `/api/analyze` call. |
| Deploy | Replaces the running `clav` container and waits for its Docker HEALTHCHECK to report healthy. If the new container never turns healthy, Jenkins rolls back to the previous image. |

The page shows the build number in its top-right corner, so you can see a new deploy land.

## Project layout

```
app/
  heatmap.py        keystroke analysis (pure Python, no Flask)
  routes.py         GET /   POST /api/analyze   GET /health
  templates/        the page
  static/           CSS and JS
tests/              pytest unit and API tests
Dockerfile          app image (slim base, non-root user, HEALTHCHECK)
Jenkinsfile         the pipeline
jenkins/            Jenkins image with Python + Docker CLI, plugins, compose file
```

## Run it locally (no Docker)

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on Mac/Linux)
pip install -r requirements-dev.txt
flake8 app tests
pytest --cov=app
flask --app "app:create_app()" run
```

Then open http://localhost:5000.

## One-time Jenkins setup

1. **Install Docker Desktop** and keep the WSL 2 backend enabled. Start it.
2. **Start Jenkins** from this folder:
   ```bash
   docker compose -f jenkins/docker-compose.yml up -d --build
   ```
   This builds a Jenkins image that already includes Python, the Docker CLI and the needed plugins, and creates the shared `clav-net` network.
3. **Unlock Jenkins.** Open http://localhost:8080. Get the unlock password with:
   ```bash
   docker exec clav-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```
   Choose **Install suggested plugins**, then create your admin user.
4. **Push this folder to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Clav: keyboard heatmap with Jenkins pipeline"
   git branch -M main
   git remote add origin https://github.com/<you>/clav.git
   git push -u origin main
   ```
5. **Create the job.** In Jenkins, go to **New Item**, enter the name `clav`, choose **Pipeline**, then:
   - Under **Pipeline**, set **Definition** to *Pipeline script from SCM*.
   - Set **SCM** to *Git* and **Repository URL** to your GitHub repo URL.
   - Set **Branch** to `*/main` and **Script Path** to `Jenkinsfile`.
6. Click **Build Now** once. That first run deploys the app to http://localhost:5000 and switches on the 2-minute polling trigger.

> Jenkins runs on your own PC, so GitHub can't send it webhooks. It polls the repo instead (`pollSCM`).
>
> Jenkins runs as root inside its container so it can use the host's Docker socket. That's fine for a local demo; a real server would use a `docker` group instead.

## Demo script

1. **Green build.** Make a small change, for example to the sample text in `app/static/app.js`, then commit and push. Within about 2 minutes a new build starts, every stage turns green, and the page at `localhost:5000` shows the new build number.
2. **Red build.** Break a test, for example change `== 6` to `== 7` in `test_capital_letter_counts_shift_press`, then commit and push. The build fails at **Test**, the later stages are skipped, and the live app stays on the previous build number. The pipeline blocked bad code from shipping.
3. **Fix it.** Revert the change and push. The build goes green and redeploys.
4. **Show the evidence:**
   - the stage view
   - the test result and coverage trend charts
   - `docker images clav`, where each tag matches a build number
   - `docker ps`, where the container shows `(healthy)`

## API

```bash
curl -X POST localhost:5000/api/analyze -H "Content-Type: application/json" -d '{"text": "Hello"}'
curl localhost:5000/health
```

`/api/analyze` takes `{"text": "..."}` (up to 100 KB) and returns:
- the key counts and colour intensities
- the top keys
- the hand split, home-row share and finger load
- the number of Shift presses

Bad input returns a JSON error with status 400; a body over 100 KB returns 413.
