"""
RSS新闻收集器模块
"""
import feedparser
import requests
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import re
import time
from bs4 import BeautifulSoup
from models import db_manager, News
from logger_config import app_logger
from config import Config


class RSSCollector:
    """RSS新闻收集器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def collect_all_news(self):
        """收集所有RSS源的新闻"""
        app_logger.info("开始收集RSS新闻...")

        # 获取所有启用的RSS源
        sources = db_manager.get_active_rss_sources()
        if not sources:
            app_logger.warning("没有找到启用的RSS源")
            return 0

        total_collected = 0
        for source in sources:
            try:
                collected = self.collect_from_source(source)
                total_collected += collected
                app_logger.info(f"从 {source.name} 收集了 {collected} 条新闻")

                # 添加延迟避免过于频繁的请求
                time.sleep(1)

            except Exception as e:
                app_logger.error(f"从 {source.name} 收集新闻失败: {e}")
                continue

        # 清理旧数据
        self._clean_old_news()

        app_logger.info(f"RSS新闻收集完成，共收集 {total_collected} 条新闻")
        return total_collected

    def collect_from_source(self, source):
        """从单个RSS源收集新闻"""
        try:
            # 获取RSS内容
            feed = self._fetch_rss_feed(source.url)
            if not feed:
                return 0

            collected_count = 0
            for entry in feed.entries:
                try:
                    if self._process_news_entry(entry, source):
                        collected_count += 1
                except Exception as e:
                    app_logger.error(f"处理新闻条目失败: {e}")
                    continue

            return collected_count

        except Exception as e:
            app_logger.error(f"从RSS源 {source.name} 收集新闻失败: {e}")
            return 0

    def _fetch_rss_feed(self, url):
        """获取RSS feed"""
        try:
            app_logger.debug(f"正在获取RSS feed: {url}")

            # 使用requests获取内容
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # 使用feedparser解析
            feed = feedparser.parse(response.content)

            if feed.bozo and feed.bozo_exception:
                app_logger.warning(f"RSS feed可能有格式问题: {feed.bozo_exception}")

            return feed

        except requests.RequestException as e:
            app_logger.error(f"获取RSS feed失败: {e}")
            return None
        except Exception as e:
            app_logger.error(f"解析RSS feed失败: {e}")
            return None

    def _process_news_entry(self, entry, source):
        """处理单个新闻条目"""
        try:
            # 提取新闻信息
            title = self._extract_title(entry)
            url = self._extract_url(entry)
            content = self._extract_content(entry)
            pub_date = self._extract_pub_date(entry)

            if not all([title, url]):
                app_logger.warning(f"新闻条目缺少必要信息: title={title}, url={url}")
                return False

            # 检查是否已存在
            existing_news = db_manager.get_news_by_url(url)
            if existing_news:
                app_logger.debug(f"新闻已存在: {title}")
                return False

            # 创建新闻记录
            news_data = {
                'title': title,
                'content': content,
                'url': url,
                'source': source.name,
                'category': source.category,
                'pub_date': pub_date
            }

            news = db_manager.create_news(news_data)
            if news:
                app_logger.debug(f"保存新闻成功: {title}")
                return True
            else:
                app_logger.error(f"保存新闻失败: {title}")
                return False

        except Exception as e:
            app_logger.error(f"处理新闻条目失败: {e}")
            return False

    def _extract_title(self, entry):
        """提取新闻标题"""
        title = getattr(entry, 'title', '')
        if title:
            # 清理标题
            title = title.strip()
            title = re.sub(r'\s+', ' ', title)  # 替换多个空格为单个空格
            title = title[:500]  # 限制长度
        return title

    def _extract_url(self, entry):
        """提取新闻链接"""
        url = getattr(entry, 'link', '')
        if url:
            # 确保URL格式正确
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
        return url

    def _extract_content(self, entry):
        """提取新闻内容"""
        content = ''

        # 尝试多个字段获取内容
        content_fields = ['description', 'summary', 'content']

        for field in content_fields:
            if hasattr(entry, field):
                field_value = getattr(entry, field)
                if field_value:
                    if isinstance(field_value, list) and field_value:
                        content = field_value[0].value if hasattr(field_value[0], 'value') else str(field_value[0])
                    else:
                        content = str(field_value)
                    break

        # 如果内容是HTML，清理标签
        if content:
            content = self._clean_html_content(content)

        # 限制内容长度
        if len(content) > 2000:
            content = content[:2000] + '...'

        return content

    def _clean_html_content(self, html_content):
        """清理HTML内容"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()

            # 获取文本内容
            text = soup.get_text()

            # 清理空白字符
            text = re.sub(r'\s+', ' ', text).strip()

            return text

        except Exception as e:
            app_logger.error(f"清理HTML内容失败: {e}")
            return html_content

    def _extract_pub_date(self, entry):
        """提取发布时间"""
        # 尝试多个时间字段
        date_fields = ['published_parsed', 'updated_parsed']

        for field in date_fields:
            if hasattr(entry, field):
                time_struct = getattr(entry, field)
                if time_struct:
                    try:
                        # 转换为datetime对象
                        pub_date = datetime(*time_struct[:6])
                        # 设置时区为UTC
                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                        return pub_date
                    except (ValueError, TypeError) as e:
                        app_logger.warning(f"转换发布时间失败: {e}")
                        continue

        # 如果没有找到时间字段，使用当前时间
        return datetime.now(timezone.utc)

    def _clean_old_news(self):
        """清理旧新闻数据"""
        try:
            deleted_count = db_manager.clean_old_news(Config.DATA_RETENTION_DAYS)
            if deleted_count > 0:
                app_logger.info(f"已清理 {deleted_count} 条超过 {Config.DATA_RETENTION_DAYS} 天的新闻数据")
        except Exception as e:
            app_logger.error(f"清理旧新闻数据失败: {e}")


# RSS收集器实例
rss_collector = RSSCollector()