from app.core.config import settings
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.user import User


def main():
    db = SessionLocal()
    try:
        email = settings.admin_email.lower().strip()
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.role = "admin"
            user.status = "active"
            if settings.admin_password:
                user.password_hash = hash_password(settings.admin_password)
            print(f"Updated admin user: {email}")
        else:
            user = User(
                email=email,
                password_hash=hash_password(settings.admin_password),
                full_name=settings.admin_full_name,
                role="admin",
                status="active",
            )
            db.add(user)
            print(f"Created admin user: {email}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
