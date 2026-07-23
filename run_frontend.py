"""前端启动入口：自动切换到项目根目录并启动 Streamlit。"""

import os
import subprocess
import sys
from pathlib import Path

# 切换到项目根目录，确保 .streamlit/config.toml 被正确读取
project_root = Path(__file__).resolve().parent
os.chdir(project_root)

# 使用当前 Python 解释器运行 streamlit
sys.argv = ["streamlit", "run", str(project_root / "frontend" / "Home.py")]

import streamlit.web.cli as stcli  # noqa: E402

if __name__ == "__main__":
    stcli.main()
