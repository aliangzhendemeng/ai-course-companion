"""初始化数据库脚本。"""

from backend.database import create_db_and_tables


def main() -> None:
    """创建数据库表。"""
    create_db_and_tables()
    print("✅ 数据库初始化完成")


if __name__ == "__main__":
    main()
