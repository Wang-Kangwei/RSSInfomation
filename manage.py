#!/usr/bin/env python3
"""
RSSInfomation 项目管理脚本
用于数据库初始化、迁移等管理任务
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.app import create_app
from core.database import init_db

app = create_app()

def init_db_command():
    """初始化数据库"""
    with app.app_context():
        init_db()
        print('数据库初始化完成')

def create_tables_command():
    """创建数据库表"""
    with app.app_context():
        from core.database import db
        from models.news import News
        from models.source import RSSSource
        from models.base import SystemConfig

        try:
            # 先删除所有表（如果存在）
            db.drop_all()
            print('已删除现有数据库表')

            # 创建所有表
            db.create_all()
            print('数据库表创建完成')

            # 初始化默认数据
            _init_default_data()
            print('默认数据初始化完成')

        except Exception as e:
            print(f'创建数据库表时出错: {e}')
            raise

def _init_default_data():
    """初始化默认数据"""
    try:
        from models.source import RSSSource
        from models.base import SystemConfig
        import traceback

        # 添加默认RSS源
        default_sources = [
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

        click.echo('开始添加默认RSS源...')
        for source_data in default_sources:
            try:
                existing = RSSSource.query.filter_by(url=source_data['url']).first()
                if not existing:
                    source = RSSSource(**source_data)
                    db.session.add(source)
                    click.echo(f'添加RSS源: {source_data["name"]}')
                else:
                    click.echo(f'RSS源已存在: {source_data["name"]}')
            except Exception as e:
                click.echo(f'添加RSS源失败 {source_data["name"]}: {e}')
                traceback.print_exc()

        # 添加系统配置
        default_configs = [
            {
                'config_key': 'rss_collect_hour',
                'config_value': '5',
                'description': 'RSS收集时间（小时）'
            },
            {
                'config_key': 'news_retention_days',
                'config_value': '7',
                'description': '新闻保留天数'
            },
            {
                'config_key': 'max_news_per_source',
                'config_value': '10',
                'description': '每个RSS源最大新闻数量'
            }
        ]

        click.echo('开始添加系统配置...')
        for config_data in default_configs:
            try:
                existing = SystemConfig.query.filter_by(config_key=config_data['config_key']).first()
                if not existing:
                    config = SystemConfig(**config_data)
                    db.session.add(config)
                    click.echo(f'添加配置: {config_data["config_key"]}')
                else:
                    click.echo(f'配置已存在: {config_data["config_key"]}')
            except Exception as e:
                click.echo(f'添加配置失败 {config_data["config_key"]}: {e}')
                traceback.print_exc()

        db.session.commit()
        click.echo('默认数据初始化完成')

    except Exception as e:
        click.echo(f'初始化默认数据时出错: {e}')
        traceback.print_exc()
        db.session.rollback()
        raise

def test_news_command(count=5):
    """测试新闻展示功能"""
    with app.app_context():
        from services.news_service import NewsService
        from wechat.formatter import WechatTextFormatter

        news_service = NewsService()
        formatter = WechatTextFormatter()

        # 获取今日新闻
        news_items = news_service.get_today_news(limit=count)

        if news_items:
            formatted_content = formatter.format(news_items)
            print(f"今日新闻（前{count}条）：\n")
            print(formatted_content)
        else:
            print("今日暂无新闻")

def collect_rss_command():
    """手动触发RSS收集"""
    with app.app_context():
        from rss.collector import RSSCollector
        from utils.logger import get_logger

        logger = get_logger(__name__)
        print("开始手动收集RSS新闻...")

        try:
            # 从配置中获取每个RSS源最大新闻数量限制
            max_news_per_source = app.config.get('MAX_NEWS_PER_SOURCE', 10)
            print(f"每个RSS源最多收集 {max_news_per_source} 条新闻")

            collector = RSSCollector(max_news_per_source=max_news_per_source)
            result = collector.collect_all_sources()

            print(f"RSS收集完成！")
            print(f"总源数量: {result.get('total_sources', 0)}")
            print(f"成功收集: {result.get('success_count', 0)}")
            print(f"收集失败: {result.get('error_count', 0)}")
            print(f"收集新闻总数: {result.get('total_news', 0)}")
            print(f"耗时: {result.get('duration', 0):.2f}秒")

            if result.get('error_count', 0) > 0:
                print("\n错误详情:")
                for error in result.get('errors', []):
                    print(f"  - {error}")
                print("\n请查看日志了解详细错误信息")

        except Exception as e:
            print(f"RSS收集失败: {e}")
            logger.error(f"手动RSS收集失败: {e}")

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python manage.py <command>")
        print("Commands:")
        print("  init-db        - 初始化数据库")
        print("  create-tables  - 创建数据库表")
        print("  test-news      - 测试新闻展示功能")
        print("  collect-rss    - 手动触发RSS收集")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'init-db':
        init_db_command()
    elif command == 'create-tables':
        create_tables_command()
    elif command == 'test-news':
        count = 5
        if len(sys.argv) > 2 and sys.argv[2] == '--count' and len(sys.argv) > 3:
            count = int(sys.argv[3])
        test_news_command(count)
    elif command == 'collect-rss':
        collect_rss_command()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)