from sqlalchemy import func

from backend.database import SessionLocal, engine
from backend.models import Leaderboard, Progress, User


def _mask_email(email: str) -> str:
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    prefix = local[:2] if len(local) > 2 else local[:1]
    return f"{prefix}***@{domain}"


def inspect_db():
    print(f"Connecting to database: {engine.url.render_as_string(hide_password=True)}")
    db = SessionLocal()
    try:
        print("\n=== DATABASE INSPECTION ===")

        total_users = db.query(User).count()
        total_progress = db.query(Progress).count()
        total_lb = db.query(Leaderboard).count()
        print(f"\n[SUMMARY] Users: {total_users} | Progress rows: {total_progress} | Leaderboard rows: {total_lb}")

        # Check duplicate usernames
        dupes = (
            db.query(func.lower(User.name), func.count(User.id))
            .group_by(func.lower(User.name))
            .having(func.count(User.id) > 1)
            .all()
        )
        if dupes:
            print(f"[WARNING] Duplicate usernames found: {dupes}")

        # Show sample users (non-simulated + first 10 overall)
        sample_users = db.query(User).order_by(User.id.asc()).limit(10).all()
        print("\n[USERS SAMPLE (first 10)]")
        for u in sample_users:
            print(f" - ID: {u.id}, Name: {u.name}, Email: {_mask_email(u.email)}")

        # Show Top 15 Leaderboard
        top_entries = (
            db.query(Leaderboard, User)
            .join(User, Leaderboard.user_id == User.id)
            .order_by(Leaderboard.total_score.desc(), Leaderboard.last_updated.asc())
            .limit(15)
            .all()
        )
        print(f"\n[LEADERBOARD TOP 15 of {total_lb}]")
        for rank, (e, user) in enumerate(top_entries, start=1):
            print(
                f" #{rank:<2} {user.name:<20} | Score: {e.total_score:<5} | "
                f"Wins: {e.games_won}/{e.games_played} | Acc: {e.average_accuracy:.1f}% | Streak: {e.highest_streak}"
            )

    except Exception as e:
        print(f"Error checking DB: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    inspect_db()
