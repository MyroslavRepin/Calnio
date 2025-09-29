import asyncio
import sys
from dotenv import load_dotenv
from pathlib import Path
from backend.app.core.config import settings
from backend.app.crud import async_create_user, get_users, async_print_users_table, async_delete_by_id, async_update_by_id, async_update_password_by_id
from backend.app.schemas.users import UserCreate
from backend.app.db.database import AsyncSessionLocal
from backend.app.db.utils import async_check_connection, async_create_tables

dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path)
DATABASE_URL = settings.database_url


def main():
    if len(sys.argv) < 2:
        print(
            "Использование: python manage.py [check|create|create_user|get_users|delete_user|update_user|migrate|upgrade|downgrade]")
        return

    command = sys.argv[1]
    if command == "check":
        asyncio.run(async_check_connection())

    elif command == "create":
        asyncio.run(async_create_tables())

    elif command == "migrate":
        # Generate a new migration
        import subprocess
        migration_message = sys.argv[2] if len(sys.argv) > 2 else "Auto-generated migration"
        result = subprocess.run(["alembic", "revision", "--autogenerate", "-m", migration_message],
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Error:", result.stderr)

    elif command == "upgrade":
        # Apply migrations to database
        import subprocess
        result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Error:", result.stderr)

    elif command == "downgrade":
        # Downgrade database by one migration
        import subprocess
        target = sys.argv[2] if len(sys.argv) > 2 else "-1"
        result = subprocess.run(["alembic", "downgrade", target], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Error:", result.stderr)

    elif command == "get_users":
        async def async_get_users():
            async with AsyncSessionLocal() as db:
                users = await get_users(db)
                async_print_users_table(users)
        asyncio.run(async_get_users())

    elif command == 'create_user':
        async def create_user_async():
            try:
                user = UserCreate(username="bob", email="bob@example.com",
                                  hashed_password="bobking!", is_superuser=False)
                async with AsyncSessionLocal() as db:
                    await async_create_user(db, user=user)

            finally:
                print(f"✅ User created successfully.")
        asyncio.run(create_user_async())

    elif command == 'delete_user':
        async def delete_user_async():
            try:
                async with AsyncSessionLocal() as db:
                    await async_delete_by_id(db, 1)

            finally:
                print(f"✅ User deleted successfully.")
        asyncio.run(delete_user_async())

    elif command == 'update_user':
        async def update_user_async():
            try:
                async with AsyncSessionLocal() as db:
                    await async_update_by_id(db=db, user_id=6, new_username="bob_king", new_email="bobking@gmail.com")

            finally:
                print(f"✅ User updated successfully.")
        asyncio.run(update_user_async())
    elif command == 'update_password':
        async def update_user_async():
            try:
                async with AsyncSessionLocal() as db:
                    await async_update_password_by_id(db=db, user_id=13, new_password="new_password")

            finally:
                print(f"✅ User updated successfully.")
        asyncio.run(update_user_async())
    else:
        print(f"Неизвестная команда: {command}")


if __name__ == "__main__":
    main()
