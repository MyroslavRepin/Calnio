from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

DATABASE_URL = "postgresql://myroslav:myroslav0818@localhost:5432/scheduloo"


def check_connection(url):
    try:
        engine = create_engine(url)
        # Пытаемся получить соединение
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Подключение успешно! Результат запроса:", result.scalar())
    except OperationalError as e:
        print("❌ Ошибка подключения:", e)


if __name__ == "__main__":
    check_connection(DATABASE_URL)
