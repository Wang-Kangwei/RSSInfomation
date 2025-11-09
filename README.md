# 微信公众号RSS新闻机器人

一个基于Python的自动化科技/AI新闻收集和微信公众号回复系统，通过RSS源定期获取最新资讯，并通过微信公众号的自动回复功能向用户展示。

## 功能特性

- 🤖 **自动化RSS收集**: 定时从多个RSS源收集科技/AI相关新闻
- 📱 **微信公众号集成**: 用户发送消息自动回复当日新闻
- 🗄️ **数据库管理**: 自动存储和管理7天内的新闻数据
- ⏰ **定时任务**: 每天早上5点自动执行RSS收集
- 🧹 **数据清理**: 自动删除超过7天的旧数据
- 🔄 **可扩展架构**: 支持动态添加新的RSS源
- 📊 **健康检查**: 提供系统状态监控接口

## 技术栈

- **后端框架**: Flask
- **数据库**: MySQL 8.0+
- **ORM**: SQLAlchemy
- **定时任务**: APScheduler
- **RSS解析**: feedparser
- **微信公众号**: wechatpy
- **配置管理**: python-dotenv
- **日志处理**: loguru

## 项目结构

```
RSSInfomation/
├── app.py                    # Flask主应用
├── config.py                 # 配置管理
├── models.py                 # 数据库模型
├── rss_collector.py          # RSS收集器
├── scheduler.py              # 定时任务调度器
├── logger_config.py          # 日志配置
├── init_db.py                # 数据库初始化
├── requirements.txt          # Python依赖
├── .env.example             # 环境配置模板
├── install.sh               # 安装脚本
├── start.sh                 # 启动脚本
├── stop.sh                  # 停止脚本
├── status.sh                # 状态检查脚本
├── run_tests.py             # 测试运行器
├── test_*.py                # 测试文件
├── test_framework.py        # 测试框架
└── README.md                # 项目说明
```

## 快速开始

### 1. 环境要求

- Python 3.8+
- MySQL 8.0+
- Linux/macOS/Windows

### 2. 安装步骤

```bash
# 克隆项目
git clone <repository-url>
cd RSSInfomation

# 运行安装脚本
chmod +x install.sh
./install.sh
```

### 3. 配置环境

编辑 `.env` 文件，配置以下参数：

```bash
# 微信公众号配置
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
WECHAT_TOKEN=your_token

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=news_bot

# 系统配置
RSS_COLLECT_TIME=05:00
DATA_RETENTION_DAYS=7
MAX_NEWS_PER_REPLY=10
```

### 4. 初始化数据库

```bash
# 创建MySQL数据库
mysql -u root -p -e "CREATE DATABASE news_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 初始化表结构和数据
python3 init_db.py
```

### 5. 启动应用

```bash
# 开发环境启动
./start.sh development

# 生产环境启动
./start.sh production

# 后台运行
./start.sh production true
```

## 使用说明

### 微信公众号设置

1. 登录微信公众号后台
2. 设置服务器地址为: `http://your-domain.com/wechat`
3. 配置Token为 `.env` 文件中的 `WECHAT_TOKEN`
4. 选择安全模式，填写 EncodingAESKey（可选）

### 管理命令

```bash
# 查看应用状态
./status.sh

# 停止应用
./stop.sh

# 重新启动
./stop.sh && ./start.sh production true

# 运行测试
python3 run_tests.py

# 手动收集新闻
curl -X POST http://localhost:5000/collect_news
```

### API接口

- `GET /wechat` - 微信公众号接口（验证）
- `POST /wechat` - 微信公众号接口（消息处理）
- `GET /health` - 健康检查
- `POST /collect_news` - 手动触发新闻收集
- `GET /news` - 获取新闻列表（支持category和limit参数）

## 配置说明

### RSS源配置

系统默认包含以下RSS源：

- TechCrunch
- AI News
- VentureBeat
- MIT Technology Review

可以通过数据库 `rss_sources` 表动态添加或修改RSS源。

### 定时任务配置

- **RSS收集**: 每天早上5点执行
- **数据清理**: 每天凌晨2点执行
- **数据保留**: 默认保留7天

### 微信消息格式

系统会自动格式化新闻为适合微信显示的格式：

```
📱 科技/AI新闻速递 📱
📅 2024年01月01日
⏰ 更新时间: 2024-01-01 10:00:00
──────────────────────────

🔬 科技新闻
1. 📰 新闻标题
   📝 新闻内容...
   🔗 新闻链接
   📤 来源: RSS源名称

🤖 AI新闻
1. 📰 AI新闻标题
   📝 AI新闻内容...
   🔗 AI新闻链接
   📤 来源: AI RSS源

──────────────────────────
💡 发送任意文字获取最新新闻
🔔 本消息每日自动更新
```

## 开发指南

### 运行测试

```bash
# 运行所有测试
python3 run_tests.py

# 运行特定模块测试
python3 run_tests.py models
python3 run_tests.py rss_collector
python3 run_tests.py app
```

### 开发环境设置

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装开发依赖
pip install -r requirements.txt

# 开发模式启动
export FLASK_ENV=development
export FLASK_DEBUG=True
python3 app.py
```

### 日志管理

日志文件位置：
- 应用日志: `logs/app.log`
- 错误日志: `logs/app_error.log`

日志级别：DEBUG/INFO/WARNING/ERROR

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务是否启动
   - 验证 `.env` 文件中的数据库配置
   - 确认数据库用户权限

2. **微信公众号验证失败**
   - 检查Token配置是否正确
   - 确认服务器地址可访问
   - 查看应用日志获取详细错误信息

3. **RSS收集失败**
   - 检查网络连接
   - 验证RSS源URL是否有效
   - 查看RSS收集器日志

4. **应用启动失败**
   - 检查端口5000是否被占用
   - 验证所有依赖是否正确安装
   - 运行 `./status.sh` 检查系统状态

### 日志分析

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/app_error.log

# 搜索特定错误
grep -i error logs/app.log
```

## 部署建议

### 生产环境部署

1. 使用Gunicorn或uWSGI作为WSGI服务器
2. 配置Nginx作为反向代理
3. 使用systemd管理服务进程
4. 配置SSL证书启用HTTPS
5. 设置日志轮转
6. 配置监控告警

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python3", "app.py"]
```

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 微信: [your-wechat-id]

---

**注意**: 本项目仅供学习和研究使用，请遵守相关API的使用条款和法律法规。