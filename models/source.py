"""
RSS源数据模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from models.base import BaseModel

class RSSSource(BaseModel):
    """RSS源表"""
    __tablename__ = 'rss_sources'

    name = Column(String(100), unique=True, nullable=False, comment='RSS源名称')
    url = Column(String(500), unique=True, nullable=False, comment='RSS源URL')
    category = Column(String(50), nullable=False, comment='分类')
    description = Column(Text, comment='描述')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否启用')
    fetch_interval = Column(Integer, default=3600, nullable=False, comment='抓取间隔(秒)')
    last_fetch_time = Column(DateTime, comment='最后抓取时间')
    last_success_time = Column(DateTime, comment='最后成功抓取时间')
    error_count = Column(Integer, default=0, nullable=False, comment='连续错误次数')
    total_news_count = Column(Integer, default=0, nullable=False, comment='总新闻数量')

    # 添加索引
    __table_args__ = (
        Index('idx_category', 'category'),
        Index('idx_is_active', 'is_active'),
        Index('idx_last_fetch_time', 'last_fetch_time'),
        {'comment': 'RSS源配置表'}
    )

    def to_dict(self):
        """转换为字典，包含额外字段"""
        data = super().to_dict()
        if self.last_fetch_time:
            data['last_fetch_time'] = self.last_fetch_time.isoformat()
        if self.last_success_time:
            data['last_success_time'] = self.last_success_time.isoformat()
        return data

    def update_last_fetch(self, success: bool = True):
        """更新最后抓取时间"""
        self.last_fetch_time = datetime.utcnow()
        if success:
            self.last_success_time = datetime.utcnow()
            self.error_count = 0
        else:
            self.error_count += 1

    def is_healthy(self) -> bool:
        """检查RSS源是否健康"""
        # 如果连续错误超过5次，认为不健康
        if self.error_count >= 5:
            return False

        # 如果超过24小时没有成功抓取，认为不健康
        if self.last_success_time:
            time_diff = datetime.utcnow() - self.last_success_time
            if time_diff.total_seconds() > 24 * 3600:
                return False

        return True

    def __repr__(self):
        return f"<RSSSource(name='{self.name}', category='{self.category}', active={self.is_active})>"