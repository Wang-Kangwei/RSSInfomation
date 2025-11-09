# 微信公众号RSS科技/AI新闻机器人产品需求文档 (PRD)

## 1. 产品概述

### 1.1 产品背景
个人微信公众号用户需要一个自动化的科技/AI新闻收集和展示系统，通过RSS源定期获取最新资讯，并通过微信公众号的自动回复功能向用户展示。

### 1.2 产品目标
- 实现RSS新闻的自动收集和存储
- 通过微信公众号自动回复功能展示当日新闻
- 提供可扩展的RSS源管理机制
- 确保系统稳定性和数据安全性

### 1.3 目标用户
- 个人微信公众号运营者
- 科技/AI资讯关注者
- 需要自动化新闻推送的用户

## 2. 功能需求

### 2.1 RSS新闻收集功能
- **功能描述**: 定时从多个RSS源收集科技/AI相关新闻
- **触发方式**: 每天早上5点自动执行
- **数据存储**: 存储最近7天的新闻数据
- **数据清理**: 自动删除超过7天的旧数据

### 2.2 微信公众号自动回复功能
- **功能描述**: 用户发送任意消息时，自动回复当日科技/AI新闻
- **展示内容**: 仅展示当天的新闻数据
- **响应方式**: 通过微信公众号自动回复接口实现

### 2.3 配置管理功能
- **功能描述**: 集中管理所有敏感配置信息
- **配置内容**:
  - 微信公众号API密钥
  - 数据库连接信息
  - RSS源列表
  - 系统运行参数

### 2.4 RSS源管理功能
- **功能描述**: 支持RSS源的动态管理和扩展
- **扩展性**: 方便后续添加新的RSS源
- **解耦设计**: RSS源与主业务逻辑分离

## 3. 技术架构

### 3.1 系统架构图
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   RSS Sources   │    │   Python App     │    │  WeChat API     │
│                 │────│                  │────│                 │
│ - TechCrunch    │    │ - RSS Collector  │    │ - Auto Reply    │
│ - AI News       │    │ - Data Processor │    │   Interface     │
│ - More Sources  │    │ - WeChat Bot     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              │
                    ┌──────────────────┐
                    │   MySQL DB       │
                    │                  │
                    │ - News Table     │
                    │ - 7 Days Data    │
                    └──────────────────┘
