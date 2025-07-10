from backend.app.db.database import engine, Base


def create_tables():
    print("Создаю таблицы...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы")


if __name__ == "__main__":
    create_tables()
