"""
RSS收集器测试
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from test_framework import BaseTestCase
from rss_collector import RSSCollector
from models import db_manager, RSSSource
from logger_config import app_logger


class TestRSSCollector(BaseTestCase):
    """RSS收集器测试"""

    def setUp(self):
        """测试初始化"""
        super().setUp()
        self.collector = RSSCollector()

    def test_init_collector(self):
        """测试RSS收集器初始化"""
        collector = RSSCollector()
        self.assertIsNotNone(collector.session)
        self.assertIn('User-Agent', collector.session.headers)

    def test_extract_title(self):
        """测试标题提取"""
        # 模拟RSS条目
        entry = Mock()
        entry.title = "  AI技术突破  "

        title = self.collector._extract_title(entry)

        self.assertEqual(title, "AI技术突破")

    def test_extract_title_with_multiple_spaces(self):
        """测试包含多个空格的标题提取"""
        entry = Mock()
        entry.title = "   AI    技术    突破   "

        title = self.collector._extract_title(entry)

        self.assertEqual(title, "AI 技术 突破")

    def test_extract_title_long(self):
        """测试超长标题截取"""
        entry = Mock()
        entry.title = "A" * 600  # 超过500字符限制

        title = self.collector._extract_title(entry)

        self.assertEqual(len(title), 500)
        self.assertTrue(title.endswith("..."))

    def test_extract_url(self):
        """测试URL提取"""
        entry = Mock()
        entry.link = "https://example.com/news"

        url = self.collector._extract_url(entry)

        self.assertEqual(url, "https://example.com/news")

    def test_extract_url_without_protocol(self):
        """测试没有协议的URL提取"""
        entry = Mock()
        entry.link = "example.com/news"

        url = self.collector._extract_url(entry)

        self.assertEqual(url, "https://example.com/news")

    def test_extract_content_from_description(self):
        """测试从description提取内容"""
        entry = Mock()
        entry.description = "这是一条新闻内容"

        content = self.collector._extract_content(entry)

        self.assertEqual(content, "这是一条新闻内容")

    def test_extract_content_from_summary(self):
        """测试从summary提取内容"""
        entry = Mock()
        entry.description = None
        entry.summary = "这是一条新闻摘要"

        content = self.collector._extract_content(entry)

        self.assertEqual(content, "这是一条新闻摘要")

    def test_extract_content_from_list(self):
        """测试从列表中提取内容"""
        entry = Mock()
        entry.description = None
        entry.summary = None
        entry.content = [Mock(value="列表中的内容")]

        content = self.collector._extract_content(entry)

        self.assertEqual(content, "列表中的内容")

    def test_extract_content_long(self):
        """测试超长内容截取"""
        long_content = "A" * 3000  # 超过2000字符限制
        entry = Mock()
        entry.description = long_content

        content = self.collector._extract_content(entry)

        self.assertEqual(len(content), 2003)  # 2000 + "..."
        self.assertTrue(content.endswith("..."))

    def test_clean_html_content(self):
        """测试HTML内容清理"""
        html_content = """
        <html>
            <head>
                <script>alert('test');</script>
                <style>body {color: red;}</style>
            </head>
            <body>
                <h1>新闻标题</h1>
                <p>新闻内容</p>
                <div>更多内容</div>
            </body>
        </html>
        """

        cleaned_content = self.collector._clean_html_content(html_content)

        # 验证脚本和样式被移除
        self.assertNotIn("alert", cleaned_content)
        self.assertNotIn("color: red", cleaned_content)

        # 验证文本内容被保留
        self.assertIn("新闻标题", cleaned_content)
        self.assertIn("新闻内容", cleaned_content)
        self.assertIn("更多内容", cleaned_content)

    def test_extract_pub_date_from_published(self):
        """测试从published_parsed提取发布时间"""
        import time
        time_struct = time.struct_time((2024, 1, 1, 10, 0, 0, 0, 1, 0))
        entry = Mock()
        entry.published_parsed = time_struct

        pub_date = self.collector._extract_pub_date(entry)

        self.assertEqual(pub_date.year, 2024)
        self.assertEqual(pub_date.month, 1)
        self.assertEqual(pub_date.day, 1)
        self.assertEqual(pub_date.hour, 10)

    def test_extract_pub_date_fallback(self):
        """测试没有发布时间时使用当前时间"""
        entry = Mock()
        del entry.published_parsed
        del entry.updated_parsed

        pub_date = self.collector._extract_pub_date(entry)

        self.assertIsNotNone(pub_date)
        self.assertIsInstance(pub_date, datetime)

    @patch('rss_collector.feedparser.parse')
    def test_fetch_rss_feed_success(self, mock_parse):
        """测试成功获取RSS feed"""
        # 模拟feedparser响应
        mock_feed = Mock()
        mock_feed.entries = []
        mock_feed.bozo = False
        mock_parse.return_value = mock_feed

        # 模拟requests响应
        mock_response = Mock()
        mock_response.content = b"mock rss content"
        mock_response.raise_for_status.return_value = None

        with patch.object(self.collector.session, 'get', return_value=mock_response):
            feed = self.collector._fetch_rss_feed("https://example.com/feed")

        self.assertIsNotNone(feed)
        mock_parse.assert_called_once_with(b"mock rss content")

    @patch('rss_collector.feedparser.parse')
    def test_fetch_rss_feed_request_error(self, mock_parse):
        """测试RSS获取请求错误"""
        import requests

        with patch.object(self.collector.session, 'get', side_effect=requests.RequestException("Network error")):
            feed = self.collector._fetch_rss_feed("https://example.com/feed")

        self.assertIsNone(feed)

    def test_process_news_entry_success(self):
        """测试成功处理新闻条目"""
        # 创建测试RSS源
        rss_source = self.create_test_rss_source()

        # 模拟新闻条目
        entry = Mock()
        entry.title = "测试新闻"
        entry.link = "https://example.com/test-news"
        entry.description = "测试内容"
        entry.published_parsed = (2024, 1, 1, 10, 0, 0, 0, 1, 0)

        result = self.collector._process_news_entry(entry, rss_source)

        self.assertTrue(result)

        # 验证新闻已保存
        saved_news = db_manager.get_news_by_url("https://example.com/test-news")
        self.assertIsNotNone(saved_news)
        self.assertEqual(saved_news.title, "测试新闻")

    def test_process_news_entry_duplicate(self):
        """测试处理重复新闻条目"""
        # 创建测试RSS源
        rss_source = self.create_test_rss_source()

        # 先创建一条新闻
        existing_news = self.create_test_news(url="https://example.com/duplicate-news")

        # 模拟相同的新闻条目
        entry = Mock()
        entry.title = "重复新闻"
        entry.link = "https://example.com/duplicate-news"
        entry.description = "重复内容"

        result = self.collector._process_news_entry(entry, rss_source)

        self.assertFalse(result)  # 应该返回False，因为新闻已存在

    def test_process_news_entry_missing_required_fields(self):
        """测试缺少必要字段的新闻条目"""
        rss_source = self.create_test_rss_source()

        # 缺少URL的条目
        entry = Mock()
        entry.title = "缺少URL的新闻"
        del entry.link
        entry.description = "内容"

        result = self.collector._process_news_entry(entry, rss_source)

        self.assertFalse(result)

    @patch.object(RSSCollector, '_fetch_rss_feed')
    @patch.object(RSSCollector, '_process_news_entry')
    def test_collect_from_source_success(self, mock_process, mock_fetch):
        """测试从RSS源收集新闻成功"""
        # 创建测试RSS源
        rss_source = self.create_test_rss_source()

        # 模拟RSS feed
        mock_feed = Mock()
        mock_feed.entries = [Mock(), Mock()]  # 两个新闻条目
        mock_fetch.return_value = mock_feed

        # 模拟处理结果（都成功）
        mock_process.side_effect = [True, True]

        result = self.collector.collect_from_source(rss_source)

        self.assertEqual(result, 2)  # 收集了2条新闻

    @patch.object(RSSCollector, '_fetch_rss_feed')
    def test_collect_from_source_fetch_error(self, mock_fetch):
        """测试RSS源获取失败"""
        rss_source = self.create_test_rss_source()
        mock_fetch.return_value = None

        result = self.collector.collect_from_source(rss_source)

        self.assertEqual(result, 0)

    def test_clean_old_news(self):
        """测试清理旧新闻"""
        # 创建测试新闻（7天前）
        from datetime import timedelta
        old_date = datetime.now() - timedelta(days=8)
        old_news = self.create_test_news(
            title="旧新闻",
            url="https://example.com/old-news",
            pub_date=old_date
        )

        # 执行清理
        with patch.object(db_manager, 'clean_old_news') as mock_clean:
            self.collector._clean_old_news()
            mock_clean.assert_called_once_with(7)


if __name__ == '__main__':
    unittest.main()