"""
核心数据库模块
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

# 初始化数据库实例
db = SQLAlchemy()

# 创建基础模型类
Base = declarative_base()

def init_db():
    """初始化数据库"""
    # 导入所有模型以确保表被创建
    from models.base import SystemConfig
    from models.news import News
    from models.source import RSSSource

    # 创建所有表
    db.create_all()

    # 初始化默认数据
    _init_default_data()

def _init_default_data():
    """初始化默认数据"""
    from models.source import RSSSource
    from config.settings import Config

    # 检查是否已有RSS源
    existing_sources = RSSSource.query.count()
    if existing_sources == 0:
        # 添加默认RSS源
        for source_config in Config.DEFAULT_RSS_SOURCES:
            source = RSSSource(
                name=source_config['name'],
                url=source_config['url'],
                category=source_config['category'],
                description=source_config['description'],
                is_active=True
            )
            db.session.add(source)

        db.session.commit()
        print(f"已添加 {len(Config.DEFAULT_RSS_SOURCES)} 个默认RSS源")

def get_db_session():
    """获取数据库会话"""
    return db.session