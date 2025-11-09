"""
数据库模型测试
"""
import unittest
from datetime import datetime, timedelta
from test_framework import BaseTestCase
from models import db_manager, News, RSSSource
from logger_config import app_logger


class TestNewsModel(BaseTestCase):
    """新闻模型测试"""

    def test_create_news(self):
        """测试创建新闻"""
        news_data = {
            'title': 'AI技术突破：新算法实现更高效训练',
            'content': '研究人员开发了一种新的深度学习算法...',
            'url': 'https://example.com/ai-breakthrough',
            'source': 'TechNews',
            'category': 'ai',
            'pub_date': datetime.now()
        }

        news = db_manager.create_news(news_data)

        self.assertIsNotNone(news)
        self.assertEqual(news.title, news_data['title'])
        self.assertEqual(news.url, news_data['url'])
        self.assertEqual(news.category, news_data['category'])
        self.assertEqual(news.source, news_data['source'])

    def test_get_news_by_url(self):
        """测试根据URL获取新闻"""
        # 创建测试新闻
        test_news = self.create_test_news(
            url='https://example.com/test-url'
        )

        # 根据URL查询新闻
        found_news = db_manager.get_news_by_url('https://example.com/test-url')

        self.assertIsNotNone(found_news)
        self.assertEqual(found_news.id, test_news.id)
        self.assertEqual(found_news.url, 'https://example.com/test-url')

    def test_get_news_by_url_not_found(self):
        """测试查询不存在的URL"""
        found_news = db_manager.get_news_by_url('https://example.com/nonexistent')
        self.assertIsNone(found_news)

    def test_get_today_news(self):
        """测试获取今日新闻"""
        # 创建今日新闻
        today_news1 = self.create_test_news(
            title='今日新闻1',
            url='https://example.com/today1'
        )
        today_news2 = self.create_test_news(
            title='今日新闻2',
            url='https://example.com/today2',
            category='ai'
        )

        # 创建昨日新闻
        yesterday = datetime.now() - timedelta(days=1)
        old_news = self.create_test_news(
            title='昨日新闻',
            url='https://example.com/yesterday',
            pub_date=yesterday
        )

        # 获取今日新闻
        today_news_list = db_manager.get_today_news()

        # 验证结果
        self.assertEqual(len(today_news_list), 2)
        today_urls = [news.url for news in today_news_list]
        self.assertIn('https://example.com/today1', today_urls)
        self.assertIn('https://example.com/today2', today_urls)
        self.assertNotIn('https://example.com/yesterday', today_urls)

    def test_get_today_news_with_category(self):
        """测试按分类获取今日新闻"""
        # 创建不同分类的新闻
        tech_news = self.create_test_news(
            title='科技新闻',
            url='https://example.com/tech',
            category='tech'
        )
        ai_news = self.create_test_news(
            title='AI新闻',
            url='https://example.com/ai',
            category='ai'
        )

        # 获取科技类新闻
        tech_news_list = db_manager.get_today_news(category='tech')
        self.assertEqual(len(tech_news_list), 1)
        self.assertEqual(tech_news_list[0].category, 'tech')

        # 获取AI类新闻
        ai_news_list = db_manager.get_today_news(category='ai')
        self.assertEqual(len(ai_news_list), 1)
        self.assertEqual(ai_news_list[0].category, 'ai')

    def test_get_today_news_with_limit(self):
        """测试限制数量获取今日新闻"""
        # 创建多条新闻
        for i in range(5):
            self.create_test_news(
                title=f'新闻{i}',
                url=f'https://example.com/news{i}'
            )

        # 限制获取3条
        news_list = db_manager.get_today_news(limit=3)
        self.assertEqual(len(news_list), 3)

    def test_clean_old_news(self):
        """测试清理旧新闻"""
        # 创建不同时间的新闻
        today = datetime.now().date()

        # 创建7天前的新闻（应该被保留）
        seven_days_ago = today - timedelta(days=7)
        old_news_1 = self.create_test_news(
            title='7天前新闻',
            url='https://example.com/old1',
            pub_date=seven_days_ago
        )

        # 创建8天前的新闻（应该被删除）
        eight_days_ago = today - timedelta(days=8)
        old_news_2 = self.create_test_news(
            title='8天前新闻',
            url='https://example.com/old2',
            pub_date=eight_days_ago
        )

        # 执行清理（保留7天）
        deleted_count = db_manager.clean_old_news(7)

        # 验证结果
        self.assertEqual(deleted_count, 1)

        remaining_news = db_manager.get_news_by_url('https://example.com/old1')
        deleted_news = db_manager.get_news_by_url('https://example.com/old2')

        self.assertIsNotNone(remaining_news)
        self.assertIsNone(deleted_news)

    def test_get_news_count(self):
        """测试获取新闻总数"""
        # 初始数量
        initial_count = db_manager.get_news_count()
        self.assertEqual(initial_count, 0)

        # 添加新闻
        self.create_test_news(url='https://example.com/news1')
        self.create_test_news(url='https://example.com/news2')

        # 验证数量
        final_count = db_manager.get_news_count()
        self.assertEqual(final_count, 2)


