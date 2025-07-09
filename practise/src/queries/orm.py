from sqlalchemy import text, insert
# from sqlalchemy.orm import Session
from database import sync_engine, session_factory, metadata_obj
from models import WorkersOrm


def create_tables():
    metadata_obj.drop_all(sync_engine)  # ❗ осторожно: это удалит все таблицы!
    metadata_obj.create_all(sync_engine)
    print("✅ Таблицы созданы!")


def insert_data():
    with session_factory() as session:
        bobr = WorkersOrm(username='Myroslav')
        bobr2 = WorkersOrm(username='artem')
        session.add(bobr)
        session.commit()
