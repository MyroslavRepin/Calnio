from backend.app.db.session import engine
from backend.app.db.base_class import Base
import backend.app.models.users


def create_tables():
    print("Создаю таблицы...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы")


if __name__ == "__main__":
    create_tables()
