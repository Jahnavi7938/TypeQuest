
from datetime import datetime, date, timedelta
from functools import wraps
import os
import random
import re

from flask import (
    Flask, render_template, redirect, url_for,
    request, flash, jsonify, session
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import func
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from config import Config
from models import (
    db, User, UserProfile, TestResult, TypingHistory,
    PersonalBest, Achievement, UserAchievement,
    DailyChallenge, ChallengeAttempt, UserStreak,
    UserSetting, LeaderboardScore, CustomTest
)


# ==========================================
# 1. FLASK APPLICATION CONFIGURATION
# ==========================================

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ==========================================
# 2. TYPING PASSAGES
# ==========================================

PASSAGES = {
    "Beginner": [
        "Small steps every day can lead to great results. Practice makes progress, so stay curious and keep going.",
        "A calm mind and steady hands help you type with care. Focus on each word and enjoy the journey."
    ],

    "Intermediate": [
        "Technology changes the way people learn, work, and communicate. Consistent practice helps build confidence and accuracy.",
        "Good habits are created through patience, repetition, and attention to detail. Measure your progress and celebrate improvement."
    ],

    "Expert": [
        "Reliable software is built through deliberate design, thoughtful testing, and careful attention to edge cases. Precision matters as much as speed.",
        "In a connected world, clear communication depends on accurate information, strong reasoning, and the ability to adapt to changing requirements."
    ]
}


# ==========================================
# 3. ACHIEVEMENTS
# ==========================================

ACHIEVEMENTS = [
    ("first_test", "First Test", "Complete your first typing test.", 1),
    ("speed_20", "Beginner Typist", "Reach 20 WPM.", 20),
    ("speed_30", "Speed Starter", "Reach 30 WPM.", 30),
    ("speed_50", "Speed Master", "Reach 50 WPM.", 50),
    ("speed_80", "Expert Typist", "Reach 80 WPM.", 80),
    ("accuracy_95", "Accuracy Champion", "Achieve 95% accuracy.", 95),
    ("perfect", "Perfect Typist", "Achieve 100% accuracy.", 100),
    ("tests_10", "Practice Habit", "Complete 10 tests.", 10),
    ("tests_100", "Typing Addict", "Complete 100 tests.", 100)
]


# ==========================================
# 4. DATABASE SEEDING
# ==========================================

def seed_data():

    # Insert achievements without duplicate codes.
    achievement_rows = [
        {
            "code": code,
            "title": title,
            "description": description,
            "threshold": threshold
        }
        for code, title, description, threshold in ACHIEVEMENTS
    ]

    achievement_stmt = (
        sqlite_insert(Achievement)
        .values(achievement_rows)
        .on_conflict_do_nothing(index_elements=["code"])
    )

    db.session.execute(achievement_stmt)

    # Create today's daily challenge only once.
    today = date.today()

    challenge_stmt = (
        sqlite_insert(DailyChallenge)
        .values(
            challenge_date=today,
            title="Daily Speed Sprint",
            description="Complete a 60-second test and aim for 25 WPM.",
            target_wpm=25
        )
        .on_conflict_do_nothing(index_elements=["challenge_date"])
    )

    db.session.execute(challenge_stmt)

    db.session.commit()


# ==========================================
# 5. DATABASE INITIALIZATION
# ==========================================

with app.app_context():

    os.makedirs(app.instance_path, exist_ok=True)

    db.create_all()

    seed_data()


# ==========================================
# 6. USER STATISTICS
# ==========================================

def user_stats(user):

    results = (
        TestResult.query
        .filter_by(user_id=user.id)
        .order_by(TestResult.created_at.desc())
        .all()
    )

    count = len(results)

    avg_wpm = (
        round(sum(x.wpm for x in results) / count, 1)
        if count else 0
    )

    avg_acc = (
        round(sum(x.accuracy for x in results) / count, 1)
        if count else 0
    )

    best = max(
        (x.wpm for x in results),
        default=0
    )

    return results, count, avg_wpm, avg_acc, round(best, 1)


# ==========================================
# 7. UPDATE USER PROGRESS
# ==========================================

def update_progress(user, result):

    # Personal best
    pb = PersonalBest.query.filter_by(
        user_id=user.id
    ).first()

    if not pb:
        pb = PersonalBest(user_id=user.id)
        db.session.add(pb)

    pb.best_wpm = max(pb.best_wpm, result.wpm)
    pb.best_accuracy = max(pb.best_accuracy, result.accuracy)
    pb.best_cpm = max(pb.best_cpm, result.cpm)

    # Typing history
    db.session.add(
        TypingHistory(
            user_id=user.id,
            result_id=result.id
        )
    )

    # Leaderboard
    db.session.add(
        LeaderboardScore(
            user_id=user.id,
            result_id=result.id,
            wpm=result.wpm,
            accuracy=result.accuracy
        )
    )

    # Total tests completed
    total = TestResult.query.filter_by(
        user_id=user.id
    ).count()

    unlocked = {
        x.achievement_id
        for x in UserAchievement.query.filter_by(
            user_id=user.id
        ).all()
    }

    # Achievement checking
    for achievement in Achievement.query.all():

        if achievement.code.startswith("speed"):
            metric = result.wpm

        elif achievement.code in ("accuracy_95", "perfect"):
            metric = result.accuracy

        else:
            metric = total

        if (
            metric >= achievement.threshold
            and achievement.id not in unlocked
        ):
            db.session.add(
                UserAchievement(
                    user_id=user.id,
                    achievement_id=achievement.id
                )
            )

    # User streak
    streak = UserStreak.query.filter_by(
        user_id=user.id
    ).first()

    if not streak:

        streak = UserStreak(
            user_id=user.id,
            current_streak=1,
            longest_streak=1,
            last_active=date.today()
        )

        db.session.add(streak)

    elif streak.last_active != date.today():

        streak.current_streak = (
            streak.current_streak + 1
            if streak.last_active == date.today() - timedelta(days=1)
            else 1
        )

        streak.longest_streak = max(
            streak.longest_streak,
            streak.current_streak
        )

        streak.last_active = date.today()

    # Daily challenge
    challenge = DailyChallenge.query.filter_by(
        challenge_date=date.today()
    ).first()

    if (
        challenge
        and result.duration >= 60
        and result.wpm >= challenge.target_wpm
    ):

        attempt = ChallengeAttempt.query.filter_by(
            user_id=user.id,
            challenge_id=challenge.id
        ).first()

        if not attempt:

            db.session.add(
                ChallengeAttempt(
                    user_id=user.id,
                    challenge_id=challenge.id,
                    completed=True,
                    achieved_wpm=result.wpm
                )
            )

    db.session.commit()


# ==========================================
# 8. GLOBAL TEMPLATE VARIABLES
# ==========================================

@app.context_processor
def inject_globals():

    return {
        "today_year": date.today().year
    }


# ==========================================
# 9. HOME PAGE
# ==========================================

@app.route("/")
def index():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return render_template("index.html")


# ==========================================
# 10. USER REGISTRATION
# ==========================================

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("8 per hour")
def register():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name", ""
        ).strip()

        username = request.form.get(
            "username", ""
        ).strip().lower()

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get("password", "")

        if (
            len(full_name) < 2
            or not re.fullmatch(r"[a-zA-Z0-9_]{3,30}", username)
        ):

            flash(
                "Enter a name and a username with 3–30 letters, numbers or underscores.",
                "danger"
            )

        elif len(password) < 8:

            flash(
                "Use a password with at least 8 characters.",
                "danger"
            )

        elif User.query.filter(
            (User.email == email) |
            (User.username == username)
        ).first():

            flash(
                "That email or username is already registered.",
                "danger"
            )

        else:

            user = User(
                full_name=full_name,
                username=username,
                email=email
            )

            user.set_password(password)

            db.session.add(user)
            db.session.flush()

            db.session.add(UserProfile(user_id=user.id))
            db.session.add(UserSetting(user_id=user.id))
            db.session.add(UserStreak(user_id=user.id))

            db.session.commit()

            login_user(user)

            flash(
                "Welcome to TypeQuest! Your account is ready.",
                "success"
            )

            return redirect(url_for("dashboard"))

    return render_template("auth.html", mode="register")


