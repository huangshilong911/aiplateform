"""模型服务数据模型"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from .base import BaseModel

class ModelService(BaseModel):
    """模型服务模型"""
    __tablename__ = "model_services"
    
    name = Column(String(200), nullable=False, unique=True)
    model_path = Column(String(500), nullable=False)
    model_type = Column(String(100), nullable=True)  # LLM, Vision, etc.
    
    # 服务器信息
    server_name = Column(String(100), nullable=False)
    gpu_indices = Column(String(200), nullable=True)  # 逗号分隔的GPU索引
    
    # 服务配置
    port = Column(Integer, nullable=True)
    max_model_len = Column(Integer, default=4096)
    gpu_memory_utilization = Column(Float, default=0.9)
    tensor_parallel_size = Column(Integer, default=1)
    
    # 状态信息
    status = Column(String(50), default="STOPPED")  # RUNNING, STOPPED, STARTING, STOPPING, ERROR
    pid = Column(Integer, nullable=True)
    start_time = Column(DateTime, nullable=True)
    
    # 统计信息
    total_requests = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # 配置参数
    extra_params = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<ModelService(name={self.name}, status={self.status}, server={self.server_name})>" 