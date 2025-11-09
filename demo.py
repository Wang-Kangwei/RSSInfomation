#!/usr/bin/env python3
"""
微信公众号RSS新闻机器人演示脚本
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db_manager
from rss_collector import rss_collector
from app import app
from datetime import datetime


def demo_database_connection():
    """演示数据库连接"""
    print("=" * 50)
    print("🔗 测试数据库连接...")
    print("=" * 50)

    try:
        db_manager.init_db()
        print("✅ 数据库连接成功")

        # 获取当前新闻数量
        news_count = db_manager.get_news_count()
        print(f"📊 当前数据库中共有 {news_count} 条新闻")

        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def demo_rss_collection():
    """演示RSS新闻收集"""
    print("\n" + "=" * 50)
    print("📡 演示RSS新闻收集...")
    print("=" * 50)

    try:
        print("🔄 开始收集RSS新闻...")
        collected_count = rss_collector.collect_all_news()
        print(f"✅ RSS收集完成，共收集 {collected_count} 条新闻")

        return collected_count
    except Exception as e:
        print(f"❌ RSS收集失败: {e}")
        return 0


def demo_data_retrieval():
    """演示数据获取"""
    print("\n" + "=" * 50)
    print("📋 演示数据获取...")
    print("=" * 50)

    try:
        # 获取今日新闻
        today_news = db_manager.get_today_news(limit=5)
        print(f"📅 今日新闻数量: {len(today_news)}")

        if today_news:
            print("\n📰 今日新闻列表:")
            for i, news in enumerate(today_news, 1):
                print(f"{i}. 📰 {news.title}")
                print(f"   📤 来源: {news.source}")
                print(f"   🏷️  分类: {news.category}")
                print(f"   🔗 链接: {news.url[:60]}...")
                print(f"   📝 内容: {news.content[:80]}...")
                print()
        else:
            print("📭 今日暂无新闻")

        # 按分类获取新闻
        tech_news = db_manager.get_today_news(category='tech', limit=3)
        ai_news = db_manager.get_today_news(category='ai', limit=3)

        print(f"🔬 科技新闻: {len(tech_news)} 条")
        print(f"🤖 AI新闻: {len(ai_news)} 条")

        return today_news

    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
        return []


def demo_flask_api():
    """演示Flask API"""
    print("\n" + "=" * 50)
    print("🌐 演示Flask API接口...")
    print("=" * 50)

    try:
        with app.test_client() as client:
            # 健康检查
            print("🏥 测试健康检查接口...")
            response = client.get('/health')
            if response.status_code == 200:
                health_data = response.get_json()
                print(f"✅ 健康检查通过")
                print(f"   状态: {health_data['status']}")
                print(f"   数据库: {health_data['database']}")
                print(f"   新闻数量: {health_data['news_count']}")
            else:
                print(f"❌ 健康检查失败: {response.status_code}")

            # 新闻API
            print("\n📰 测试新闻API接口...")
            response = client.get('/news?limit=3')
            if response.status_code == 200:
                news_data = response.get_json()
                print(f"✅ 新闻API正常")
                print(f"   新闻数量: {news_data['count']}")

                if news_data['news']:
                    print("   最新新闻:")
                    for i, news in enumerate(news_data['news'], 1):
                        print(f"   {i}. {news['title'][:50]}...")
            else:
                print(f"❌ 新闻API失败: {response.status_code}")

            # 手动收集新闻
            print("\n🔄 测试手动收集新闻接口...")
            response = client.post('/collect_news')
            if response.status_code == 200:
                collect_data = response.get_json()
                print(f"✅ 手动收集成功")
                print(f"   收集数量: {collect_data.get('collected_count', 0)}")
            else:
                print(f"❌ 手动收集失败: {response.status_code}")

    except Exception as e:
        print(f"❌ Flask API测试失败: {e}")


def demo_rss_sources():
    """演示RSS源管理"""
    print("\n" + "=" * 50)
    print("📡 演示RSS源管理...")
    print("=" * 50)

    try:
        rss_sources = db_manager.get_active_rss_sources()
        print(f"📊 当前启用的RSS源数量: {len(rss_sources)}")

        if rss_sources:
            print("\n📋 RSS源列表:")
            for i, source in enumerate(rss_sources, 1):
                print(f"{i}. 📡 {source.name}")
                print(f"   🔗 {source.url}")
                print(f"   🏷️  分类: {source.category}")
                print(f"   ✅ 状态: {'启用' if source.is_active else '禁用'}")
                print()

        return rss_sources

    except Exception as e:
        print(f"❌ RSS源获取失败: {e}")
        return []


def main():
    """主演示函数"""
    print("🎉 微信公众号RSS新闻机器人演示")
    print("📅 演示时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print()

    # 演示各个功能模块
    if demo_database_connection():
        demo_rss_sources()
        demo_rss_collection()
        demo_data_retrieval()
        demo_flask_api()

    print("\n" + "=" * 50)
    print("🎉 演示完成！")
    print("=" * 50)

    print("\n📋 功能总结:")
    print("✅ 数据库连接和初始化")
    print("✅ RSS新闻自动收集")
    print("✅ 数据存储到MySQL")
    print("✅ 新闻数据查询和检索")
    print("✅ Flask API接口")
    print("✅ RSS源管理")

    print("\n🚀 系统已就绪，可以开始使用！")


if __name__ == "__main__":
    main()