# RSSInfomation

基于微信公众号的RSS科技/AI新闻收集和展示系统

## 项目简介

RSSInfomation是一个自动化的RSS新闻收集系统，专为微信公众号设计。系统能够自动从多个科技和AI相关的RSS源收集新闻，并通过微信公众号自动回复功能向用户展示当日最新资讯。

## 主要功能

- 🔄 **自动RSS收集**: 每日定时从多个RSS源收集科技/AI新闻
- 🗄️ **数据管理**: 智能去重，自动清理7天前的旧数据
- 📱 **微信集成**: 通过微信公众号自动回复展示新闻
- ⚙️ **灵活配置**: 支持动态添加/管理RSS源
- 📊 **数据统计**: 提供新闻收集和展示统计功能
- 🔍 **内容搜索**: 支持标题和内容的全文搜索

## 技术栈

- **后端**: Python 3.8+, Flask
- **数据库**: MySQL 8.0+, SQLAlchemy
- **定时任务**: APScheduler
- **RSS解析**: feedparser
- **微信公众号**: wechatpy

## 🔧 环境要求

- **Python**: 3.8+ (当前环境: 3.9.6)
- **数据库**: MySQL 8.0+
- **依赖**: 所有依赖包已安装完成

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd RSSInfomation

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置文件，填入数据库和微信配置
nano .env
```

**需要配置的关键信息：**

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=rss_news

# 微信公众号配置
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
WECHAT_TOKEN=your_token
WECHAT_ENCODING_AES_KEY=your_encoding_aes_key

# 系统配置
RSS_COLLECT_HOUR=5              # RSS收集时间（小时，默认凌晨5点）
NEWS_RETENTION_DAYS=7          # 新闻保留天数
MAX_NEWS_PER_SOURCE=10         # 每个RSS源最大新闻数量（默认10条）
LOG_LEVEL=INFO                 # 日志级别
FLASK_ENV=development          # Flask环境
SECRET_KEY=your_secret_key_here # Flask密钥
```

### 3. 数据库准备

```bash
# 确保MySQL服务运行
brew services start mysql  # macOS
# 或
sudo systemctl start mysql  # Linux

# 创建数据库
mysql -u root -p
CREATE DATABASE rss_news CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT
```

### 4. 初始化数据库

```bash
# 创建数据库表
/usr/bin/python3 manage.py create-tables
```

## 🎯 运行方式

### 方式一：开发环境运行

#### 步骤1: 初始化数据库
```bash
/usr/bin/python3 manage.py create-tables
```

#### 步骤2: 启动Web应用
```bash
/usr/bin/python3 app.py
```
- **访问地址**: `http://localhost:5000`
- **调试模式**: 开发环境默认开启
- **日志输出**: 控制台实时显示

#### 步骤3: 启动RSS收集调度器
在新的终端窗口中运行：
```bash
/usr/bin/python3 scheduler.py
```
- **定时收集**: 每天早上5点自动执行
- **手动停止**: 按 `Ctrl+C` 停止调度器
- **状态监控**: 控制台显示调度状态

### 方式二：生产环境运行

#### 使用管理脚本
```bash
# 初始化数据库
/usr/bin/python3 manage.py init-db

# 创建数据库表
/usr/bin/python3 manage.py create-tables

# 测试新闻功能
/usr/bin/python3 manage.py test-news --count 5
```

#### 使用生产级服务器
```bash
# 安装gunicorn (如果未安装)
pip install gunicorn

# 启动Web服务
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"

# 使用supervisor管理调度器
supervisord -c supervisor.conf
```

## 📱 微信公众号配置

### 1. 服务器配置
- **URL**: `http://your-domain.com/wechat`
- **Token**: 与 `.env` 文件中的 `WECHAT_TOKEN` 一致
- **EncodingAESKey**: 与 `.env` 文件中的配置一致
- **消息加解密方式**: 选择安全模式

### 2. 功能验证
```bash
# 测试新闻格式化
/usr/bin/python3 manage.py test-news --count 3

# 检查日志
tail -f logs/app.log
```

## 🛠️ 可用命令

### 数据库管理
```bash
/usr/bin/python3 manage.py create-tables    # 创建数据库表
/usr/bin/python3 manage.py init-db          # 初始化数据库
```

### 功能测试
```bash
/usr/bin/python3 manage.py test-news        # 测试新闻展示功能
/usr/bin/python3 manage.py test-news --count 10  # 显示前10条新闻
/usr/bin/python3 manage.py collect-rss      # 手动触发RSS收集（调试用）
```

