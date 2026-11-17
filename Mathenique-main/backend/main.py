from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import os
from random import shuffle
import uuid

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.database import Base, SessionLocal, engine, get_db
from backend.models import GameSession, Leaderboard, LessonProgress, Progress, Question, User
from backend.questions_seed import seed_questions
from backend.schemas import (
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    GameFinishResponse,
    GameStartRequest,
    GameStartResponse,
    GameTimeoutResponse,
    LeaderboardResponse,
    LessonProgressOut,
    QuestionOut,
    StatsOut,
    Token,
    UserCreate,
    UserRankResponse,
)
from backend.security import rate_limit, rate_limiter

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
IS_PRODUCTION = ENVIRONMENT == "production"

LESSON_META: dict[int, tuple[str, int]] = {
    1: ("algebra", 1),
    2: ("algebra", 2),
    3: ("geometry", 1),
    4: ("geometry", 2),
    5: ("trigonometry", 1),
    6: ("trigonometry", 2),
}

_DEFAULT_PROD_ORIGINS = [
    "https://mathenique-1.onrender.com",
    "https://mathenique-frontend.onrender.com",
    "https://mathenique-frontend-w2uu.onrender.com",
]
_DEFAULT_DEV_ORIGINS = [
    *_DEFAULT_PROD_ORIGINS,
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def _parse_csv_env(name: str) -> list[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Question).count() == 0:
            seed_questions(db)
        else:
            legacy_trig = (
                db.query(Question)
                .filter(Question.text == "If cos X = a/b, then sin X is equal to:")
                .first()
            )
            if legacy_trig and legacy_trig.options == [
                "(b2-a2)/b",
                "(b-a)/b",
                "√(b2-a2)/b",
                "√(b-a)/b",
            ]:
                legacy_trig.options = ["(b^2-a^2)/b", "(b-a)/b", "√(b^2-a^2)/b", "√(b-a)/b"]
                db.commit()
    except IntegrityError:
        db.rollback()
    finally:
        db.close()
    yield


app = FastAPI(
    lifespan=lifespan,
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
)

allowed_hosts = _parse_csv_env("ALLOWED_HOSTS") or (
    ["*.onrender.com"]
    if IS_PRODUCTION
    else ["localhost", "127.0.0.1", "0.0.0.0", "testserver"]
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

allowed_origins = _parse_csv_env("ALLOWED_ORIGINS") or (
    _DEFAULT_PROD_ORIGINS if IS_PRODUCTION else _DEFAULT_DEV_ORIGINS
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=(
        None
        if IS_PRODUCTION
        else r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$"
    ),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cache-Control"] = "no-store"
    if IS_PRODUCTION:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _ensure_progress(user_id: int, db: Session) -> Progress:
    progress = db.query(Progress).filter(Progress.user_id == user_id).first()
    if not progress:
        progress = Progress(
            user_id=user_id,
            total_questions=0,
            correct_answers=0,
            games_played=0,
            lessons_completed=0,
            challenge_best_streak=0,
            apocalypse_best_streak=0,
            challenge_high_score=0,
            apocalypse_high_score=0,
        )
        db.add(progress)
        db.flush()
    return progress


def _stats_out(progress: Progress | None) -> StatsOut:
    if not progress:
        return StatsOut(
            total_questions=0,
            correct_answers=0,
            games_played=0,
            challenge_best_streak=0,
            apocalypse_best_streak=0,
            lessons_completed=0,
            challenge_high_score=0,
            apocalypse_high_score=0,
        )
    return StatsOut(
        total_questions=progress.total_questions,
        correct_answers=progress.correct_answers,
        games_played=progress.games_played,
        challenge_best_streak=progress.challenge_best_streak,
        apocalypse_best_streak=progress.apocalypse_best_streak,
        lessons_completed=progress.lessons_completed,
        challenge_high_score=progress.challenge_high_score,
        apocalypse_high_score=progress.apocalypse_high_score,
    )


def initialize_leaderboard_entry(user_id: int, db: Session) -> Leaderboard:
    """Create leaderboard entry for user if missing."""
    existing = db.query(Leaderboard).filter(Leaderboard.user_id == user_id).first()
    if existing:
        return existing
    leaderboard = Leaderboard(user_id=user_id)
    db.add(leaderboard)
    db.flush()
    return leaderboard


def _get_completed_lesson_ids(user_id: int, db: Session) -> set[int]:
    rows = (
        db.query(LessonProgress.lesson_id)
        .filter(
            LessonProgress.user_id == user_id,
            LessonProgress.completed >= 1,
        )
        .all()
    )
    return {row[0] for row in rows if row[0] in LESSON_META}


@app.get("/")
@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/me")
def get_me(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
    }


@app.get("/profile")
def profile(user_id: int = Depends(get_current_user)):
    return {"id": user_id}


@app.get("/lessons/progress", response_model=list[LessonProgressOut])
def get_lesson_progress(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == user_id)
        .all()
    )


@app.get("/questions", response_model=list[QuestionOut])
def get_questions(
    mode: str | None = None,
    count: int = Query(10, ge=1, le=50),
    subject: str | None = None,
    difficulty: int | None = Query(None, ge=1, le=3),
    is_lesson: bool = Query(False),
    _user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Question)

    if is_lesson:
        query = query.filter(Question.is_lesson == 1)

    if subject:
        query = query.filter(Question.subject == subject)

    if difficulty is not None:
        query = query.filter(Question.difficulty == difficulty)

    if mode == "challenge":
        query = query.filter(Question.difficulty <= 2)
    elif mode == "apocalypse":
        query = query.filter(Question.difficulty <= 3)

    questions = query.all()
    shuffle(questions)
    return questions[:count]


@app.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("register", 5, 60))],
)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = (
        db.query(User).filter(func.lower(User.email) == user.email).first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    existing_name = (
        db.query(User).filter(func.lower(User.name) == user.name.lower()).first()
    )
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password),
    )

    try:
        db.add(new_user)
        db.flush()
        initialize_leaderboard_entry(new_user.id, db)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    return {
        "id": new_user.id,
        "email": new_user.email,
        "name": new_user.name,
        "message": "User registered successfully",
    }


