"""
RSS源管理模块
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from core.database import get_db_session
from models.source import RSSSource
from core.exceptions import ValidationError, DatabaseError
from utils.logger import get_logger

logger = get_logger(__name__)

class RSSSourceManager:
    """RSS源管理器"""

    def __init__(self):
        self.session = get_db_session()

    def create_source(self, source_data: Dict[str, Any]) -> RSSSource:
        """创建RSS源"""
        try:
            # 验证必填字段
            required_fields = ['name', 'url', 'category']
            for field in required_fields:
                if not source_data.get(field):
                    raise ValidationError(f"缺少必填字段: {field}")

            # 检查名称是否已存在
            existing_source = self.get_source_by_name(source_data['name'])
            if existing_source:
                raise ValidationError(f"RSS源名称已存在: {source_data['name']}")

            # 检查URL是否已存在
            existing_source = self.get_source_by_url(source_data['url'])
            if existing_source:
                raise ValidationError(f"RSS源URL已存在: {source_data['url']}")

            # 创建RSS源
            source = RSSSource(
                name=source_data['name'],
                url=source_data['url'],
                category=source_data['category'],
                description=source_data.get('description', ''),
                is_active=source_data.get('is_active', True),
                fetch_interval=source_data.get('fetch_interval', 3600)
            )

            self.session.add(source)
            self.session.commit()

            logger.info(f"创建RSS源成功: {source.name}")
            return source

        except Exception as e:
            self.session.rollback()
            logger.error(f"创建RSS源失败: {e}")
            raise DatabaseError(f"创建RSS源失败: {str(e)}")

    def get_source_by_id(self, source_id: int) -> Optional[RSSSource]:
        """根据ID获取RSS源"""
        try:
            return self.session.query(RSSSource).filter(RSSSource.id == source_id).first()
        except Exception as e:
            logger.error(f"获取RSS源失败: {e}")
            return None

    def get_source_by_name(self, name: str) -> Optional[RSSSource]:
        """根据名称获取RSS源"""
        try:
            return self.session.query(RSSSource).filter(RSSSource.name == name).first()
        except Exception as e:
            logger.error(f"获取RSS源失败: {e}")
            return None

    def get_source_by_url(self, url: str) -> Optional[RSSSource]:
        """根据URL获取RSS源"""
        try:
            return self.session.query(RSSSource).filter(RSSSource.url == url).first()
        except Exception as e:
            logger.error(f"获取RSS源失败: {e}")
            return None

    def get_all_sources(self, active_only: bool = True) -> List[RSSSource]:
        """获取所有RSS源"""
        try:
            query = self.session.query(RSSSource)
            if active_only:
                query = query.filter(RSSSource.is_active == True)
            return query.all()
        except Exception as e:
            logger.error(f"获取RSS源列表失败: {e}")
            return []

    def get_sources_by_category(self, category: str, active_only: bool = True) -> List[RSSSource]:
        """根据分类获取RSS源"""
        try:
            query = self.session.query(RSSSource).filter(RSSSource.category == category)
            if active_only:
                query = query.filter(RSSSource.is_active == True)
            return query.all()
        except Exception as e:
            logger.error(f"获取分类RSS源失败: {e}")
            return []

    def update_source(self, source_id: int, update_data: Dict[str, Any]) -> Optional[RSSSource]:
        """更新RSS源"""
        try:
            source = self.get_source_by_id(source_id)
            if not source:
                return None

            # 检查名称冲突
            if 'name' in update_data and update_data['name'] != source.name:
                existing = self.get_source_by_name(update_data['name'])
                if existing:
                    raise ValidationError(f"RSS源名称已存在: {update_data['name']}")

            # 检查URL冲突
            if 'url' in update_data and update_data['url'] != source.url:
                existing = self.get_source_by_url(update_data['url'])
                if existing:
                    raise ValidationError(f"RSS源URL已存在: {update_data['url']}")

            # 更新字段
            for field, value in update_data.items():
                if hasattr(source, field):
                    setattr(source, field, value)

            self.session.commit()
            logger.info(f"更新RSS源成功: {source.name}")
            return source

        except Exception as e:
            self.session.rollback()
            logger.error(f"更新RSS源失败: {e}")
            raise DatabaseError(f"更新RSS源失败: {str(e)}")

    def delete_source(self, source_id: int) -> bool:
        """删除RSS源"""
        try:
            source = self.get_source_by_id(source_id)
            if not source:
                return False

            self.session.delete(source)
            self.session.commit()

            logger.info(f"删除RSS源成功: {source.name}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"删除RSS源失败: {e}")
            raise DatabaseError(f"删除RSS源失败: {str(e)}")

    def activate_source(self, source_id: int) -> bool:
        """激活RSS源"""
        return self._update_source_status(source_id, True)

    def deactivate_source(self, source_id: int) -> bool:
        """停用RSS源"""
        return self._update_source_status(source_id, False)

    def _update_source_status(self, source_id: int, is_active: bool) -> bool:
        """更新RSS源状态"""
        try:
            source = self.get_source_by_id(source_id)
            if not source:
                return False

            source.is_active = is_active
            self.session.commit()

            status = "激活" if is_active else "停用"
            logger.info(f"{status}RSS源成功: {source.name}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"更新RSS源状态失败: {e}")
            return False

    def get_sources_for_fetch(self) -> List[RSSSource]:
        """获取需要抓取的RSS源"""
        try:
            # 获取活跃的RSS源
            now = datetime.utcnow()
            query = self.session.query(RSSSource).filter(RSSSource.is_active == True)

            # 过滤需要抓取的源
            sources_to_fetch = []
            for source in query.all():
                if self._should_fetch_source(source, now):
                    sources_to_fetch.append(source)

            return sources_to_fetch

        except Exception as e:
            logger.error(f"获取待抓取RSS源失败: {e}")
            return []

    def _should_fetch_source(self, source: RSSSource, now: datetime) -> bool:
        """判断是否应该抓取该RSS源"""
        # 如果从未抓取过，需要抓取
        if not source.last_fetch_time:
            return True

        # 计算距离上次抓取的时间
        time_diff = now - source.last_fetch_time
        return time_diff.total_seconds() >= source.fetch_interval

    def get_unhealthy_sources(self, hours: int = 24) -> List[RSSSource]:
        """获取不健康的RSS源"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            query = self.session.query(RSSSource).filter(
                and_(
                    RSSSource.is_active == True,
                    or_(
                        RSSSource.error_count >= 5,
                        and_(
                            RSSSource.last_success_time < cutoff_time,
                            RSSSource.last_success_time.isnot(None)
                        )
                    )
                )
            )
            return query.all()

        except Exception as e:
            logger.error(f"获取不健康RSS源失败: {e}")
            return []

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        try:
            categories = self.session.query(RSSSource.category).distinct().all()
            return [category[0] for category in categories if category[0]]
        except Exception as e:
            logger.error(f"获取分类列表失败: {e}")
            return []

    def get_source_statistics(self) -> Dict[str, Any]:
        """获取RSS源统计信息"""
        try:
            total_sources = self.session.query(RSSSource).count()
            active_sources = self.session.query(RSSSource).filter(RSSSource.is_active == True).count()
            unhealthy_sources = len(self.get_unhealthy_sources())

            categories = self.get_categories()
            category_count = len(categories)

            return {
                'total_sources': total_sources,
                'active_sources': active_sources,
                'inactive_sources': total_sources - active_sources,
                'unhealthy_sources': unhealthy_sources,
                'total_categories': category_count,
                'categories': categories
            }

        except Exception as e:
            logger.error(f"获取RSS源统计信息失败: {e}")
            return {}

    def __del__(self):
        """析构函数"""
        try:
            self.session.close()
        except:
            pass