class TestRSSSourceModel(BaseTestCase):
    """RSS源模型测试"""

    def test_create_rss_source(self):
        """测试创建RSS源"""
        rss_data = {
            'name': 'TechCrunch',
            'url': 'https://techcrunch.com/feed/',
            'category': 'tech',
            'is_active': True
        }

        # 手动创建RSS源（用于测试）
        rss_source = RSSSource(**rss_data)
        self.session.add(rss_source)
        self.session.commit()

        # 验证结果
        self.assertEqual(rss_source.name, rss_data['name'])
        self.assertEqual(rss_source.url, rss_data['url'])
        self.assertEqual(rss_source.category, rss_data['category'])
        self.assertTrue(rss_source.is_active)

    def test_get_active_rss_sources(self):
        """测试获取启用的RSS源"""
        # 创建启用的RSS源
        active_source = self.create_test_rss_source(
            name='活跃RSS源',
            url='https://example.com/active',
            is_active=True
        )

        # 创建禁用的RSS源
        inactive_source = self.create_test_rss_source(
            name='禁用RSS源',
            url='https://example.com/inactive',
            is_active=False
        )

        # 获取启用的RSS源
        active_sources = db_manager.get_active_rss_sources()

        # 验证结果
        self.assertEqual(len(active_sources), 1)
        self.assertEqual(active_sources[0].name, '活跃RSS源')
        self.assertTrue(active_sources[0].is_active)


class TestNewsToDict(BaseTestCase):
    """测试模型转换为字典功能"""

    def test_news_to_dict(self):
        """测试新闻模型转字典"""
        test_news = self.create_test_news()

        news_dict = test_news.to_dict()

        self.assertIsInstance(news_dict, dict)
        self.assertEqual(news_dict['title'], test_news.title)
        self.assertEqual(news_dict['url'], test_news.url)
        self.assertEqual(news_dict['category'], test_news.category)
        self.assertEqual(news_dict['source'], test_news.source)
        self.assertIn('pub_date', news_dict)
        self.assertIn('created_at', news_dict)

    def test_rss_source_to_dict(self):
        """测试RSS源模型转字典"""
        rss_source = self.create_test_rss_source()

        source_dict = rss_source.to_dict()

        self.assertIsInstance(source_dict, dict)
        self.assertEqual(source_dict['name'], rss_source.name)
        self.assertEqual(source_dict['url'], rss_source.url)
        self.assertEqual(source_dict['category'], rss_source.category)
        self.assertTrue(source_dict['is_active'])
        self.assertIn('created_at', source_dict)
        self.assertIn('updated_at', source_dict)


if __name__ == '__main__':
    unittest.main()