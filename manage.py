import sys
from backend.app.db.check_db import check_connection
from backend.app.db.create_tables import create_tables
from backend.app.db.database import SessionLocal
from backend.app.schemas.users import UserCreate
from backend.app.crud.users import create_user, get_users
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
        get_users(SessionLocal())
    elif command == 'create_user':
        try:
            user = UserCreate(username="testuser",
                              email="test@example.com", password="password123")
            create_user(db=SessionLocal(), user=user)
            print("✅ User created successfully.")
        finally:
            SessionLocal().close()
    else:
        print(f"Неизвестная команда: {command}")


if __name__ == "__main__":
    main()
