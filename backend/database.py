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
    """创建所有数据表，并对已有表做幂等的增量列迁移。

    SQLite 的 create_all 只建新表、不给已有表加新列，因此新增的列在这里
    用 ALTER TABLE ... ADD COLUMN 逐个补齐（已存在则跳过）。
    """
    SQLModel.metadata.create_all(engine)
    _migrate_add_columns()


# 增量列迁移：(表名, 列名, 列定义)。已存在的列会被跳过。
_ADD_COLUMN_MIGRATIONS: list[tuple[str, str, str]] = [
    ("chatmessage", "course_ids", "VARCHAR"),
]


def _migrate_add_columns() -> None:
    """为已有表补充新列（幂等）。"""
    from sqlalchemy import text

    with engine.begin() as conn:
        for table, column, definition in _ADD_COLUMN_MIGRATIONS:
            existing = {
                row[1]
                for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
            }
            if column not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))


def get_session() -> Session:
    """获取数据库会话。"""
    with Session(engine) as session:
        yield session
