#!/bin/bash

# 微信公众号RSS新闻机器人启动脚本

set -e

# 检查是否在正确的目录
if [ ! -f "app.py" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 错误: 虚拟环境不存在，请先运行 install.sh"
    exit 1
fi

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "❌ 错误: .env 配置文件不存在，请先运行 install.sh"
    exit 1
fi

# 检查是否配置了必要参数
if grep -q "your_app_id\|your_app_secret\|your_token\|your_password" .env; then
    echo "⚠️ 警告: 请先在 .env 文件中配置实际参数"
    echo "需要配置的项:"
    echo "   - WECHAT_APP_ID"
    echo "   - WECHAT_APP_SECRET"
    echo "   - WECHAT_TOKEN"
    echo "   - DB_PASSWORD"
    echo ""
    read -p "是否继续启动? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 初始化数据库
echo "🗄️ 初始化数据库..."
python3 init_db.py

# 检查启动模式
MODE=${1:-development}
DAEMON=${2:-false}

echo "🚀 启动模式: $MODE"
echo "📊 后台运行: $DAEMON"

if [ "$MODE" = "production" ]; then
    export FLASK_ENV=production
    export FLASK_DEBUG=False
    echo "🏭 生产环境模式"
else
    export FLASK_ENV=development
    export FLASK_DEBUG=True
    echo "🛠️ 开发环境模式"
fi

# 启动应用
if [ "$DAEMON" = "true" ]; then
    echo "🔄 后台启动应用..."
    nohup python3 app.py > logs/app.log 2>&1 &
    echo $! > app.pid
    echo "✅ 应用已在后台启动，PID: $(cat app.pid)"
    echo "📋 查看日志: tail -f logs/app.log"
    echo "🛑 停止应用: ./stop.sh"
else
    echo "🔄 前台启动应用..."
    echo "📋 按 Ctrl+C 停止应用"
    python3 app.py
fi