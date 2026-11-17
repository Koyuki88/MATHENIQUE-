from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    lessons_completed = Column(Integer, default=0)
    challenge_best_streak = Column(Integer, default=0)
    apocalypse_best_streak = Column(Integer, default=0)
    challenge_high_score = Column(Integer, default=0)
    apocalypse_high_score = Column(Integer, default=0)

    user = relationship("User")


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mode = Column(String)  # normal | mixed | challenge | apocalypse
    subject = Column(String, nullable=True)
    score = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lesson_id = Column(Integer)
    stars = Column(Integer, default=0)
    completed = Column(Integer, default=0)

    user = relationship("User")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    options = Column(JSON, nullable=False)
    correct_index = Column(Integer, nullable=False)

    subject = Column(String, nullable=True)  # algebra | geometry | trigonometry
    difficulty = Column(Integer, default=1)  # 1-3
    is_lesson = Column(Integer, default=0)
    is_game = Column(Integer, default=1)


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mode = Column(String, nullable=False)  # lesson | normal | mixed | challenge | apocalypse
    lesson_id = Column(Integer, nullable=True)
    subject = Column(String, nullable=True)
    question_ids = Column(JSON, nullable=False)
    answered_ids = Column(JSON, nullable=False, default=list)
    correct_count = Column(Integer, nullable=False, default=0)
    total_answered = Column(Integer, nullable=False, default=0)
    score = Column(Integer, nullable=False, default=0)
    current_streak = Column(Integer, nullable=False, default=0)
    best_streak = Column(Integer, nullable=False, default=0)
    lives = Column(Integer, nullable=False, default=3)
    status = Column(String, nullable=False, default="active")  # active | won | lost | ended
    finalized = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User")


class Leaderboard(Base):
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    total_score = Column(Integer, default=0, index=True)
    games_won = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    average_accuracy = Column(Float, default=0.0)
    highest_streak = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, index=True)

    user = relationship("User", backref="leaderboard_entry")

    __table_args__ = (
        Index('idx_leaderboard_score_time', 'total_score', 'last_updated'),
    )
