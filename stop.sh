#!/bin/bash

# 微信公众号RSS新闻机器人停止脚本

set -e

echo "🛑 停止微信公众号RSS新闻机器人..."

# 检查PID文件
if [ -f "app.pid" ]; then
    PID=$(cat app.pid)
    echo "📋 找到应用进程 PID: $PID"

    # 检查进程是否存在
    if ps -p $PID > /dev/null 2>&1; then
        echo "🔄 正在停止进程..."
        kill $PID

        # 等待进程结束
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                echo "✅ 应用已停止"
                rm -f app.pid
                exit 0
            fi
            echo "⏳ 等待进程结束... ($i/10)"
            sleep 1
        done

        # 强制杀死进程
        echo "⚠️ 强制停止进程..."
        kill -9 $PID
        rm -f app.pid
        echo "✅ 应用已强制停止"
    else
        echo "⚠️ 进程不存在，清理PID文件"
        rm -f app.pid
    fi
else
    echo "📋 未找到PID文件，尝试查找相关进程..."

    # 查找Python进程
    PIDS=$(ps aux | grep "python3 app.py" | grep -v grep | awk '{print $2}')

    if [ -n "$PIDS" ]; then
        echo "🔄 找到相关进程: $PIDS"
        echo "🔄 停止进程..."
        echo "$PIDS" | xargs kill

        # 等待进程结束
        sleep 2

        # 再次检查
        REMAINING_PIDS=$(ps aux | grep "python3 app.py" | grep -v grep | awk '{print $2}')
        if [ -n "$REMAINING_PIDS" ]; then
            echo "⚠️ 强制停止剩余进程..."
            echo "$REMAINING_PIDS" | xargs kill -9
        fi

        echo "✅ 所有相关进程已停止"
    else
        echo "ℹ️ 未找到运行中的应用进程"
    fi
fi

# 清理临时文件
echo "🧹 清理临时文件..."
rm -f app.pid

echo "✅ 停止完成"