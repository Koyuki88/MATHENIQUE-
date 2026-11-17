import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_email(value: str) -> str:
    cleaned = value.strip().lower()
    if len(cleaned) > 254 or not _EMAIL_RE.match(cleaned):
        raise ValueError("Invalid email address")
    return cleaned


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Name cannot be empty")
        if any(ord(ch) < 32 for ch in cleaned):
            raise ValueError("Name contains invalid control characters")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _normalize_email(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password cannot be whitespace only")
        return v


class UserLogin(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _normalize_email(v)


class Token(BaseModel):
    access_token: str
    token_type: str


class QuestionOut(BaseModel):
    id: int
    text: str
    options: list[str]
    subject: str | None
    difficulty: int
    is_lesson: int
    is_game: int

    model_config = ConfigDict(from_attributes=True)


class GameStartRequest(BaseModel):
    mode: Literal["lesson", "normal", "mixed", "challenge", "apocalypse"]
    subject: Literal["algebra", "geometry", "trigonometry"] | None = None
    lesson_id: int | None = Field(default=None, ge=1, le=6)


class GameStartResponse(BaseModel):
    session_id: str
    mode: str
    questions: list[QuestionOut]


class AnswerSubmitRequest(BaseModel):
    question_id: int = Field(ge=1)
    selected_index: int = Field(ge=0, le=3)


class AnswerSubmitResponse(BaseModel):
    is_correct: bool
    correct_index: int
    points_earned: int
    score: int
    streak: int
    best_streak: int
    lives: int
    status: str


class GameTimeoutResponse(BaseModel):
    lives: int
    score: int
    best_streak: int
    status: str


class StatsOut(BaseModel):
    total_questions: int
    correct_answers: int
    games_played: int
    challenge_best_streak: int
    apocalypse_best_streak: int
    lessons_completed: int
    challenge_high_score: int
    apocalypse_high_score: int


class GameFinishResponse(BaseModel):
    status: str
    score: int
    best_streak: int
    stars: int | None = None
    stats: StatsOut


class LessonProgressOut(BaseModel):
    lesson_id: int
    stars: int
    completed: int

    model_config = ConfigDict(from_attributes=True)


class LeaderboardEntry(BaseModel):
    id: int
    user_id: int
    total_score: int
    games_won: int
    games_played: int
    average_accuracy: float
    highest_streak: int
    last_updated: str

    model_config = ConfigDict(from_attributes=True)


class LeaderboardResponse(BaseModel):
    rank: int
    user_name: str
    score: int
    games_won: int
    games_played: int
    accuracy: float
    streak: int


class UserRankResponse(BaseModel):
    user_rank: int
    total_players: int
    user_score: int
    user_name: str