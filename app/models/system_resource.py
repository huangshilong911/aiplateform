"""系统资源数据模型"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from .base import BaseModel

class SystemResource(BaseModel):
    """系统资源模型"""
    __tablename__ = "system_resources"
    
    server_name = Column(String(100), nullable=False, index=True)
    
    # CPU信息
    cpu_count = Column(Integer, nullable=True)
    cpu_usage = Column(Float, nullable=True)  # 百分比
    load_average = Column(String(100), nullable=True)  # 1min,5min,15min
    
    # 内存信息
    memory_total = Column(Integer, nullable=True)  # MB
    memory_used = Column(Integer, nullable=True)   # MB
    memory_free = Column(Integer, nullable=True)   # MB
    memory_percent = Column(Float, nullable=True)  # 百分比
    
    # 磁盘信息
    disk_total = Column(Integer, nullable=True)    # GB
    disk_used = Column(Integer, nullable=True)     # GB
    disk_free = Column(Integer, nullable=True)     # GB
    disk_percent = Column(Float, nullable=True)    # 百分比
    
    # 网络信息
    network_sent = Column(Integer, nullable=True)  # MB
    network_recv = Column(Integer, nullable=True)  # MB
    
    # 系统信息
    uptime = Column(Integer, nullable=True)        # 运行时间（秒）
    boot_time = Column(DateTime, nullable=True)
    
    # 进程信息
    process_count = Column(Integer, nullable=True)
    
    # 详细信息（JSON格式）
    details = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<SystemResource(server={self.server_name}, cpu={self.cpu_usage}%, mem={self.memory_percent}%)>" 