# ==========================================
# 11. USER LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def login():

    if request.method == "POST":

        identity = request.form.get(
            "identity", ""
        ).strip().lower()

        user = User.query.filter(
            (User.email == identity) |
            (User.username == identity)
        ).first()

        if user and user.check_password(
            request.form.get("password", "")
        ):

            login_user(
                user,
                remember=bool(request.form.get("remember"))
            )

            return redirect(url_for("dashboard"))

        flash(
            "Incorrect username/email or password.",
            "danger"
        )

    return render_template("auth.html", mode="login")


# ==========================================
# 12. USER LOGOUT
# ==========================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "info"
    )

    return redirect(url_for("index"))


# ==========================================
# 13. GUEST MODE
# ==========================================

@app.route("/guest")
def guest():

    session["guest_mode"] = True

    return redirect(url_for("typing_test"))


# ==========================================
# 14. USER DASHBOARD
# ==========================================

@app.route("/dashboard")
@login_required
def dashboard():

    results, count, avg, acc, best = user_stats(current_user)

    streak = UserStreak.query.filter_by(
        user_id=current_user.id
    ).first()

    pb = PersonalBest.query.filter_by(
        user_id=current_user.id
    ).first()

    unlocked = UserAchievement.query.filter_by(
        user_id=current_user.id
    ).count()

    challenge = DailyChallenge.query.filter_by(
        challenge_date=date.today()
    ).first()

    return render_template(
        "dashboard.html",
        count=count,
        avg=avg,
        acc=acc,
        best=best,
        streak=streak,
        pb=pb,
        unlocked=unlocked,
        recent=results[:5],
        challenge=challenge
    )