### RSS收集调试
```bash
# 手动触发RSS收集（无需等待定时任务）
/usr/bin/python3 manage.py collect-rss

# 查看收集结果
/usr/bin/python3 manage.py test-news --count 20

# 检查详细日志
tail -f logs/rss_collector.log
```

### 直接运行
```bash
/usr/bin/python3 app.py                     # 启动Web应用
/usr/bin/python3 scheduler.py               # 启动RSS调度器
```

## 🔧 调试方法

### RSS收集功能调试

为了方便调试RSS收集功能，无需等待凌晨5点的定时任务，系统提供了手动触发方式：

#### 1. 手动触发RSS收集
```bash
# 立即执行RSS收集，显示收集统计信息
/usr/bin/python3 manage.py collect-rss
```

该命令会输出以下信息：
- 处理的RSS源数量
- 新增新闻数量
- 更新新闻数量
- 错误数量（如有）

#### 2. 验证收集结果
```bash
# 查看收集到的新闻（默认前5条）
/usr/bin/python3 manage.py test-news

# 查看更多新闻（前20条）
/usr/bin/python3 manage.py test-news --count 20
```

#### 3. 调试流程建议
```bash
# 步骤1: 手动收集RSS
/usr/bin/python3 manage.py collect-rss

# 步骤2: 查看收集结果
/usr/bin/python3 manage.py test-news --count 10

# 步骤3: 查看详细日志（如有问题）
tail -f logs/rss_collector.log
```

这种调试方式特别适合开发阶段快速验证RSS收集功能，无需修改定时任务配置。

### 开发工具
```bash
# 代码格式化
black .

# 代码检查
flake8 .

# 运行测试
pytest tests/
```

## 📊 系统监控

### 日志文件位置
- **应用日志**: `logs/app.log`
- **RSS收集日志**: `logs/rss_collector.log`
- **微信接口日志**: `logs/wechat.log`
- **错误日志**: `logs/error.log`

### 监控指标
- RSS源可用性
- 数据收集成功率
- 微信API响应时间
- 数据库连接状态

### 健康检查
```bash
# 检查Web服务状态
curl http://localhost:5000/

# 检查微信接口
curl -X POST http://localhost:5000/wechat
```

## 🔄 RSS源配置

### 默认RSS源
系统预配置了以下科技/AI类RSS源：

**科技类：**
- 36氪: https://36kr.com/feed
- 虎嗅网: https://www.huxiu.com/rss/0.xml
- 钛媒体: https://www.tmtpost.com/feed
- 极客公园: https://www.geekpark.net/rss

**AI类：**
- 机器之心: https://www.jiqizhixin.com/rss
- 量子位: https://www.qbitai.com/feed
- OpenAI Blog: https://openai.com/blog/rss.xml

### 添加自定义RSS源
可以通过数据库直接添加新的RSS源：
```sql
INSERT INTO rss_sources (name, url, category, description)
VALUES ('源名称', 'RSS_URL', '分类', '描述');
```

## ⚠️ 常见问题与解决方案

### 1. 数据库连接失败
**错误**: `Access denied for user 'root'@'localhost'`
**解决**: 检查 `.env` 文件中的数据库配置是否正确

### 2. 微信接口验证失败
**错误**: `signature validation failed`
**解决**: 确保 `WECHAT_TOKEN` 与公众号后台配置一致

### 3. RSS收集失败
**错误**: `RSS source unreachable`
**解决**: 检查网络连接和RSS源URL是否有效

### 4. 端口占用
**错误**: `Address already in use`
**解决**:
```bash
# 查找占用端口的进程
lsof -i :5000

# 杀死进程
kill -9 PID
```

## 📈 性能优化建议

### 数据库优化
- 定期清理过期数据 (系统自动清理7天前的数据)
- 优化数据库索引
- 配置连接池

### 缓存策略
- 启用Redis缓存 (可选)
- RSS响应缓存
- 数据库查询结果缓存

### 监控告警
- 配置系统监控
- 设置异常告警
- 日志分析

## 🔧 数据库字符集配置

### 中文乱码问题解决

如果在使用MySQL命令行客户端查询时遇到中文乱码问题，请按以下步骤解决：

#### 1. 运行字符集诊断工具
```bash
# 检查当前数据库字符集配置
/usr/bin/python3 fix_charset.py
```

该工具会显示当前数据库、表的字符集配置，并提供修复选项。

#### 2. 修复数据库字符集
如果需要修复，在诊断工具提示时选择 'y'，工具会自动：
- 将数据库字符集修改为 `utf8mb4`
- 将所有表字符集修改为 `utf8mb4`
- 使用 `utf8mb4_unicode_ci` 排序规则

