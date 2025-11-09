"""
数据库初始化脚本
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from models import db_manager
from logger_config import app_logger


def init_database():
    """初始化数据库"""
    try:
        app_logger.info("开始初始化数据库...")

        # 验证配置
        Config.validate_config()

        # 初始化数据库
        db_manager.init_db()

        # 测试数据库连接
        session = db_manager.get_session()
        news_count = db_manager.get_news_count()
        sources_count = len(db_manager.get_active_rss_sources())

        app_logger.info(f"数据库初始化完成！")
        app_logger.info(f"当前新闻数量: {news_count}")
        app_logger.info(f"RSS源数量: {sources_count}")

        return True

    except Exception as e:
        app_logger.error(f"数据库初始化失败: {e}")
        return False
    finally:
        if 'session' in locals():
            session.close()


if __name__ == "__main__":
    success = init_database()
    if success:
        print("✅ 数据库初始化成功！")
        sys.exit(0)
    else:
        print("❌ 数据库初始化失败！")
        sys.exit(1)