"""
RSS解析器模块
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import feedparser
import re
from bs4 import BeautifulSoup
import hashlib
from urllib.parse import urlparse

from core.exceptions import RSSParseError
from utils.logger import get_logger

logger = get_logger(__name__)

class NewsItem:
    """新闻项数据类"""
    def __init__(self):
        self.title: str = ""
        self.content: str = ""
        self.link: str = ""
        self.author: str = ""
        self.category: str = ""
        self.source_name: str = ""
        self.source_url: str = ""
        self.pub_date: Optional[datetime] = None
        self.guid: str = ""
        self.hash_code: str = ""

    def generate_hash_code(self):
        """生成内容哈希值"""
        content = f"{self.title}{self.link}{self.pub_date.isoformat() if self.pub_date else ''}"
        self.hash_code = hashlib.sha256(content.encode('utf-8')).hexdigest()

    def __repr__(self):
        return f"<NewsItem(title='{self.title[:50]}...', source='{self.source_name}')>"

class RSSParser(ABC):
    """RSS解析器抽象基类"""

    @abstractmethod
    def parse(self, rss_content: str, source_name: str, source_url: str, category: str) -> List[NewsItem]:
        """解析RSS内容"""
        pass

    @abstractmethod
    def can_parse(self, rss_content: str) -> bool:
        """检查是否能解析该RSS格式"""
        pass

class StandardRSSParser(RSSParser):
    """标准RSS解析器"""

    def __init__(self):
        self.content_cleaner = ContentCleaner()

    def parse(self, rss_content: str, source_name: str, source_url: str, category: str) -> List[NewsItem]:
        """解析标准RSS格式"""
        try:
            feed = feedparser.parse(rss_content)

            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS解析警告: {feed.bozo_exception}")

            news_items = []
            for entry in feed.entries:
                news_item = self._parse_entry(entry, source_name, source_url, category)
                if news_item:
                    news_items.append(news_item)

            logger.info(f"从 {source_name} 解析出 {len(news_items)} 条新闻")
            return news_items

        except Exception as e:
            logger.error(f"RSS解析失败: {e}")
            raise RSSParseError(f"RSS解析失败: {str(e)}")

    def can_parse(self, rss_content: str) -> bool:
        """检查是否为标准RSS格式"""
        try:
            feed = feedparser.parse(rss_content)
            return hasattr(feed, 'entries') and len(feed.entries) > 0
        except:
            return False

    def _parse_entry(self, entry: Any, source_name: str, source_url: str, category: str) -> Optional[NewsItem]:
        """解析单个RSS条目"""
        try:
            news_item = NewsItem()

            # 标题
            news_item.title = self._get_title(entry)

            # 链接
            news_item.link = self._get_link(entry)

            # 内容
            news_item.content = self._get_content(entry)

            # 作者
            news_item.author = self._get_author(entry)

            # 发布时间
            news_item.pub_date = self._get_pub_date(entry)

            # GUID
            news_item.guid = self._get_guid(entry)

            # 源信息
            news_item.source_name = source_name
            news_item.source_url = source_url
            news_item.category = category

            # 生成哈希值
            news_item.generate_hash_code()

            return news_item

        except Exception as e:
            logger.warning(f"解析RSS条目失败: {e}")
            return None

    def _get_title(self, entry: Any) -> str:
        """获取标题"""
        title = getattr(entry, 'title', '')
        return self.content_cleaner.clean_text(title) if title else '无标题'

    def _get_link(self, entry: Any) -> str:
        """获取链接"""
        link = getattr(entry, 'link', '')
        return link.strip() if link else ''

    def _get_content(self, entry: Any) -> str:
        """获取内容"""
        content = ''

        # 尝试获取详细内容
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value if entry.content else ''
        elif hasattr(entry, 'description'):
            content = entry.description

        return self.content_cleaner.clean_html(content) if content else ''

    def _get_author(self, entry: Any) -> str:
        """获取作者"""
        author = ''

        if hasattr(entry, 'author'):
            author = entry.author
        elif hasattr(entry, 'author_detail') and entry.author_detail:
            author = entry.author_detail.get('name', '')

        return self.content_cleaner.clean_text(author) if author else ''

    def _get_pub_date(self, entry: Any) -> Optional[datetime]:
        """获取发布时间"""
        # 尝试多种时间字段
        time_fields = ['published_parsed', 'updated_parsed']

        for field in time_fields:
            if hasattr(entry, field) and getattr(entry, field):
                time_struct = getattr(entry, field)
                try:
                    return datetime(*time_struct[:6])
                except (ValueError, TypeError):
                    continue

        return None

    def _get_guid(self, entry: Any) -> str:
        """获取GUID"""
        guid = getattr(entry, 'id', '')
        if not guid and hasattr(entry, 'link'):
            guid = entry.link
        return guid.strip() if guid else ''

class AtomRSSParser(RSSParser):
    """Atom格式解析器"""

    def __init__(self):
        self.standard_parser = StandardRSSParser()

    def parse(self, rss_content: str, source_name: str, source_url: str, category: str) -> List[NewsItem]:
        """解析Atom格式"""
        # Atom格式通常也可以用标准解析器处理
        return self.standard_parser.parse(rss_content, source_name, source_url, category)

    def can_parse(self, rss_content: str) -> bool:
        """检查是否为Atom格式"""
        try:
            feed = feedparser.parse(rss_content)
            return getattr(feed, 'version', '').startswith('atom')
        except:
            return False

class ContentCleaner:
    """内容清理器"""

    def clean_text(self, text: str) -> str:
        """清理纯文本"""
        if not text:
            return ''

        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())

        # 移除HTML实体
        text = re.sub(r'&[a-zA-Z0-9#]+;', '', text)

        return text

    def clean_html(self, html: str) -> str:
        """清理HTML内容"""
        if not html:
            return ''

        try:
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html, 'html.parser')

            # 移除脚本和样式标签
            for script in soup(["script", "style"]):
                script.decompose()

            # 获取纯文本
            text = soup.get_text()

            # 清理空白字符
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            # 限制长度
            if len(text) > 1000:
                text = text[:1000] + '...'

            return text

        except Exception as e:
            logger.warning(f"HTML清理失败: {e}")
            return self.clean_text(html)

class RSSParserFactory:
    """RSS解析器工厂"""

    def __init__(self):
        self.parsers = [
            StandardRSSParser(),
            AtomRSSParser()
        ]

    def create_parser(self, rss_content: str) -> RSSParser:
        """根据RSS内容创建合适的解析器"""
        for parser in self.parsers:
            if parser.can_parse(rss_content):
                return parser

        # 默认返回标准解析器
        return StandardRSSParser()

    def get_supported_formats(self) -> List[str]:
        """获取支持的格式列表"""
        return ['RSS 2.0', 'RSS 1.0', 'Atom 1.0', 'Atom 0.3']