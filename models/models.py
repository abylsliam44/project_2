from datetime import datetime
from sqlalchemy import MetaData, Table, Column, Integer, String, TIMESTAMP, ForeignKey, Text, JSON, Float

metadata = MetaData()

# Модель таблицы пользователей
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String, nullable=False, unique=True),
    Column("phone", String, nullable=False),
    Column("password", String, nullable=False),
    Column("name", String, nullable=True),
    Column("city", String, nullable=True),
    Column("registered_at", TIMESTAMP, default=datetime.utcnow),
)

# Модель таблицы объявлений
shanyraks = Table(
    "shanyraks",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("type", String, nullable=False),
    Column("price", Integer, nullable=False),
    Column("address", String, nullable=False),
    Column("area", Float, nullable=False),
    Column("rooms_count", Integer, nullable=False),
    Column("description", Text, nullable=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
)

# Модель таблицы комментариев
comments = Table(
    "comments",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("content", Text, nullable=False),
    Column("created_at", TIMESTAMP, default=datetime.utcnow),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("shanyrak_id", Integer, ForeignKey("shanyraks.id"), nullable=False),
)
