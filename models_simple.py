import logging
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config import Config

Base = declarative_base()

class News(Base):
    __tablename__ = 'news'
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    url = Column(String(1000), nullable=False)
    source = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    pub_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
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
    __tablename__ = 'rss_sources'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    category = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None

    def init_db(self):
        try:
            self.engine = create_engine(
                Config.SQLALCHEMY_DATABASE_URI,
                echo=Config.SQLALCHEMY_ECHO
            )
            self.SessionLocal = scoped_session(sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            ))
            Base.metadata.create_all(bind=self.engine)
            logging.info('数据库初始化成功')
        except Exception as e:
            logging.error(f'数据库初始化失败: {e}')
            raise

    def get_session(self):
        if not self.SessionLocal:
            raise RuntimeError('数据库未初始化')
        return self.SessionLocal()

    def create_news(self, news_data):
        try:
            session = self.get_session()
            news = News(**news_data)
            session.add(news)
            session.commit()
            session.refresh(news)
            return news
        except Exception as e:
            session.rollback()
            return None
        finally:
            session.close()

    def get_news_by_url(self, url):
        try:
            session = self.get_session()
            return session.query(News).filter(News.url == url).first()
        except Exception:
            return None
        finally:
            session.close()

    def get_today_news(self, category=None, limit=None):
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
        except Exception:
            return []
        finally:
            session.close()

    def get_active_rss_sources(self):
        try:
            session = self.get_session()
            return session.query(RSSSource).filter(RSSSource.is_active == True).all()
        except Exception:
            return []
        finally:
            session.close()

    def get_news_count(self):
        try:
            session = self.get_session()
            return session.query(News).count()
        except Exception:
            return 0
        finally:
            session.close()

db_manager = DatabaseManager()