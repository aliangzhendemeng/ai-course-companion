#!/usr/bin/env bash
# 后端启动脚本：无论从哪里执行，都切换到项目根目录再启动
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 离线加载 HuggingFace 模型，避免网络超时阻塞请求
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

"$PROJECT_ROOT/venv/bin/python" "$PROJECT_ROOT/run.py"
