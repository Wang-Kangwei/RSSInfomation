"""
基础数据模型
"""

from datetime import datetime
from core.database import db
from sqlalchemy import Column, Integer, String, Text, DateTime

class BaseModel(db.Model):
    """基础模型类"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    created_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='创建时间')
    updated_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment='更新时间')

    def to_dict(self):
        """转换为字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"

class SystemConfig(BaseModel):
    """系统配置表"""
    __tablename__ = 'system_config'

    config_key = Column(String(100), unique=True, nullable=False, comment='配置键')
    config_value = Column(Text, comment='配置值')
    description = Column(Text, comment='配置描述')

    def __repr__(self):
        return f"<SystemConfig(key={self.config_key})>"