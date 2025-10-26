"""
数据库配置
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import Config

# 创建数据库引擎
engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    **Config.SQLALCHEMY_ENGINE_OPTIONS
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库"""
    # 导入所有模型以确保表被创建
    from models.base import SystemConfig
    from models.news import News
    from models.source import RSSSource

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 初始化默认数据
    _init_default_data()

def _init_default_data():
    """初始化默认数据"""
    from models.source import RSSSource

    session = SessionLocal()
    try:
        # 检查是否已有RSS源
        existing_sources = session.query(RSSSource).count()
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
                session.add(source)

            session.commit()
            print(f"已添加 {len(Config.DEFAULT_RSS_SOURCES)} 个默认RSS源")
    except Exception as e:
        session.rollback()
        print(f"初始化默认数据失败: {e}")
    finally:
        session.close()