# ==========================================
# 15. TYPING TEST
# ==========================================

@app.route("/typing")
def typing_test():

    level = request.args.get(
        "level", "Beginner"
    )

    if level not in PASSAGES:
        level = "Beginner"

    passage = random.choice(PASSAGES[level])

    return render_template(
        "typing.html",
        passage=passage,
        level=level
    )


# ==========================================
# 16. SAVE TYPING TEST RESULT
# ==========================================

@app.route("/api/result", methods=["POST"])
def save_result():

    if not current_user.is_authenticated:

        return jsonify({
            "saved": False,
            "message": "Sign in to save your score."
        }), 401

    data = request.get_json(silent=True) or {}

    try:

        duration = max(
            1,
            min(int(data.get("duration", 60)), 3600)
        )

        correct = max(
            0,
            int(data.get("correct_chars", 0))
        )

        wrong = max(
            0,
            int(data.get("wrong_chars", 0))
        )

        total = correct + wrong

        if total == 0 or total > 20000:

            return jsonify({
                "error": "The submitted test data is not valid."
            }), 400

        # Recalculate metrics on the server.
        elapsed = max(
            1,
            min(int(data.get("elapsed", duration)), duration)
        )

        wpm = round(
            (correct / 5) / (elapsed / 60),
            1
        )

        cpm = round(
            correct / (elapsed / 60),
            1
        )

        accuracy = round(
            (correct / total) * 100,
            1
        )

        level = data.get(
            "difficulty", "Beginner"
        )

        if level not in PASSAGES:
            level = "Beginner"

        result = TestResult(
            user_id=current_user.id,
            mode=data.get("mode", "time")[:30],
            difficulty=level,
            duration=duration,
            wpm=wpm,
            cpm=cpm,
            accuracy=accuracy,
            correct_chars=correct,
            wrong_chars=wrong,
            total_chars=total,
            typed_text=str(
                data.get("typed_text", "")
            )[:20000]
        )

        db.session.add(result)
        db.session.flush()

        update_progress(current_user, result)

        return jsonify({
            "saved": True,
            "wpm": wpm,
            "cpm": cpm,
            "accuracy": accuracy
        })

    except (ValueError, TypeError):

        db.session.rollback()

        return jsonify({
            "error": "Invalid score data."
        }), 400


