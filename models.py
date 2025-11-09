"""
数据库模型模块
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from config import Config
from logger_config import app_logger

Base = declarative_base()


class News(Base):
    """新闻模型"""
    __tablename__ = 'news'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    title = Column(String(500), nullable=False, comment='新闻标题')
    content = Column(Text, comment='新闻内容摘要')
    url = Column(String(1000), nullable=False, comment='新闻链接')
    source = Column(String(100), nullable=False, comment='新闻来源')
    category = Column(String(50), nullable=False, comment='新闻分类(tech/ai)')
    pub_date = Column(DateTime, nullable=False, comment='发布时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 索引
    __table_args__ = (
        Index('idx_pub_date', 'pub_date'),
        Index('idx_category', 'category'),
        Index('idx_created_at', 'created_at'),
        # 不为URL创建索引，避免长度问题
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_comment': '新闻数据表'}
    )

    def __repr__(self):
        return f'<News {self.title}>'

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'source': self.source,
            'category': self.category,
            'pub_date': self.pub_date.isoformat() if self.pub_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class RSSSource(Base):
    """RSS源配置模型"""
    __tablename__ = 'rss_sources'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = Column(String(100), nullable=False, comment='RSS源名称')
    url = Column(String(500), nullable=False, comment='RSS源URL')
    category = Column(String(50), nullable=False, comment='分类(tech/ai)')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def __repr__(self):
        return f'<RSSSource {self.name}>'

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.session_factory = None

    def init_db(self):
        """初始化数据库连接"""
        try:
            # 创建数据库引擎
            self.engine = create_engine(
                Config.SQLALCHEMY_DATABASE_URI,
                pool_size=10,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=Config.SQLALCHEMY_ECHO
            )

            # 创建会话工厂
            self.SessionLocal = scoped_session(sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            ))
            self.session_factory = self.SessionLocal

            # 创建表
            Base.metadata.create_all(bind=self.engine)
            app_logger.info("数据库初始化成功")

            # 初始化默认RSS源
            self._init_default_rss_sources()

        except SQLAlchemyError as e:
            app_logger.error(f"数据库初始化失败: {e}")
            raise

    def _init_default_rss_sources(self):
        """初始化默认RSS源"""
        try:
            session = self.get_session()
            # 检查是否已有RSS源
            existing_sources = session.query(RSSSource).count()
            if existing_sources == 0:
                # 添加默认RSS源
                for source_data in Config.DEFAULT_RSS_SOURCES:
                    rss_source = RSSSource(**source_data)
                    session.add(rss_source)
                session.commit()
                app_logger.info(f"已添加 {len(Config.DEFAULT_RSS_SOURCES)} 个默认RSS源")
        except SQLAlchemyError as e:
            session.rollback()
            app_logger.error(f"初始化RSS源失败: {e}")
            raise
        finally:
            session.close()

    def get_session(self):
        """获取数据库会话"""
        if not self.session_factory:
            raise RuntimeError("数据库未初始化，请先调用 init_db()")
        return self.session_factory()

    def close_session(self):
        """关闭数据库会话"""
        if self.SessionLocal:
            self.SessionLocal.remove()

    def create_news(self, news_data):
        """创建新闻记录"""
        try:
            session = self.get_session()
            news = News(**news_data)
            session.add(news)
            session.commit()
            session.refresh(news)
            app_logger.debug(f"创建新闻成功: {news.title}")
            return news
        except SQLAlchemyError as e:
            session.rollback()
            app_logger.error(f"创建新闻失败: {e}")
            return None
        finally:
            session.close()

    def get_news_by_url(self, url):
        """根据URL获取新闻"""
        try:
            session = self.get_session()
            news = session.query(News).filter(News.url == url).first()
            return news
        except SQLAlchemyError as e:
            app_logger.error(f"查询新闻失败: {e}")
            return None
        finally:
            session.close()

    def get_today_news(self, category=None, limit=None):
        """获取今日新闻"""
        try:
            session = self.get_session()
            today = datetime.now().date()

            query = session.query(News).filter(
                News.created_at >= today
            ).order_by(News.created_at.desc())

            if category:
                query = query.filter(News.category == category)

            if limit:
                query = query.limit(limit)

            return query.all()
        except SQLAlchemyError as e:
            app_logger.error(f"获取今日新闻失败: {e}")
            return []
        finally:
            session.close()

    def get_active_rss_sources(self):
        """获取所有启用的RSS源"""
        try:
            session = self.get_session()
            sources = session.query(RSSSource).filter(
                RSSSource.is_active == True
            ).all()
            return sources
        except SQLAlchemyError as e:
            app_logger.error(f"获取RSS源失败: {e}")
            return []
        finally:
            session.close()

    def clean_old_news(self, days=7):
        """清理旧新闻数据"""
        try:
            session = self.get_session()
            cutoff_date = datetime.now() - timedelta(days=days)

            deleted_count = session.query(News).filter(
                News.created_at < cutoff_date
            ).delete()

            session.commit()
            app_logger.info(f"已清理 {deleted_count} 条 {days} 天前的新闻数据")
            return deleted_count
        except SQLAlchemyError as e:
            session.rollback()
            app_logger.error(f"清理旧新闻失败: {e}")
            return 0
        finally:
            session.close()

    def get_news_count(self):
        """获取新闻总数"""
        try:
            session = self.get_session()
            count = session.query(News).count()
            return count
        except SQLAlchemyError as e:
            app_logger.error(f"获取新闻总数失败: {e}")
            return 0
        finally:
            session.close()


# 全局数据库管理器实例
db_manager = DatabaseManager()