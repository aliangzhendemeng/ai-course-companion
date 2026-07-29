#!/usr/bin/env bash
#
# 【双击启动】AI 慕课学伴（macOS）
#
# 双击本文件即可在"终端"中启动应用并自动打开浏览器。
# 停止使用：在打开的终端窗口里按 Ctrl+C，前后端会一起关闭。
#
# 本文件只是 start_app.sh 的双击入口，出错时窗口不会立刻关闭，方便查看原因。

# 切到本脚本所在目录（项目根）
cd "$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 运行主启动脚本；无论成功或失败都不要立刻关窗
./start_app.sh
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -ne 0 ]; then
  echo "————————————————————————————"
  echo "启动未完成（退出码 $EXIT_CODE）。请把上面的提示截图反馈。"
else
  echo "服务已停止。"
fi
echo "按任意键关闭本窗口…"
read -n 1 -s -r