@app.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(rate_limit("login", 10, 60))],
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    normalized_email = form_data.username.strip().lower()
    if not normalized_email or len(normalized_email) > 254 or len(form_data.password) > 128:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    rate_limiter.hit(f"login:account:{normalized_email}", 10, 60)

    db_user = (
        db.query(User).filter(func.lower(User.email) == normalized_email).first()
    )
    if not db_user or not verify_password(form_data.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get("/stats", response_model=StatsOut)
def get_stats(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    progress = db.query(Progress).filter(Progress.user_id == user_id).first()
    return _stats_out(progress)


@app.post(
    "/game/start",
    response_model=GameStartResponse,
    dependencies=[Depends(rate_limit("game_start", 30, 60))],
)
def start_game(
    payload: GameStartRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    completed_lessons = _get_completed_lesson_ids(user_id, db)

    if payload.mode == "lesson":
        if payload.lesson_id is None or payload.lesson_id not in LESSON_META:
            raise HTTPException(status_code=400, detail="Valid lesson_id is required")

        highest_completed = max(completed_lessons, default=0)
        if payload.lesson_id > highest_completed + 1:
            raise HTTPException(status_code=403, detail="Lesson is locked")

        topic, lesson_diff = LESSON_META[payload.lesson_id]
        primary = (
            db.query(Question)
            .filter(
                Question.is_lesson == 1,
                Question.subject == topic,
                Question.difficulty == lesson_diff,
            )
            .all()
        )
        shuffle(primary)
        selected = primary[:5]

        if len(selected) < 5:
            selected_ids = {q.id for q in selected}
            fallback_query = db.query(Question).filter(
                Question.is_lesson == 1,
                Question.subject == topic,
            )
            if selected_ids:
                fallback_query = fallback_query.filter(~Question.id.in_(selected_ids))
            fallback = fallback_query.all()
            shuffle(fallback)
            selected.extend(fallback[: 5 - len(selected)])

        ttl = timedelta(minutes=30)
        subject = topic
        lesson_id = payload.lesson_id
    else:
        if not completed_lessons:
            raise HTTPException(
                status_code=403,
                detail="Complete at least one lesson to unlock the Arena",
            )

        if payload.mode == "normal":
            if not payload.subject:
                raise HTTPException(status_code=400, detail="Subject is required for normal mode")
            unlocked_topics = {LESSON_META[lid][0] for lid in completed_lessons}
            if payload.subject not in unlocked_topics:
                raise HTTPException(status_code=403, detail="Subject is locked")
            query = db.query(Question).filter(
                Question.is_game == 1,
                Question.subject == payload.subject,
            )
            count = 10
            ttl = timedelta(minutes=30)
            subject = payload.subject
        else:
            if len(completed_lessons) < len(LESSON_META):
                raise HTTPException(
                    status_code=403,
                    detail="Complete all lessons to unlock this mode",
                )
            query = db.query(Question).filter(Question.is_game == 1)
            if payload.mode == "challenge":
                query = query.filter(Question.difficulty <= 2)
                count = 10
                ttl = timedelta(minutes=10)
            elif payload.mode == "apocalypse":
                query = query.filter(Question.difficulty <= 3)
                count = 30
                ttl = timedelta(seconds=90)
            else:
                count = 10
                ttl = timedelta(minutes=30)
            subject = None

        pool = query.all()
        shuffle(pool)
        selected = pool[:count]
        lesson_id = None

    if not selected:
        raise HTTPException(status_code=404, detail="No questions available for this mode")

    now = _utc_now()
    session = GameSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        mode=payload.mode,
        lesson_id=lesson_id,
        subject=subject,
        question_ids=[q.id for q in selected],
        answered_ids=[],
        correct_count=0,
        total_answered=0,
        score=0,
        current_streak=0,
        best_streak=0,
        lives=3,
        status="active",
        finalized=False,
        created_at=now,
        expires_at=now + ttl,
    )
    db.add(session)
    db.commit()

    return GameStartResponse(
        session_id=session.id,
        mode=session.mode,
        questions=[QuestionOut.model_validate(q) for q in selected],
    )


@app.post(
    "/game/{session_id}/answer",
    response_model=AnswerSubmitResponse,
    dependencies=[Depends(rate_limit("game_answer", 120, 60))],
)
def submit_answer(
    session_id: str,
    payload: AnswerSubmitRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(GameSession)
        .filter(GameSession.id == session_id, GameSession.user_id == user_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")

    if session.status != "active":
        raise HTTPException(status_code=400, detail="Game session is no longer active")

    if _utc_now() > _as_utc(session.expires_at):
        session.status = "ended" if session.mode == "apocalypse" else "lost"
        db.commit()
        raise HTTPException(status_code=400, detail="Game session has expired")

    answered_list = list(session.answered_ids or [])
    question_ids = list(session.question_ids or [])
    if not question_ids:
        raise HTTPException(status_code=400, detail="Invalid session state")

    if session.mode == "apocalypse":
        expected_idx = len(answered_list) % len(question_ids)
    else:
        if len(answered_list) >= len(question_ids):
            raise HTTPException(status_code=400, detail="All questions already answered")
        expected_idx = len(answered_list)

    expected_question_id = question_ids[expected_idx]
    if payload.question_id != expected_question_id:
        raise HTTPException(status_code=400, detail="Unexpected question for current step")

    question = db.get(Question, payload.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    is_correct = payload.selected_index == question.correct_index

    answered_list.append(payload.question_id)
    session.answered_ids = answered_list
    session.total_answered += 1

    progress = _ensure_progress(user_id, db)
    progress.total_questions += 1

    points_earned = 0
    if is_correct:
        progress.correct_answers += 1
        session.correct_count += 1
        session.current_streak += 1
        session.best_streak = max(session.best_streak, session.current_streak)
        if session.mode != "lesson":
            points_earned = 10 if session.mode == "normal" else 20
            session.score += points_earned
    else:
        session.lives = max(0, session.lives - 1)
        session.current_streak = 0

    if session.lives <= 0:
        session.status = "lost"
    elif session.mode != "apocalypse" and len(answered_list) >= len(question_ids):
        session.status = "won"

    if session.mode in ("normal", "mixed", "challenge", "apocalypse"):
        leaderboard = initialize_leaderboard_entry(user_id, db)
        if is_correct:
            leaderboard.total_score += points_earned
            leaderboard.highest_streak = max(leaderboard.highest_streak, session.best_streak)
        leaderboard.average_accuracy = (
            round((progress.correct_answers / progress.total_questions) * 100, 2)
            if progress.total_questions > 0
            else 0.0
        )

    db.commit()

    return AnswerSubmitResponse(
        is_correct=is_correct,
        correct_index=question.correct_index,
        points_earned=points_earned,
        score=session.score,
        streak=session.current_streak,
        best_streak=session.best_streak,
        lives=session.lives,
        status=session.status,
    )


@app.post(
    "/game/{session_id}/timeout",
    response_model=GameTimeoutResponse,
    dependencies=[Depends(rate_limit("game_timeout", 60, 60))],
)
def handle_game_timeout(
    session_id: str,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(GameSession)
        .filter(GameSession.id == session_id, GameSession.user_id == user_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")

    if session.status != "active":
        return GameTimeoutResponse(
            lives=session.lives,
            score=session.score,
            best_streak=session.best_streak,
            status=session.status,
        )

    if session.mode == "apocalypse":
        session.status = "ended"
    elif session.mode == "challenge":
        answered_list = list(session.answered_ids or [])
        question_ids = list(session.question_ids or [])
        if len(answered_list) < len(question_ids):
            answered_list.append(question_ids[len(answered_list)])
            session.answered_ids = answered_list

        session.lives = max(0, session.lives - 1)
        session.current_streak = 0

        if session.lives <= 0:
            session.status = "lost"
        elif len(answered_list) >= len(question_ids):
            session.status = "won"
    else:
        raise HTTPException(status_code=400, detail="Timeout only applies to timed modes")

    db.commit()

    return GameTimeoutResponse(
        lives=session.lives,
        score=session.score,
        best_streak=session.best_streak,
        status=session.status,
    )


@app.post(
    "/game/{session_id}/finish",
    response_model=GameFinishResponse,
    dependencies=[Depends(rate_limit("game_finish", 30, 60))],
)
def finish_game(
    session_id: str,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(GameSession)
        .filter(GameSession.id == session_id, GameSession.user_id == user_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")

    if session.status == "active":
        if session.mode == "apocalypse" and _utc_now() >= _as_utc(session.expires_at):
            session.status = "ended"
        else:
            raise HTTPException(status_code=400, detail="Game session is still active")

    # Atomically claim finalization so a session cannot be scored twice concurrently
    claimed = (
        db.query(GameSession)
        .filter(
            GameSession.id == session.id,
            GameSession.user_id == user_id,
            GameSession.finalized.is_(False),
        )
        .update({"finalized": True}, synchronize_session=False)
    )

    progress = _ensure_progress(user_id, db)
    stars: int | None = None

    if session.mode == "lesson" and session.status == "won" and session.lesson_id is not None:
        total_q = max(1, len(session.question_ids or []))
        if session.correct_count >= total_q:
            stars = 3
        elif session.correct_count >= total_q - 1:
            stars = 2
        else:
            stars = 1

        if claimed == 1:
            lp = (
                db.query(LessonProgress)
                .filter(
                    LessonProgress.user_id == user_id,
                    LessonProgress.lesson_id == session.lesson_id,
                )
                .first()
            )
            if lp:
                lp.stars = max(lp.stars, stars)
                lp.completed = 1
            else:
                db.add(
                    LessonProgress(
                        user_id=user_id,
                        lesson_id=session.lesson_id,
                        stars=stars,
                        completed=1,
                    )
                )
            db.flush()
            progress.lessons_completed = (
                db.query(LessonProgress)
                .filter(LessonProgress.user_id == user_id, LessonProgress.completed >= 1)
                .count()
            )
    elif session.mode in ("normal", "mixed", "challenge", "apocalypse") and claimed == 1:
        progress.games_played += 1
        if session.mode == "challenge":
            progress.challenge_high_score = max(progress.challenge_high_score, session.score)
            progress.challenge_best_streak = max(progress.challenge_best_streak, session.best_streak)
        elif session.mode == "apocalypse":
            progress.apocalypse_high_score = max(progress.apocalypse_high_score, session.score)
            progress.apocalypse_best_streak = max(progress.apocalypse_best_streak, session.best_streak)

        leaderboard = initialize_leaderboard_entry(user_id, db)
        leaderboard.games_played += 1
        if session.status == "won":
            leaderboard.games_won += 1
        leaderboard.highest_streak = max(leaderboard.highest_streak, session.best_streak)
        leaderboard.average_accuracy = (
            round((progress.correct_answers / progress.total_questions) * 100, 2)
            if progress.total_questions > 0
            else 0.0
        )

    db.commit()
    db.refresh(progress)

    return GameFinishResponse(
        status=session.status,
        score=session.score,
        best_streak=session.best_streak,
        stars=stars,
        stats=_stats_out(progress),
    )


@app.get(
    "/leaderboard/global",
    response_model=list[LeaderboardResponse],
    dependencies=[Depends(rate_limit("leaderboard_read", 240, 60))],
)
def get_global_leaderboard(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    _user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get global leaderboard with pagination."""
    leaderboard_entries = (
        db.query(Leaderboard)
        .join(User, Leaderboard.user_id == User.id)
        .options(joinedload(Leaderboard.user))
        .order_by(Leaderboard.total_score.desc(), Leaderboard.last_updated.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for i, entry in enumerate(leaderboard_entries):
        result.append(
            LeaderboardResponse(
                rank=skip + i + 1,
                user_name=entry.user.name,
                score=entry.total_score,
                games_won=entry.games_won,
                games_played=entry.games_played,
                accuracy=round(entry.average_accuracy, 2),
                streak=entry.highest_streak,
            )
        )

    return result


@app.get(
    "/leaderboard/my-rank",
    response_model=UserRankResponse,
    dependencies=[Depends(rate_limit("leaderboard_read", 240, 60))],
)
def get_my_rank(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's rank on leaderboard."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    leaderboard = initialize_leaderboard_entry(user_id, db)
    db.commit()

    rank = (
        db.query(Leaderboard)
        .filter(Leaderboard.total_score > leaderboard.total_score)
        .count()
        + 1
    )
    total_players = db.query(Leaderboard).count()

    return UserRankResponse(
        user_rank=rank,
        total_players=total_players,
        user_score=leaderboard.total_score,
        user_name=user.name,
    )


@app.get(
    "/leaderboard/top-10",
    dependencies=[Depends(rate_limit("leaderboard_read", 240, 60))],
)
def get_top_10(
    _user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get top 10 players with quick access."""
    top_players = (
        db.query(Leaderboard)
        .join(User, Leaderboard.user_id == User.id)
        .options(joinedload(Leaderboard.user))
        .order_by(Leaderboard.total_score.desc(), Leaderboard.last_updated.asc())
        .limit(10)
        .all()
    )

    result = []
    for rank, entry in enumerate(top_players, start=1):
        result.append(
            {
                "rank": rank,
                "name": entry.user.name,
                "score": entry.total_score,
                "accuracy": round(entry.average_accuracy, 2),
            }
        )

    return result


@app.get(
    "/leaderboard/user/{user_name}",
    dependencies=[Depends(rate_limit("leaderboard_read", 240, 60))],
)
def get_user_leaderboard(
    user_name: str,
    _user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get specific user's leaderboard stats."""
    cleaned_name = user_name.strip()
    if not cleaned_name or len(cleaned_name) > 64:
        raise HTTPException(status_code=400, detail="Invalid username")

    user = (
        db.query(User)
        .filter(func.lower(User.name) == cleaned_name.lower())
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    leaderboard = initialize_leaderboard_entry(user.id, db)
    db.commit()

    rank = (
        db.query(Leaderboard)
        .filter(Leaderboard.total_score > leaderboard.total_score)
        .count()
        + 1
    )

    return {
        "rank": rank,
        "name": user.name,
        "score": leaderboard.total_score,
        "games_won": leaderboard.games_won,
        "games_played": leaderboard.games_played,
        "accuracy": round(leaderboard.average_accuracy, 2),
        "streak": leaderboard.highest_streak,
    }
