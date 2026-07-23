"""SQLModel 数据库连接与会话管理。"""

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from backend.config import settings

# SQLite URL 使用项目根目录下的绝对路径，避免因工作目录不同导致找不到数据库文件
db_path = settings.resolve_path(settings.database_url.replace("sqlite:///./", "").replace("sqlite:///", ""))
db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{db_path}",
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
