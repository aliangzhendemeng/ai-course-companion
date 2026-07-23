#!/usr/bin/env bash
# 前端启动脚本：无论从哪里执行，都切换到项目根目录再启动
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

"$PROJECT_ROOT/venv/bin/python" "$PROJECT_ROOT/run_frontend.py"
