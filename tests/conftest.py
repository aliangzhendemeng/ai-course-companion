"""pytest 配置。"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest


@pytest.fixture(scope="function")
def reset_database(tmp_path, monkeypatch):
    """为每个测试创建独立的数据库，并重新初始化 engine。"""
    db_file = tmp_path / "test.db"
    monkeypatch.setattr("backend.config.settings.database_url", f"sqlite:///{db_file}")

    # 重新创建 engine 与表
    from backend import database
    from sqlmodel import SQLModel, create_engine

    new_engine = create_engine(
        f"sqlite:///{db_file}",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    database.engine = new_engine
    SQLModel.metadata.create_all(new_engine)
    yield new_engine
