from app.database import SessionLocal
from app.models import User

db = SessionLocal()
users = db.query(User).all()
print(f"Total users: {len(users)}")
for user in users:
    print(f"- {user.email} ({user.username}) - Verified: {user.is_verified}")
db.close()