# ==========================================
# 17. GAMES PAGE
# ==========================================

@app.route("/games")
def games():

    return render_template("games.html")


# ==========================================
# 18. PRACTICE PAGE
# ==========================================

@app.route("/practice")
def practice():

    return render_template("practice.html")


# ==========================================
# 19. ANALYTICS PAGE
# ==========================================

@app.route("/analytics")
@login_required
def analytics():

    results, count, avg, acc, best = user_stats(current_user)

    ordered = list(reversed(results[-20:]))

    return render_template(
        "analytics.html",
        results=ordered,
        count=count,
        avg=avg,
        acc=acc,
        best=best
    )


# ==========================================
# 20. TYPING HISTORY
# ==========================================

@app.route("/history")
@login_required
def history():

    results, *_ = user_stats(current_user)

    return render_template(
        "history.html",
        results=results
    )


# ==========================================
# 21. ACHIEVEMENTS PAGE
# ==========================================

@app.route("/achievements")
@login_required
def achievements():

    items = Achievement.query.order_by(
        Achievement.id
    ).all()

    unlocked = {
        x.achievement_id
        for x in UserAchievement.query.filter_by(
            user_id=current_user.id
        ).all()
    }

    return render_template(
        "achievements.html",
        items=items,
        unlocked=unlocked
    )


# ==========================================
# 22. LEADERBOARD
# ==========================================

@app.route("/leaderboard")
def leaderboard():

    rows = (
        db.session.query(
            User.username,
            User.avatar,
            func.max(LeaderboardScore.wpm).label("wpm"),
            func.max(LeaderboardScore.accuracy).label("accuracy")
        )
        .join(
            LeaderboardScore,
            User.id == LeaderboardScore.user_id
        )
        .group_by(User.id)
        .order_by(
            func.max(LeaderboardScore.wpm).desc()
        )
        .limit(50)
        .all()
    )

    return render_template(
        "leaderboard.html",
        rows=rows
    )


# ==========================================
# 23. USER PROFILE
# ==========================================

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if request.method == "POST":

        current_user.full_name = request.form.get(
            "full_name",
            current_user.full_name
        ).strip()[:100]

        current_user.avatar = request.form.get(
            "avatar", "⌨️"
        )[:8]

        current_user.profile.bio = request.form.get(
            "bio", ""
        ).strip()[:240]

        db.session.commit()

        flash(
            "Profile updated.",
            "success"
        )

    results, count, avg, acc, best = user_stats(current_user)

    return render_template(
        "profile.html",
        count=count,
        avg=avg,
        acc=acc,
        best=best
    )


# ==========================================
# 24. USER SETTINGS
# ==========================================

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    setting = current_user.settings

    if request.method == "POST":

        theme = request.form.get(
            "theme", "dark"
        )

        setting.theme = (
            theme
            if theme in ["dark", "light", "amoled", "blue"]
            else "dark"
        )

        setting.sound = bool(
            request.form.get("sound")
        )

        setting.font_size = max(
            14,
            min(
                26,
                int(request.form.get("font_size", 18))
            )
        )

        db.session.commit()

        flash(
            "Settings saved.",
            "success"
        )

    return render_template(
        "settings.html",
        setting=setting
    )


# ==========================================
# 25. ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def not_found(e):

    return render_template(
        "error.html",
        code=404,
        message="This page could not be found."
    ), 404


@app.errorhandler(500)
def server_error(e):

    db.session.rollback()

    return render_template(
        "error.html",
        code=500,
        message="Something went wrong. Please try again."
    ), 500


# ==========================================
# 26. RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(debug=True)