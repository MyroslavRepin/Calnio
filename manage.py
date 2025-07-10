import sys
from backend.app.db.check_db import check_connection
from backend.app.db.create_tables import create_tables
from backend.app.db.database import SessionLocal
from backend.app.schemas.users import UserCreate
from backend.app.crud.users import create_user, get_users, print_users_table
from backend.app.db.database import DATABASE_URL


def main():
    if len(sys.argv) < 2:
        print(
            "Использование: python manage.py [check|create|create_user|get_users]")
        return

    command = sys.argv[1]
    if command == "check":
        check_connection(DATABASE_URL)
    elif command == "create":
        create_tables()
    elif command == "get_users":
        db = SessionLocal()
        try:
            users = get_users(db)
            print_users_table(users)
        finally:
            db.close()

    elif command == 'create_user':
        try:
            user = UserCreate(username="testuser",
                              email="test@example.com", password="password123", is_superuser=True)
            user2 = UserCreate(username="jessica",
                               email="jesica@example.com", password="mikhaiel", is_superuser=False)
            # create_user(db=SessionLocal(), user=user)
            create_user(db=SessionLocal(), user=user2)
            print("✅ User created successfully.")
        finally:
            SessionLocal().close()
    else:
        print(f"Неизвестная команда: {command}")


if __name__ == "__main__":
    main()