#### 3. 配置MySQL客户端
在MySQL配置文件中设置客户端字符集：

**Linux/macOS** (`~/.my.cnf`):
```ini
[client]
default-character-set = utf8mb4

[mysql]
default-character-set = utf8mb4
```

**Windows** (`my.ini`):
```ini
[client]
default-character-set = utf8mb4

[mysql]
default-character-set = utf8mb4
```

#### 4. 在MySQL命令行中设置
如果临时需要设置，可在MySQL命令行中执行：
```sql
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
```

#### 5. 重新创建数据库表
修复字符集后，建议重新创建数据库表以确保所有字段都使用正确的字符集：
```bash
/usr/bin/python3 manage.py create-tables
```

## 🔒 安全注意事项

1. **配置文件安全**: 确保 `.env` 文件不被提交到版本控制
2. **数据库安全**: 使用强密码，限制数据库访问权限
3. **微信API安全**: 定期更换API密钥
4. **网络安全**: 生产环境使用HTTPS

## 项目结构

```
RSSInfomation/
├── app.py                 # 应用主入口
├── manage.py             # 管理脚本
├── requirements.txt      # 生产依赖
├── requirements-dev.txt  # 开发依赖
├── config/              # 配置文件
├── core/                # 核心模块
├── models/              # 数据模型
│   ├── news.py          # 新闻数据模型（已移除summary字段）
│   ├── source.py        # RSS源数据模型
│   └── base.py          # 基础模型类
├── rss/                 # RSS收集模块
│   ├── collector.py     # RSS收集器（已移除summary处理）
│   ├── parser.py        # RSS解析器（已移除summary字段）
│   └── __init__.py
├── wechat/              # 微信接口模块
│   ├── formatter.py     # 消息格式化器（已移除summary显示）
│   └── __init__.py
├── services/            # 业务服务
│   ├── news_service.py  # 新闻服务（已移除summary搜索）
│   └── __init__.py
├── utils/               # 工具模块
│   ├── validators.py    # 数据验证器（已移除summary验证）
│   ├── helpers.py       # 辅助函数
│   ├── logger.py        # 日志工具
│   └── __init__.py
├── tests/               # 测试目录
└── logs/                # 日志目录
```

## 开发指南

详细的开发文档请参考：
- [需求文档.md](./需求文档.md) - 完整的需求说明
- [TODO.md](./TODO.md) - 详细的开发计划

## 📝 更新日志

### v1.1.1 (2024-10-26)
**修复**: RSS源表中文乱码问题
- 🔧 **数据库修复**: 修复`rss_sources`表`name`和`description`字段的中文乱码
- 🛠️ **配置优化**: 改进数据库连接配置，确保UTF8MB4编码正确处理
- 📊 **数据恢复**: 重新插入正确的中文RSS源数据
  - 36氪 (36氪科技媒体)
  - 虎嗅网 (虎嗅网科技资讯)
  - 机器之心 (机器之心AI媒体)
  - 量子位 (量子位AI资讯)

### v1.1.0 (2024-10-26)
**重大变更**: 移除新闻摘要字段
- 🗑️ **数据库**: 移除`news`表中的`summary`字段
- 🧹 **代码重构**: 清理所有与summary相关的代码
  - `models/news.py`: 移除summary字段定义
  - `rss/parser.py`: 移除NewsItem中的summary属性和_get_summary方法
  - `rss/collector.py`: 移除summary字段的数据保存
  - `services/news_service.py`: 移除search_news中的summary搜索条件
  - `wechat/formatter.py`: 移除微信消息格式化中的summary处理
  - `utils/validators.py`: 移除validate_summary方法和验证逻辑
- 🔍 **搜索优化**: 搜索功能现在基于标题和内容进行全文搜索
- 📱 **显示优化**: 微信消息格式更简洁，突出标题和来源信息

**技术影响**:
- 数据库存储空间减少
- 消息格式更紧凑，提升用户体验
- 代码结构更清晰，降低维护成本

**迁移指南**:
如需更新现有数据库，请手动执行：
```sql
ALTER TABLE news DROP COLUMN summary;
```

## 📞 技术支持

如遇到问题，请检查：
1. 日志文件中的错误信息
2. 配置文件是否正确
3. 网络连接是否正常
4. 数据库服务是否运行

---

## 许可证

MIT License

---

**文档版本**: v1.0
**创建日期**: 2024-10-26
**Python路径**: `/usr/bin/python3`
**项目路径**: `/Users/wangkangwei/workspace/MyInfomationRssProject/RSSInfomation`