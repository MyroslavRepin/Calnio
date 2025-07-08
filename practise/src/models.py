from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

metadata_obj = MetaData()

workers_table = Table(
    'workers',
    metadata_obj,
    Column('uuid', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column('username', String),
)
