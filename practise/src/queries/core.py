from sqlalchemy import text, insert
from database import sync_engine, metadata_obj
import uuid


def create_tables():
    metadata_obj.drop_all(sync_engine)
    metadata_obj.create_all(sync_engine)
    # Base.metadata.create_all(sync_engine)


# def insert_data(username):
#     with sync_engine.connect() as conn:
#         stmt = insert(workers_table).values(
#             [{'uuid': uuid.uuid4(), 'username': username}])
#         conn.execute(stmt)
#         conn.commit()
