"""SQLModel 数据库连接与会话管理。"""

from sqlmodel import Session, SQLModel, create_engine

from backend.config import settings

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    """创建所有数据表。"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """获取数据库会话。"""
    with Session(engine) as session:
        yield session
