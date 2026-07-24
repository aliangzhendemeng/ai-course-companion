#!/bin/bash
# 启动 Next.js 现代前端（开发模式）
set -e

cd "$(dirname "$0")/frontend-next"
npm run dev
