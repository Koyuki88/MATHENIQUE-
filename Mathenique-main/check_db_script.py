from backend.database import SessionLocal, engine
from backend.models import User, Leaderboard, Progress

def inspect_db():
    print(f"Connecting to database: {engine.url}")
    db = SessionLocal()
    try:
        print("\n=== DATABASE INSPECTION ===")
        
        # Check Users
        users = db.query(User).all()
        print(f"\n[USERS] Total: {len(users)}")
        for u in users:
            print(f" - ID: {u.id}, Name: {u.name}, Email: {u.email}")

        # Check Leaderboard
        entries = db.query(Leaderboard).all()
        print(f"\n[LEADERBOARD] Total Entries: {len(entries)}")
        for e in entries:
            # Fetch associated user
            user = db.query(User).filter(User.id == e.user_id).first()
            name = user.name if user else "Unknown"
            print(f" - User: {name:<15} | Score: {e.total_score:<5} | Games: {e.games_played} | Streak: {e.highest_streak}")

    except Exception as e:
        print(f"Error checking DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_db()
