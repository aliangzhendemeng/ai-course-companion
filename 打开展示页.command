#!/bin/bash
cd "$(dirname "$0")/showcase"

# 清理已有的 Astro 进程，避免端口冲突
pkill -f "astro preview" 2>/dev/null || true
pkill -f "astro dev" 2>/dev/null || true
lsof -ti:4321 | xargs kill -9 2>/dev/null || true
sleep 1

npm run dev -- --port 4321 &
sleep 4
open http://localhost:4321/
wait
