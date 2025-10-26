"""
RSS收集器模块
"""

import time
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse
import socket

from core.database import get_db_session
from models.news import News
from models.source import RSSSource
from rss.parser import RSSParserFactory, NewsItem
from core.exceptions import RSSFetchError, RSSParseError, DatabaseError
from utils.logger import get_logger

logger = get_logger(__name__)

class RSSCollector:
    """RSS收集器"""

    def __init__(self, max_news_per_source=10):
        self.parser_factory = RSSParserFactory()
        self.session = requests.Session()
        self.max_news_per_source = max_news_per_source

        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'RSSInfomation/1.0 (RSS Reader Bot)',
            'Accept': 'application/rss+xml, application/xml, text/xml',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })

        # 设置超时时间
        self.timeout = 30

    def collect_from_source(self, source_id: int) -> int:
        """从指定RSS源收集新闻"""
        try:
            session = get_db_session()

            # 获取RSS源信息
            source = session.query(RSSSource).filter(RSSSource.id == source_id).first()
            if not source:
                raise RSSFetchError(f"RSS源不存在: {source_id}")

            if not source.is_active:
                logger.warning(f"RSS源未激活，跳过收集: {source.name}")
                return 0

            logger.info(f"开始收集RSS源: {source.name} ({source.url})")
            start_time = datetime.utcnow()

            try:
                # 获取RSS内容
                rss_content = self._fetch_rss_content(source.url)

                # 解析RSS内容
                news_items = self._parse_rss_content(rss_content, source)

                # 限制每个RSS源的新闻数量
                if len(news_items) > self.max_news_per_source:
                    news_items = news_items[:self.max_news_per_source]
                    logger.info(f"RSS源 {source.name} 新闻数量超过限制，截取前 {self.max_news_per_source} 条")

                # 保存新闻数据
                saved_count = self._save_news_items(news_items)

                # 更新RSS源状态
                self._update_source_status(source, True, saved_count)

                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"RSS收集完成: {source.name}, 收集到{saved_count}条新闻, 耗时{duration:.2f}秒")

                return saved_count

            except Exception as e:
                # 更新RSS源错误状态
                self._update_source_status(source, False, 0, str(e))
                raise

        except Exception as e:
            logger.error(f"RSS收集失败: {source_id}, 错误: {e}")
            raise RSSFetchError(f"RSS收集失败: {str(e)}")

    def collect_all_sources(self) -> Dict[str, Any]:
        """从所有活跃RSS源收集新闻"""
        session = get_db_session()

        try:
            # 获取所有活跃的RSS源
            sources = session.query(RSSSource).filter(RSSSource.is_active == True).all()

            total_news = 0
            success_count = 0
            error_count = 0
            errors = []

            start_time = datetime.utcnow()

            for source in sources:
                try:
                    news_count = self.collect_from_source(source.id)
                    total_news += news_count
                    success_count += 1

                except Exception as e:
                    error_count += 1
                    error_msg = f"收集 {source.name} 失败: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            duration = (datetime.utcnow() - start_time).total_seconds()

            result = {
                'total_sources': len(sources),
                'success_count': success_count,
                'error_count': error_count,
                'total_news': total_news,
                'duration': duration,
                'errors': errors
            }

            logger.info(f"批量收集完成: 成功{success_count}个源, 失败{error_count}个源, "
                       f"共收集{total_news}条新闻, 耗时{duration:.2f}秒")

            return result

        except Exception as e:
            logger.error(f"批量收集失败: {e}")
            raise RSSFetchError(f"批量收集失败: {str(e)}")

    def _fetch_rss_content(self, url: str) -> str:
        """获取RSS内容"""
        try:
            # 验证URL格式
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise RSSFetchError(f"无效的RSS URL: {url}")

            # 发送HTTP请求
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # 检查响应内容类型
            content_type = response.headers.get('content-type', '').lower()
            if not any(ct in content_type for ct in ['xml', 'rss', 'atom']):
                logger.warning(f"RSS响应内容类型异常: {content_type}")

            # 检查响应内容长度
            content = response.text
            if len(content) < 100:  # RSS内容通常不会很短
                raise RSSFetchError(f"RSS内容过短，可能获取失败: {len(content)} 字符")

            return content

        except requests.exceptions.Timeout:
            raise RSSFetchError(f"RSS请求超时: {url}")
        except requests.exceptions.ConnectionError:
            raise RSSFetchError(f"RSS连接失败: {url}")
        except requests.exceptions.HTTPError as e:
            raise RSSFetchError(f"RSS HTTP错误: {url}, 状态码: {e.response.status_code}")
        except Exception as e:
            raise RSSFetchError(f"RSS获取失败: {url}, 错误: {str(e)}")

    def _parse_rss_content(self, rss_content: str, source: RSSSource) -> List[NewsItem]:
        """解析RSS内容"""
        try:
            # 创建合适的解析器
            parser = self.parser_factory.create_parser(rss_content)

            # 解析RSS内容
            news_items = parser.parse(rss_content, source.name, source.url, source.category)

            # 过滤和验证新闻项
            filtered_items = []
            for item in news_items:
                if self._validate_news_item(item):
                    filtered_items.append(item)
                else:
                    logger.debug(f"过滤掉无效新闻项: {item.title}")

            logger.info(f"RSS解析完成: {source.name}, 原始{len(news_items)}条, 有效{len(filtered_items)}条")
            return filtered_items

        except Exception as e:
            logger.error(f"RSS解析失败: {source.name}, 错误: {e}")
            raise RSSParseError(f"RSS解析失败: {str(e)}")

    def _validate_news_item(self, item: NewsItem) -> bool:
        """验证新闻项是否有效"""
        # 检查必填字段
        if not item.title or len(item.title.strip()) < 3:
            return False

        if not item.link:
            return False

        # 检查URL格式
        try:
            parsed_url = urlparse(item.link)
            if not parsed_url.scheme or not parsed_url.netloc:
                return False
        except:
            return False

        # 检查发布时间（如果有的话）
        if item.pub_date and item.pub_date > datetime.utcnow():
            logger.warning(f"新闻发布时间在未来: {item.title}, {item.pub_date}")
            # 可以选择是否过滤掉未来时间的新闻

        return True

    def _save_news_items(self, news_items: List[NewsItem]) -> int:
        """保存新闻项到数据库"""
        if not news_items:
            return 0

        session = get_db_session()
        saved_count = 0

        try:
            for item in news_items:
                # 检查是否已存在（基于哈希值去重）
                existing_news = session.query(News).filter(News.hash_code == item.hash_code).first()
                if existing_news:
                    logger.debug(f"新闻已存在，跳过: {item.title}")
                    continue

                # 创建新闻记录
                news = News(
                    title=item.title,
                    content=item.content,
                    link=item.link,
                    author=item.author,
                    category=item.category,
                    source_name=item.source_name,
                    source_url=item.source_url,
                    pub_date=item.pub_date or datetime.utcnow(),
                    guid=item.guid,
                    hash_code=item.hash_code
                )

                session.add(news)
                saved_count += 1

            # 批量提交
            session.commit()
            logger.info(f"保存新闻成功: {saved_count} 条")
            return saved_count

        except Exception as e:
            session.rollback()
            logger.error(f"保存新闻失败: {e}")
            raise DatabaseError(f"保存新闻失败: {str(e)}")

    def _update_source_status(self, source: RSSSource, success: bool, news_count: int = 0, error_msg: str = None):
        """更新RSS源状态"""
        try:
            now = datetime.utcnow()
            source.last_fetch_time = now

            if success:
                source.last_success_time = now
                source.error_count = 0
                source.total_news_count += news_count
            else:
                source.error_count += 1
                logger.warning(f"RSS源收集失败: {source.name}, 错误次数: {source.error_count}")

            # 如果错误次数过多，自动停用
            if source.error_count >= 10:
                source.is_active = False
                logger.warning(f"RSS源因错误次数过多被自动停用: {source.name}")

            session = get_db_session()
            session.commit()

        except Exception as e:
            logger.error(f"更新RSS源状态失败: {e}")

    def test_rss_source(self, url: str) -> Dict[str, Any]:
        """测试RSS源是否可用"""
        result = {
            'url': url,
            'accessible': False,
            'parseable': False,
            'news_count': 0,
            'error': None,
            'sample_news': []
        }

        try:
            # 测试可访问性
            rss_content = self._fetch_rss_content(url)
            result['accessible'] = True

            # 测试可解析性
            parser = self.parser_factory.create_parser(rss_content)
            news_items = parser.parse(rss_content, "测试源", url, "test")

            result['parseable'] = True
            result['news_count'] = len(news_items)

            # 获取前几条新闻作为样本
            for item in news_items[:3]:
                result['sample_news'].append({
                    'title': item.title,
                    'link': item.link,
                    'pub_date': item.pub_date.isoformat() if item.pub_date else None
                })

        except Exception as e:
            result['error'] = str(e)
            logger.warning(f"RSS源测试失败: {url}, 错误: {e}")

        return result

    def get_collector_statistics(self) -> Dict[str, Any]:
        """获取收集器统计信息"""
        session = get_db_session()

        try:
            # 统计新闻总数
            total_news = session.query(News).count()

            # 统计今日新闻数
            today = datetime.utcnow().date()
            today_news = session.query(News).filter(
                News.collect_time >= today
            ).count()

            # 统计最近7天新闻数
            week_ago = datetime.utcnow() - timedelta(days=7)
            week_news = session.query(News).filter(
                News.collect_time >= week_ago
            ).count()

            # 统计RSS源信息
            total_sources = session.query(RSSSource).count()
            active_sources = session.query(RSSSource).filter(RSSSource.is_active == True).count()

            return {
                'total_news': total_news,
                'today_news': today_news,
                'week_news': week_news,
                'total_sources': total_sources,
                'active_sources': active_sources,
                'inactive_sources': total_sources - active_sources
            }

        except Exception as e:
            logger.error(f"获取收集器统计信息失败: {e}")
            return {}

# 需要导入timedelta
from datetime import timedelta