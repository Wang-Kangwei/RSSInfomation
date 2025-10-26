"""
新闻业务服务
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from core.database import get_db_session
from models.news import News
from models.source import RSSSource
from core.exceptions import NewsNotFoundError, DatabaseError
from utils.logger import get_logger

logger = get_logger(__name__)

class NewsService:
    """新闻业务服务类"""

    def __init__(self):
        self.session = get_db_session()

    def get_today_news(self, category: str = None, limit: int = 20) -> List[News]:
        """获取今日新闻"""
        try:
            today = datetime.utcnow().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())

            query = self.session.query(News).filter(
                and_(
                    News.collect_time >= start_of_day,
                    News.collect_time <= end_of_day,
                    News.is_published == True
                )
            )

            # 按分类筛选
            if category:
                query = query.filter(News.category == category)

            # 按发布时间倒序排列，限制数量
            news_list = query.order_by(desc(News.pub_date)).limit(limit).all()

            logger.info(f"获取今日新闻: 分类={category or '全部'}, 数量={len(news_list)}")
            return news_list

        except Exception as e:
            logger.error(f"获取今日新闻失败: {e}")
            raise DatabaseError(f"获取今日新闻失败: {str(e)}")

    def get_recent_news(self, days: int = 7, category: str = None, limit: int = 50) -> List[News]:
        """获取最近几天的新闻"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            query = self.session.query(News).filter(
                and_(
                    News.collect_time >= cutoff_date,
                    News.is_published == True
                )
            )

            # 按分类筛选
            if category:
                query = query.filter(News.category == category)

            # 按发布时间倒序排列，限制数量
            news_list = query.order_by(desc(News.pub_date)).limit(limit).all()

            logger.info(f"获取最近{days}天新闻: 分类={category or '全部'}, 数量={len(news_list)}")
            return news_list

        except Exception as e:
            logger.error(f"获取最近新闻失败: {e}")
            raise DatabaseError(f"获取最近新闻失败: {str(e)}")

    def get_news_by_date(self, date: datetime.date, category: str = None, limit: int = 50) -> List[News]:
        """获取指定日期的新闻"""
        try:
            start_of_day = datetime.combine(date, datetime.min.time())
            end_of_day = datetime.combine(date, datetime.max.time())

            query = self.session.query(News).filter(
                and_(
                    News.collect_time >= start_of_day,
                    News.collect_time <= end_of_day,
                    News.is_published == True
                )
            )

            # 按分类筛选
            if category:
                query = query.filter(News.category == category)

            # 按发布时间倒序排列，限制数量
            news_list = query.order_by(desc(News.pub_date)).limit(limit).all()

            logger.info(f"获取指定日期新闻: 日期={date}, 分类={category or '全部'}, 数量={len(news_list)}")
            return news_list

        except Exception as e:
            logger.error(f"获取指定日期新闻失败: {e}")
            raise DatabaseError(f"获取指定日期新闻失败: {str(e)}")

    def get_news_by_source(self, source_name: str, limit: int = 20) -> List[News]:
        """获取指定RSS源的新闻"""
        try:
            query = self.session.query(News).filter(
                and_(
                    News.source_name == source_name,
                    News.is_published == True
                )
            )

            news_list = query.order_by(desc(News.pub_date)).limit(limit).all()

            logger.info(f"获取RSS源新闻: 源={source_name}, 数量={len(news_list)}")
            return news_list

        except Exception as e:
            logger.error(f"获取RSS源新闻失败: {e}")
            raise DatabaseError(f"获取RSS源新闻失败: {str(e)}")

    def search_news(self, keyword: str, category: str = None, limit: int = 20) -> List[News]:
        """搜索新闻"""
        try:
            query = self.session.query(News).filter(
                and_(
                    or_(
                        News.title.contains(keyword),
                        News.content.contains(keyword)
                    ),
                    News.is_published == True
                )
            )

            # 按分类筛选
            if category:
                query = query.filter(News.category == category)

            # 按发布时间倒序排列，限制数量
            news_list = query.order_by(desc(News.pub_date)).limit(limit).all()

            logger.info(f"搜索新闻: 关键词={keyword}, 分类={category or '全部'}, 数量={len(news_list)}")
            return news_list

        except Exception as e:
            logger.error(f"搜索新闻失败: {e}")
            raise DatabaseError(f"搜索新闻失败: {str(e)}")

    def get_news_by_id(self, news_id: int) -> Optional[News]:
        """根据ID获取新闻"""
        try:
            news = self.session.query(News).filter(
                and_(
                    News.id == news_id,
                    News.is_published == True
                )
            ).first()

            if news:
                # 增加查看次数
                news.increment_view_count()
                self.session.commit()

            return news

        except Exception as e:
            logger.error(f"获取新闻详情失败: {e}")
            return None

    def get_hot_news(self, days: int = 1, limit: int = 10) -> List[News]:
        """获取热门新闻（按查看次数排序）"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            news_list = self.session.query(News).filter(
                and_(
                    News.collect_time >= cutoff_date,
                    News.is_published == True
                )
            ).order_by(desc(News.view_count)).limit(limit).all()

            logger.info(f"获取热门新闻: 天数={days}, 数量={len(news_list)}")
            return news_list

        except Exception as e:
            logger.error(f"获取热门新闻失败: {e}")
            raise DatabaseError(f"获取热门新闻失败: {str(e)}")

    def get_news_categories(self) -> List[str]:
        """获取所有新闻分类"""
        try:
            categories = self.session.query(News.category).distinct().all()
            return [category[0] for category in categories if category[0]]

        except Exception as e:
            logger.error(f"获取新闻分类失败: {e}")
            return []

    def get_news_statistics(self) -> Dict[str, Any]:
        """获取新闻统计信息"""
        try:
            # 总新闻数
            total_news = self.session.query(News).count()

            # 今日新闻数
            today = datetime.utcnow().date()
            today_news = self.session.query(News).filter(
                News.collect_time >= today
            ).count()

            # 本周新闻数
            week_ago = datetime.utcnow() - timedelta(days=7)
            week_news = self.session.query(News).filter(
                News.collect_time >= week_ago
            ).count()

            # 本月新闻数
            month_ago = datetime.utcnow() - timedelta(days=30)
            month_news = self.session.query(News).filter(
                News.collect_time >= month_ago
            ).count()

            # 各分类统计
            category_stats = {}
            categories = self.get_news_categories()
            for category in categories:
                count = self.session.query(News).filter(
                    and_(
                        News.category == category,
                        News.collect_time >= week_ago
                    )
                ).count()
                category_stats[category] = count

            return {
                'total_news': total_news,
                'today_news': today_news,
                'week_news': week_news,
                'month_news': month_news,
                'category_stats': category_stats
            }

        except Exception as e:
            logger.error(f"获取新闻统计信息失败: {e}")
            return {}

    def cleanup_old_news(self, days: int = 7) -> int:
        """清理过期新闻"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # 统计要删除的新闻数量
            count = self.session.query(News).filter(
                News.collect_time < cutoff_date
            ).count()

            if count > 0:
                # 删除过期新闻
                deleted_count = self.session.query(News).filter(
                    News.collect_time < cutoff_date
                ).delete()

                self.session.commit()
                logger.info(f"清理过期新闻完成: 删除了 {deleted_count} 条新闻")
                return deleted_count
            else:
                logger.info("没有需要清理的过期新闻")
                return 0

        except Exception as e:
            self.session.rollback()
            logger.error(f"清理过期新闻失败: {e}")
            raise DatabaseError(f"清理过期新闻失败: {str(e)}")

    def update_news_status(self, news_id: int, is_published: bool) -> bool:
        """更新新闻发布状态"""
        try:
            news = self.session.query(News).filter(News.id == news_id).first()
            if not news:
                return False

            news.is_published = is_published
            self.session.commit()

            status = "发布" if is_published else "隐藏"
            logger.info(f"新闻状态更新成功: {news.title} -> {status}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"更新新闻状态失败: {e}")
            return False

    def __del__(self):
        """析构函数"""
        try:
            self.session.close()
        except:
            pass