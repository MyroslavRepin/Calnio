from sqlalchemy.orm import Session
from backend.app.models.users import User
from backend.app.schemas.users import UserCreate
from hashlib import sha256


def get_users(db: Session):
    return db.query(User).all()


def create_user(db: Session, user: UserCreate):
    hashed_password = sha256(user.password.encode()).hexdigest()
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
