# TypeQuest – The Ultimate Gamified Typing Speed Tester

A Flask + SQLite typing practice platform with authentication, a live typing test, performance history, analytics, achievements, daily challenges, profiles, themes and a community leaderboard.

## Requirements
- Python 3.10 or newer
- pip
- A modern browser
- Internet connection for Bootstrap, Font Awesome, Google Fonts and Chart.js CDN assets

## Run on Windows
1. Extract `TypeQuest.zip`.
2. Open the extracted `TypeQuest` folder in VS Code.
3. Open a terminal in that folder.
4. Create and activate a virtual environment:

```powershell
py -m venv venv
venv\Scripts\activate
```

5. Install packages:

```powershell
py -m pip install -r requirements.txt
```

6. Start the app:

```powershell
py run.py
```

7. Open http://127.0.0.1:5000 in your browser.

## Run on macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

## Included features
- Registration, login, logout, password hashing and guest test access
- Dashboard with personal statistics and recent sessions
- Time-based typing test (15, 30, 60 and 120 seconds)
- Beginner, Intermediate and Expert passages
- Live WPM, accuracy, error count and progress
- Saved test results and history
- Performance chart with Chart.js
- Achievement badges and daily speed challenge
- Community leaderboard based on saved scores
- Editable profile and theme/sound preferences
- Responsive layout for desktop and mobile

## Project structure

```text
TypeQuest/
├── app.py
├── config.py
├── models.py
├── run.py
├── requirements.txt
├── README.md
├── instance/
├── templates/
└── static/
    ├── css/
    ├── js/
    ├── images/
    └── sounds/
```

## Database
SQLite database is created automatically at `instance/typequest.db` on first run. The app creates its tables and seeds the achievement catalogue and today's challenge automatically.

## Security notes
- Passwords are stored using Werkzeug password hashing.
- Flask-WTF CSRF protection is enabled for forms and the score API.
- Login and registration routes have rate limits.
- Use a long random `SECRET_KEY` environment variable before deployment.
- For a public leaderboard, add stronger anti-cheat controls and independent server-issued test challenges. A browser-based typing client cannot provide perfect anti-cheat guarantees.

## Important implementation notes
- The current score endpoint recalculates WPM, CPM and accuracy on the server using submitted character counts and elapsed time. For a production competitive leaderboard, use server-issued passage IDs, signed test sessions and stricter timing validation.
- Password reset email delivery, friend-specific leaderboards, cloud deployment, and advanced falling-word game mechanics require additional service/infrastructure work and are not represented as completed features in this starter release.
