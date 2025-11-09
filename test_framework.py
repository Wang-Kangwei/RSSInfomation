"""
测试框架配置
"""
import unittest
import tempfile
import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import TestingConfig
from models import db_manager, Base, News, RSSSource
from logger_config import app_logger


class BaseTestCase(unittest.TestCase):
    """测试基类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 使用测试配置
        cls.config = TestingConfig()

        # 设置测试数据库
        cls.temp_db = tempfile.NamedTemporaryFile(delete=False)
        cls.temp_db.close()

        # 更新数据库URI为临时SQLite文件
        cls.config.SQLALCHEMY_DATABASE_URI = f'sqlite:///{cls.temp_db.name}'

        # 初始化数据库
        cls._setup_test_database()

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        # 关闭数据库连接
        db_manager.close_session()

        # 删除临时数据库文件
        if os.path.exists(cls.temp_db.name):
            os.unlink(cls.temp_db.name)

    def setUp(self):
        """每个测试方法前的初始化"""
        # 开始一个事务
        self.session = db_manager.get_session()
        self.session.begin_nested()

    def tearDown(self):
        """每个测试方法后的清理"""
        # 回滚事务
        self.session.rollback()
        self.session.close()

    @classmethod
    def _setup_test_database(cls):
        """设置测试数据库"""
        try:
            # 临时设置数据库配置
            import models
            original_config = getattr(models, 'Config', None)
            models.Config = cls.config

            # 初始化数据库
            db_manager.engine = None
            db_manager.SessionLocal = None
            db_manager.session_factory = None
            db_manager.init_db()

            # 恢复原始配置
            if original_config:
                models.Config = original_config

            app_logger.info("测试数据库初始化完成")

        except Exception as e:
            app_logger.error(f"测试数据库初始化失败: {e}")
            raise

    def create_test_news(self, **kwargs):
        """创建测试新闻数据"""
        default_data = {
            'title': '测试新闻标题',
            'content': '这是一条测试新闻内容',
            'url': 'https://example.com/test-news',
            'source': '测试来源',
            'category': 'tech',
            'pub_date': '2024-01-01 10:00:00'
        }

        # 合并默认数据和传入参数
        data = {**default_data, **kwargs}

        news = News(**data)
        self.session.add(news)
        self.session.commit()
        self.session.refresh(news)

        return news

    def create_test_rss_source(self, **kwargs):
        """创建测试RSS源数据"""
        default_data = {
            'name': '测试RSS源',
            'url': 'https://example.com/feed',
            'category': 'tech',
            'is_active': True
        }

        # 合并默认数据和传入参数
        data = {**default_data, **kwargs}

        rss_source = RSSSource(**data)
        self.session.add(rss_source)
        self.session.commit()
        self.session.refresh(rss_source)

        return rss_source