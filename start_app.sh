#!/usr/bin/env bash
#
# AI 慕课学伴 一键启动脚本（macOS / Linux）
#
# 功能：
#   - 同时启动后端（FastAPI, :8000）和前端（Next.js, :3000）
#   - 自动打开浏览器到前端页面
#   - Ctrl+C 退出时一并关闭两个进程
#   - 端口被占用、依赖缺失时给出友好提示
#
# 用法：
#   ./start_app.sh            启动（开发模式，前端热重载）
#   ./start_app.sh --no-open  启动但不自动打开浏览器
#

set -euo pipefail

# 切到脚本所在目录（项目根目录）
cd "$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

OPEN_BROWSER=true
for arg in "$@"; do
  case "$arg" in
    --no-open) OPEN_BROWSER=false ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
  esac
done

BACKEND_PORT=8000
FRONTEND_PORT=3000
BACKEND_PID=""
FRONTEND_PID=""

log() { printf '\033[1;36m[启动]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[错误]\033[0m %s\n' "$*" >&2; }

# 检查端口是否被占用，占用则给出提示并退出
check_port() {
  local port="$1" name="$2"
  if lsof -ti ":$port" >/dev/null 2>&1; then
    err "端口 $port 已被占用（$name 需要）。"
    err "  可能上次未正常退出。可执行：  lsof -ti :$port | xargs kill"
    err "  或确认是否有其他程序占用了该端口。"
    exit 1
  fi
}

# 退出时清理两个进程
cleanup() {
  echo ""
  log "正在关闭服务…"
  # 按 PID 关闭（含其子进程树）
  [ -n "$BACKEND_PID" ]  && pkill -TERM -P "$BACKEND_PID"  2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && pkill -TERM -P "$FRONTEND_PID" 2>/dev/null || true
  [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  # 兜底：next dev 会 fork 出独立子进程，按端口与命令名确保清理干净
  lsof -ti ":$BACKEND_PORT"  2>/dev/null | xargs kill 2>/dev/null || true
  lsof -ti ":$FRONTEND_PORT" 2>/dev/null | xargs kill 2>/dev/null || true
  pkill -f "next dev -p $FRONTEND_PORT" 2>/dev/null || true
  wait 2>/dev/null || true
  log "已退出。"
}
trap cleanup INT TERM EXIT

# ---- 依赖检查 ----
if [ ! -d "venv" ]; then
  err "未找到后端虚拟环境 venv/。请先创建并安装依赖："
  err "  python3 -m venv venv && ./venv/bin/pip install -r requirements.txt"
  exit 1
fi
if [ ! -d "frontend-next/node_modules" ]; then
  err "未找到前端依赖 frontend-next/node_modules。请先安装："
  err "  cd frontend-next && npm install"
  exit 1
fi

check_port "$BACKEND_PORT" "后端"
check_port "$FRONTEND_PORT" "前端"

# 离线加载 HuggingFace 模型，避免网络超时阻塞请求（Whisper/embedding 已缓存）
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

# ---- 启动后端 ----
log "启动后端  → http://localhost:$BACKEND_PORT"
./venv/bin/python run.py > /tmp/ai-course-backend.log 2>&1 &
BACKEND_PID=$!

# ---- 启动前端 ----
log "启动前端  → http://localhost:$FRONTEND_PORT"
( cd frontend-next && ./node_modules/.bin/next dev -p "$FRONTEND_PORT" ) > /tmp/ai-course-frontend.log 2>&1 &
FRONTEND_PID=$!

# ---- 等待前端就绪后打开浏览器 ----
if $OPEN_BROWSER; then
  (
    for _ in $(seq 1 60); do
      if curl -s -o /dev/null "http://localhost:$FRONTEND_PORT" 2>/dev/null; then
        log "打开浏览器…"
        if command -v open >/dev/null 2>&1; then
          open "http://localhost:$FRONTEND_PORT"          # macOS
        elif command -v xdg-open >/dev/null 2>&1; then
          xdg-open "http://localhost:$FRONTEND_PORT"      # Linux
        fi
        exit 0
      fi
      sleep 1
    done
    err "前端启动超时，请手动访问 http://localhost:$FRONTEND_PORT"
  ) &
fi

echo ""
log "两个服务已启动。按 Ctrl+C 停止。"
log "  后端日志: /tmp/ai-course-backend.log"
log "  前端日志: /tmp/ai-course-frontend.log"
echo ""

# 等待任一进程退出（保持脚本存活，便于 Ctrl+C 捕获）
wait
