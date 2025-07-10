from tabulate import tabulate
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.app.models.users import User
from backend.app.schemas.users import UserCreate
from hashlib import sha256


def get_users(db: Session):
    return db.query(User).all()


def print_users_table(users):
    rows = []
    for u in users:
        rows.append([u.id, u.username, u.email, u.is_superuser])
    print(tabulate(rows, headers=["ID", "Username",
          "Email", "Is Admin"], tablefmt="psql"))


def create_user(db: Session, user: UserCreate):
    try:
        hashed_password = sha256(user.password.encode()).hexdigest()
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,
            is_superuser=user.is_superuser
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "❌ Пользователь с таким email или username уже существует")


def delete_by_id(db: Session, user_id):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
