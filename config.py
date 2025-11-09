"""
配置管理模块
"""
import os
from decouple import config
from datetime import time


class Config:
    """基础配置类"""

    # Flask配置
    SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')
    DEBUG = config('FLASK_DEBUG', default=False, cast=bool)

    # 数据库配置
    DB_HOST = config('DB_HOST', default='localhost')
    DB_PORT = config('DB_PORT', default=3306, cast=int)
    DB_USER = config('DB_USER', default='root')
    DB_PASSWORD = config('DB_PASSWORD', default='')
    DB_NAME = config('DB_NAME', default='news_bot')

    # SQLAlchemy配置
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG

    # 微信公众号配置
    WECHAT_APP_ID = config('WECHAT_APP_ID', default='')
    WECHAT_APP_SECRET = config('WECHAT_APP_SECRET', default='')
    WECHAT_TOKEN = config('WECHAT_TOKEN', default='')

    # RSS收集配置
    RSS_COLLECT_TIME = config('RSS_COLLECT_TIME', default='05:00')
    DATA_RETENTION_DAYS = config('DATA_RETENTION_DAYS', default=7, cast=int)
    MAX_NEWS_PER_REPLY = config('MAX_NEWS_PER_REPLY', default=10, cast=int)

    # 日志配置
    LOG_LEVEL = config('LOG_LEVEL', default='INFO')
    LOG_FILE = config('LOG_FILE', default='logs/app.log')

    # 默认RSS源
    DEFAULT_RSS_SOURCES = [
        {
            'name': 'TechCrunch',
            'url': 'https://techcrunch.com/feed/',
            'category': 'tech'
        },
        {
            'name': 'AI News',
            'url': 'https://artificialintelligence-news.com/feed/',
            'category': 'ai'
        },
        {
            'name': 'VentureBeat',
            'url': 'https://venturebeat.com/feed/',
            'category': 'tech'
        },
        {
            'name': 'MIT Technology Review',
            'url': 'https://www.technologyreview.com/feed/',
            'category': 'tech'
        }
    ]

    @staticmethod
    def get_rss_collect_time():
        """获取RSS收集时间对象"""
        hour, minute = map(int, Config.RSS_COLLECT_TIME.split(':'))
        return time(hour, minute)

    @staticmethod
    def validate_config():
        """验证必要的配置项"""
        required_configs = [
            'WECHAT_APP_ID',
            'WECHAT_APP_SECRET',
            'WECHAT_TOKEN',
            'DB_PASSWORD'
        ]

        missing_configs = []
        for config_name in required_configs:
            if not getattr(Config, config_name):
                missing_configs.append(config_name)

        if missing_configs:
            raise ValueError(f"缺少必要的配置项: {', '.join(missing_configs)}")


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# 配置字典
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}