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
    _migrate_conversations()


# 增量列迁移：(表名, 列名, 列定义)。已存在的列会被跳过。
_ADD_COLUMN_MIGRATIONS: list[tuple[str, str, str]] = [
    ("chatmessage", "course_ids", "VARCHAR"),
    ("question", "generated_at", "DATETIME"),
    ("question", "cleared_at", "DATETIME"),
    ("questionattempt", "question_generated_at", "DATETIME"),
    ("chatmessage", "conversation_id", "INTEGER"),
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


def _migrate_conversations() -> None:
    """把无 conversation_id 的旧 ChatMessage 按 (course_id, scope, course_ids) 分组，
    各组建一个 Conversation 并回填 conversation_id。幂等。

    分组键复用前端 contextKey 思路：course 用 course_id；set/all 用 course_ids。
    """
    from sqlalchemy import text

    with Session(engine) as session:
        # 自愈：清理无消息的空会话（历史迁移若因进程重启竞态留下残留）
        session.execute(
            text("DELETE FROM conversation WHERE id NOT IN "
                 "(SELECT DISTINCT conversation_id FROM chatmessage WHERE conversation_id IS NOT NULL)")
        )
        orphans = session.exec(
            text("SELECT id, course_id, scope, course_ids, role, content FROM chatmessage "
                 "WHERE conversation_id IS NULL ORDER BY id")
        ).all()
        if not orphans:
            session.commit()
            return

        # 分组
        groups: dict[tuple, list] = {}
        for row in orphans:
            mid, course_id, scope, course_ids, role, content = row
            if scope in ("set", "all") and course_ids:
                key = ("set", course_ids)  # set/all 按 course_ids 分
            else:
                key = ("course", str(course_id))
            groups.setdefault(key, []).append((mid, course_id, scope, course_ids, role, content))

        from backend.models import Conversation

        for key, rows in groups.items():
            course_id = rows[0][1]
            scope = rows[0][2]
            course_ids = rows[0][3]
            # 标题：首条 user 问题前 20 字
            first_user = next((r[5] for r in rows if r[4] == "user"), None)
            title = (first_user or "历史会话")[:20]
            conv = Conversation(course_id=course_id, title=title, scope=scope, course_ids=course_ids)
            session.add(conv)
            session.flush()  # 拿到 conv.id
            for (mid, *_rest) in rows:
                session.execute(
                    text("UPDATE chatmessage SET conversation_id = :cid WHERE id = :mid"),
                    {"cid": conv.id, "mid": mid},
                )
        session.commit()


def get_session() -> Session:
    """获取数据库会话。"""
    with Session(engine) as session:
        yield session
