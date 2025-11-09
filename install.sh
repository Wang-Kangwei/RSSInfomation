#!/bin/bash

# 微信公众号RSS新闻机器人安装脚本

set -e

echo "🚀 开始安装微信公众号RSS新闻机器人..."

# 检查Python版本
echo "📋 检查Python版本..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python版本检查通过: $python_version"
else
    echo "❌ Python版本过低，需要3.8或更高版本，当前版本: $python_version"
    exit 1
fi

# 检查并安装pip
echo "📦 检查pip..."
if ! command -v pip3 &> /dev/null; then
    echo "📦 安装pip..."
    python3 -m ensurepip --upgrade
fi

# 创建虚拟环境
echo "🐍 创建Python虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "⬆️ 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📚 安装Python依赖包..."
pip install -r requirements.txt

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs
mkdir -p data

# 复制配置文件
echo "⚙️ 创建配置文件..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ 已创建 .env 配置文件"
    echo "📝 请编辑 .env 文件配置您的微信公众号和数据库信息"
else
    echo "✅ .env 配置文件已存在"
fi

# 设置文件权限
echo "🔐 设置文件权限..."
chmod +x *.sh
chmod 600 .env

# 检查配置文件
echo "🔍 检查配置文件..."
if grep -q "your_app_id\|your_app_secret\|your_token\|your_password" .env; then
    echo "⚠️ 警告: 请在 .env 文件中配置您的实际参数"
    echo "📝 需要配置的项:"
    echo "   - WECHAT_APP_ID"
    echo "   - WECHAT_APP_SECRET"
    echo "   - WECHAT_TOKEN"
    echo "   - DB_PASSWORD"
fi

# 运行测试
echo "🧪 运行基本测试..."
python3 init_db.py

echo ""
echo "🎉 安装完成！"
echo ""
echo "📋 下一步操作:"
echo "1. 编辑 .env 文件，配置微信公众号和数据库信息"
echo "2. 确保MySQL数据库已启动并创建了数据库"
echo "3. 运行 'python3 init_db.py' 初始化数据库"
echo "4. 运行 'python3 app.py' 启动应用"
echo ""
echo "📚 更多信息请查看 README.md 文件"