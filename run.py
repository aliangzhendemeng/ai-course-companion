"""项目启动入口：自动将项目根目录加入 sys.path 并启动后端服务。"""

import os
import sys
from pathlib import Path

# 切换到项目根目录，确保 .env、数据库路径和重载监听都正确
project_root = Path(__file__).resolve().parent
os.chdir(project_root)

# 将项目根目录加入 Python 模块搜索路径，避免 ModuleNotFoundError
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
