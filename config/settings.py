"""
应用配置设置
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""

    # 基础Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # 数据库配置
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
    DB_NAME = os.environ.get('DB_NAME', 'rss_news')

    # 数据库URI
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }

    # 微信公众号配置
    WECHAT_APP_ID = os.environ.get('WECHAT_APP_ID')
    WECHAT_APP_SECRET = os.environ.get('WECHAT_APP_SECRET')
    WECHAT_TOKEN = os.environ.get('WECHAT_TOKEN')
    WECHAT_ENCODING_AES_KEY = os.environ.get('WECHAT_ENCODING_AES_KEY')

    # RSS收集配置
    RSS_COLLECT_HOUR = int(os.environ.get('RSS_COLLECT_HOUR', 5))
    NEWS_RETENTION_DAYS = int(os.environ.get('NEWS_RETENTION_DAYS', 7))

    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))

    # RSS源配置
    DEFAULT_RSS_SOURCES = [
        {
            'name': '36氪',
            'url': 'https://36kr.com/feed',
            'category': 'tech',
            'description': '36氪科技媒体'
        },
        {
            'name': '虎嗅网',
            'url': 'https://www.huxiu.com/rss/0.xml',
            'category': 'tech',
            'description': '虎嗅网科技资讯'
        },
        {
            'name': '机器之心',
            'url': 'https://www.jiqizhixin.com/rss',
            'category': 'ai',
            'description': '机器之心AI媒体'
        },
        {
            'name': '量子位',
            'url': 'https://www.qbitai.com/feed',
            'category': 'ai',
            'description': '量子位AI资讯'
        }
    ]

    # 分页配置
    NEWS_PER_PAGE = 20

    # 缓存配置 (可选)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False

    # 开发环境使用更详细的日志
    LOG_LEVEL = 'DEBUG'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True

    # 测试数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # 禁用CSRF保护
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False

    # 生产环境安全配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}