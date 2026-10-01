from datetime import datetime, date
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(20), default="⌨️")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile = db.relationship("UserProfile", backref="user", uselist=False, cascade="all, delete-orphan")
    results = db.relationship("TestResult", backref="user", lazy=True, cascade="all, delete-orphan")
    settings = db.relationship("UserSetting", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserProfile(db.Model):
    __tablename__ = "user_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    bio = db.Column(db.String(240), default="")
    preferred_level = db.Column(db.String(20), default="Beginner")

class TestResult(db.Model):
    __tablename__ = "test_results"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    mode = db.Column(db.String(30), default="time")
    difficulty = db.Column(db.String(20), default="Beginner")
    duration = db.Column(db.Integer, default=60)
    wpm = db.Column(db.Float, nullable=False)
    cpm = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    correct_chars = db.Column(db.Integer, default=0)
    wrong_chars = db.Column(db.Integer, default=0)
    total_chars = db.Column(db.Integer, default=0)
    typed_text = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class TypingHistory(db.Model):
    __tablename__ = "typing_history"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    result_id = db.Column(db.Integer, db.ForeignKey("test_results.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PersonalBest(db.Model):
    __tablename__ = "personal_bests"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    best_wpm = db.Column(db.Float, default=0)
    best_accuracy = db.Column(db.Float, default=0)
    best_cpm = db.Column(db.Float, default=0)

class Achievement(db.Model):
    __tablename__ = "achievements"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(180), nullable=False)
    threshold = db.Column(db.Float, default=1)

class UserAchievement(db.Model):
    __tablename__ = "user_achievements"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey("achievements.id"), nullable=False)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)

class DailyChallenge(db.Model):
    __tablename__ = "daily_challenges"
    id = db.Column(db.Integer, primary_key=True)
    challenge_date = db.Column(db.Date, unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(180), nullable=False)
    target_wpm = db.Column(db.Integer, default=25)

class ChallengeAttempt(db.Model):
    __tablename__ = "challenge_attempts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey("daily_challenges.id"), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    achieved_wpm = db.Column(db.Float, default=0)

class UserStreak(db.Model):
    __tablename__ = "user_streaks"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_active = db.Column(db.Date)

class UserSetting(db.Model):
    __tablename__ = "user_settings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    theme = db.Column(db.String(20), default="dark")
    sound = db.Column(db.Boolean, default=False)
    font_size = db.Column(db.Integer, default=18)

class LeaderboardScore(db.Model):
    __tablename__ = "leaderboard_scores"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    result_id = db.Column(db.Integer, db.ForeignKey("test_results.id"), nullable=False)
    wpm = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CustomTest(db.Model):
    __tablename__ = "custom_tests"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