```

### 3.2 技术栈
- **编程语言**: Python 3.8+
- **数据库**: MySQL 8.0+
- **Web框架**: Flask/FastAPI
- **定时任务**: APScheduler
- **RSS解析**: feedparser
- **微信公众号SDK**: wechatpy
- **配置管理**: python-dotenv
- **ORM**: SQLAlchemy

## 4. 数据库设计

### 4.1 数据库表结构

#### 4.1.1 新闻表 (news)
```sql
CREATE TABLE news (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    title VARCHAR(500) NOT NULL COMMENT '新闻标题',
    content TEXT COMMENT '新闻内容摘要',
    url VARCHAR(1000) NOT NULL COMMENT '新闻链接',
    source VARCHAR(100) NOT NULL COMMENT '新闻来源',
    category VARCHAR(50) NOT NULL COMMENT '新闻分类(tech/ai)',
    pub_date DATETIME NOT NULL COMMENT '发布时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_pub_date (pub_date),
    INDEX idx_category (category),
    INDEX idx_created_at (created_at),
    UNIQUE KEY uk_url (url(255)) COMMENT '防止重复新闻'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='新闻数据表';
```

#### 4.1.2 RSS源配置表 (rss_sources)
```sql
CREATE TABLE rss_sources (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    name VARCHAR(100) NOT NULL COMMENT 'RSS源名称',
    url VARCHAR(500) NOT NULL COMMENT 'RSS源URL',
    category VARCHAR(50) NOT NULL COMMENT '分类(tech/ai)',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_url (url)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RSS源配置表';
```

### 4.2 数据生命周期管理
- **数据保留期**: 7天
- **清理策略**: 每次插入新数据时，删除超过7天的旧数据
- **数据去重**: 基于URL进行去重处理

## 5. 详细功能设计

### 5.1 RSS新闻收集模块

#### 5.1.1 核心功能
- 定时任务调度 (每天5:00 AM)
- RSS源数据获取
- 数据解析和清洗
- 数据去重和存储
- 旧数据清理

#### 5.1.2 技术实现
```python
# RSS收集器伪代码
class RSSCollector:
    def __init__(self):
        self.rss_sources = self.load_rss_sources()

    def collect_news(self):
        for source in self.rss_sources:
            news_items = self.parse_rss(source.url)
            for item in news_items:
                self.save_news(item, source.category)
        self.clean_old_news()

    def parse_rss(self, url):
        # 使用feedparser解析RSS
        pass

    def save_news(self, news_item, category):
        # 保存到数据库，去重处理
        pass

    def clean_old_news(self):
        # 删除7天前的数据
        pass
```

### 5.2 微信公众号自动回复模块

#### 5.2.1 核心功能
- 接收微信消息
- 获取当日新闻数据
- 格式化新闻内容
- 发送自动回复

#### 5.2.2 技术实现
```python
# 微信机器人伪代码
class WeChatBot:
    def __init__(self):
        self.app_id = config.WECHAT_APP_ID
        self.app_secret = config.WECHAT_APP_SECRET

    def handle_message(self, message):
        if message.type == 'text':
            news_list = self.get_today_news()
            reply_content = self.format_news(news_list)
            self.reply_user(message.user, reply_content)

    def get_today_news(self):
        # 获取今天的新闻数据
        pass

    def format_news(self, news_list):
        # 格式化新闻内容为微信消息格式
        pass
```

### 5.3 配置管理模块

#### 5.3.1 配置文件结构 (.env)
```
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

### 5.4 RSS可扩展架构

#### 5.4.1 RSS源管理
```python
# RSS源管理器
class RSSSourceManager:
    def add_source(self, name, url, category):
        # 动态添加RSS源
        pass

    def remove_source(self, source_id):
        # 移除RSS源
        pass

    def update_source(self, source_id, **kwargs):
        # 更新RSS源配置
        pass

    def get_active_sources(self):
        # 获取所有启用的RSS源
        pass
```

## 6. 部署和运维

### 6.1 系统要求
- **操作系统**: Linux (Ubuntu 20.04+ 推荐)
- **Python版本**: 3.8+
- **MySQL版本**: 8.0+
- **内存**: 最小512MB，推荐1GB+
- **存储**: 最小5GB，推荐20GB+

### 6.2 部署架构
```
┌─────────────────┐
│   Server        │
│                 │
│ - Python App    │
│ - MySQL         │
│ - Nginx (可选)  │
│ - Supervisor    │
└─────────────────┘
```

### 6.3 监控和日志
- **应用日志**: 记录RSS收集、微信交互等关键操作
- **错误日志**: 记录系统异常和错误信息
- **性能监控**: 监控RSS响应时间、数据库查询性能
- **数据统计**: 统计新闻收集数量、用户交互次数

## 7. 开发计划

### 7.1 开发阶段
1. **阶段一**: 基础架构搭建 (2-3天)
   - 项目初始化
   - 数据库设计和创建
   - 基础配置管理

2. **阶段二**: RSS收集功能 (3-4天)
   - RSS解析器开发
   - 数据收集和存储
   - 定时任务实现

3. **阶段三**: 微信公众号集成 (3-4天)
   - 微信SDK集成
   - 自动回复功能
   - 消息格式化

4. **阶段四**: 系统集成和测试 (2-3天)
   - 模块集成
   - 功能测试
   - 性能优化

5. **阶段五**: 部署上线 (1-2天)
   - 生产环境部署
   - 监控配置
   - 文档完善

### 7.2 风险评估
- **技术风险**: RSS源可用性、微信API限制
- **性能风险**: 大量数据处理、并发访问
- **安全风险**: API密钥泄露、数据安全

## 8. 成功指标

### 8.1 技术指标
- **系统可用性**: ≥ 99%
- **RSS收集成功率**: ≥ 95%
- **微信响应时间**: ≤ 3秒
- **数据准确性**: 100%去重率

### 8.2 业务指标
- **新闻更新及时性**: 每日5点前完成
- **用户互动率**: 回复消息打开率
- **系统稳定性**: 月故障次数 < 3次

## 9. 后续扩展规划

### 9.1 功能扩展
- 支持多种消息格式 (图文、卡片)
- 添加新闻搜索功能
- 支持用户订阅特定分类
- 添加新闻分享功能

### 9.2 技术优化
- 引入缓存机制 (Redis)
- 实现分布式架构
- 添加数据分析功能
- 支持多公众号管理

---

**文档版本**: v1.0
**创建日期**: 2025-11-02
**最后更新**: 2025-11-02
**文档状态**: 待评审