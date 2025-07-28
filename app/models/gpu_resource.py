"""GPU资源数据模型"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from .base import BaseModel

class GpuResource(BaseModel):
    """GPU资源模型"""
    __tablename__ = "gpu_resources"
    
    server_name = Column(String(100), nullable=False, index=True)
    gpu_index = Column(Integer, nullable=False)
    gpu_name = Column(String(200), nullable=True)
    gpu_uuid = Column(String(100), nullable=True)
    
    # GPU使用率和内存信息
    utilization_gpu = Column(Float, nullable=True)
    utilization_memory = Column(Float, nullable=True)
    memory_total = Column(Integer, nullable=True)  # MB
    memory_used = Column(Integer, nullable=True)   # MB
    memory_free = Column(Integer, nullable=True)   # MB
    
    # 温度和功耗
    temperature = Column(Float, nullable=True)
    power_draw = Column(Float, nullable=True)
    power_limit = Column(Float, nullable=True)
    
    # 进程信息
    process_count = Column(Integer, default=0)
    
    # 状态
    status = Column(String(50), default="AVAILABLE")  # AVAILABLE, BUSY, ERROR
    
    def __repr__(self):
        return f"<GpuResource(server={self.server_name}, gpu={self.gpu_index}, util={self.utilization_gpu}%)>" 