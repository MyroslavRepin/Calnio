from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from database import Base


class WorkersOrm(Base):
    __tablename__ = 'workers'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column()
