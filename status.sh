#!/bin/bash

# 微信公众号RSS新闻机器人状态检查脚本

set -e

echo "📊 微信公众号RSS新闻机器人状态检查"
echo "=================================="

# 检查项目文件
echo "📁 检查项目文件..."
required_files=("app.py" "config.py" "models.py" "rss_collector.py" "scheduler.py")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (缺失)"
    fi
done

# 检查配置文件
echo ""
echo "⚙️ 检查配置文件..."
if [ -f ".env" ]; then
    echo "✅ .env 配置文件存在"

    # 检查配置完整性
    if grep -q "your_app_id\|your_app_secret\|your_token\|your_password" .env; then
        echo "⚠️ 警告: 配置文件包含默认值，需要更新为实际参数"
    else
        echo "✅ 配置文件已正确设置"
    fi
else
    echo "❌ .env 配置文件不存在"
fi

# 检查虚拟环境
echo ""
echo "🐍 检查Python虚拟环境..."
if [ -d "venv" ]; then
    echo "✅ 虚拟环境存在"

    # 检查虚拟环境是否激活
    if [ "$VIRTUAL_ENV" != "" ]; then
        echo "✅ 虚拟环境已激活"
    else
        echo "ℹ️ 虚拟环境未激活"
    fi
else
    echo "❌ 虚拟环境不存在"
fi

# 检查依赖包
echo ""
echo "📦 检查依赖包..."
if [ -d "venv" ]; then
    source venv/bin/activate

    # 检查关键依赖
    key_packages=("flask" "sqlalchemy" "feedparser" "wechatpy" "apscheduler")
    for package in "${key_packages[@]}"; do
        if python3 -c "import ${package}" 2>/dev/null; then
            echo "✅ ${package}"
        else
            echo "❌ ${package} (未安装)"
        fi
    done
else
    echo "❌ 无法检查依赖包 (虚拟环境不存在)"
fi

# 检查进程状态
echo ""
echo "🔄 检查应用进程状态..."
if [ -f "app.pid" ]; then
    PID=$(cat app.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 应用正在运行 (PID: $PID)"

        # 获取进程信息
        PROCESS_INFO=$(ps -p $PID -o pid,etime,pcpu,pmem --no-headers)
        echo "📊 进程信息: $PROCESS_INFO"
    else
        echo "❌ PID文件存在但进程未运行"
    fi
else
    # 查找Python进程
    PIDS=$(ps aux | grep "python3 app.py" | grep -v grep | awk '{print $2}')
    if [ -n "$PIDS" ]; then
        echo "⚠️ 发现运行中的进程但没有PID文件: $PIDS"
    else
        echo "ℹ️ 应用未运行"
    fi
fi

# 检查日志文件
echo ""
echo "📋 检查日志文件..."
if [ -f "logs/app.log" ]; then
    echo "✅ 应用日志文件存在"

    # 显示最后几行日志
    echo "📄 最近的日志记录:"
    tail -n 3 logs/app.log | sed 's/^/   /'
else
    echo "ℹ️ 应用日志文件不存在"
fi

# 检查数据库连接
echo ""
echo "🗄️ 检查数据库连接..."
if [ -f "app.py" ]; then
    if [ -d "venv" ]; then
        source venv/bin/activate

        # 尝试初始化数据库
        if python3 -c "
import sys
sys.path.append('.')
from config import Config
try:
    from models import db_manager
    db_manager.init_db()
    print('✅ 数据库连接正常')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
" 2>/dev/null; then
            echo "✅ 数据库连接测试通过"
        else
            echo "❌ 数据库连接测试失败"
        fi
    fi
fi

# 检查端口占用
echo ""
echo "🌐 检查端口占用..."
if command -v netstat &> /dev/null; then
    if netstat -tlnp 2>/dev/null | grep ":5000 " > /dev/null; then
        echo "✅ 端口 5000 已被监听"
        PORT_INFO=$(netstat -tlnp 2>/dev/null | grep ":5000 ")
        echo "📊 端口信息: $PORT_INFO"
    else
        echo "ℹ️ 端口 5000 未被监听"
    fi
elif command -v ss &> /dev/null; then
    if ss -tlnp 2>/dev/null | grep ":5000 " > /dev/null; then
        echo "✅ 端口 5000 已被监听"
    else
        echo "ℹ️ 端口 5000 未被监听"
    fi
else
    echo "ℹ️ 无法检查端口占用"
fi

# 检查HTTP服务
echo ""
echo "🌍 检查HTTP服务..."
if command -v curl &> /dev/null; then
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health | grep -q "200"; then
        echo "✅ HTTP服务正常响应"

        # 获取健康检查信息
        HEALTH_INFO=$(curl -s http://localhost:5000/health 2>/dev/null)
        if [ -n "$HEALTH_INFO" ]; then
            echo "📊 健康检查: $HEALTH_INFO"
        fi
    else
        echo "❌ HTTP服务无响应"
    fi
else
    echo "ℹ️ 无法检查HTTP服务 (curl未安装)"
fi

echo ""
echo "📋 状态检查完成"