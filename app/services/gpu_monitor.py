"""GPU监控服务"""

import re
import json
import threading
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ..config import AiPlatformConfig, GpuServerConfig
from ..models.gpu_resource import GpuResource
from ..database import get_database_manager
from .ssh_manager import get_ssh_manager

logger = logging.getLogger(__name__)

class GpuMonitorService:
    """GPU监控服务"""
    
    def __init__(self, config: AiPlatformConfig):
        self.config = config
        self.ssh_manager = get_ssh_manager()
        self.db_manager = get_database_manager()
        
        self._monitoring = False
        self._monitor_thread = None
        
    def start_monitoring(self):
        """启动GPU监控"""
        if self._monitoring:
            logger.warning("GPU监控已在运行")
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self._monitor_thread.start()
        logger.info("GPU监控服务已启动")
    
    def stop_monitoring(self):
        """停止GPU监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=10)
        logger.info("GPU监控服务已停止")
    
    def _monitor_worker(self):
        """监控工作线程"""
        while self._monitoring:
            try:
                self._collect_all_gpu_info()
                time.sleep(self.config.monitoring.gpu_interval)
            except Exception as e:
                logger.error(f"GPU监控循环出错: {e}")
                time.sleep(5)
    
    def _collect_all_gpu_info(self):
        """收集所有服务器的GPU信息"""
        for server_config in self.config.gpu_servers:
            if server_config.enabled:
                try:
                    gpu_resources = self._collect_gpu_info(server_config)
                    if gpu_resources:
                        self._save_gpu_resources(gpu_resources)
                        logger.debug(f"已收集GPU信息: {server_config.name} ({len(gpu_resources)}个GPU)")
                except Exception as e:
                    logger.error(f"收集GPU信息失败 {server_config.name}: {e}")
    
    def _collect_gpu_info(self, server_config: GpuServerConfig) -> List[GpuResource]:
        """收集单个服务器的GPU信息"""
        # 执行nvidia-smi命令获取GPU信息
        cmd = "nvidia-smi --query-gpu=index,name,uuid,utilization.gpu,utilization.memory,memory.total,memory.used,memory.free,temperature.gpu,power.draw,power.limit --format=csv,noheader,nounits"
        
        exit_code, stdout, stderr = self.ssh_manager.execute_command(
            server_config, cmd, timeout=30
        )
        
        if exit_code != 0:
            logger.warning(f"nvidia-smi命令执行失败 {server_config.name}: {stderr}")
            return []
        
        gpu_resources = []
        current_time = datetime.now()
        
        for line in stdout.strip().split('\n'):
            if not line.strip():
                continue
                
            try:
                parts = [part.strip() for part in line.split(',')]
                if len(parts) >= 11:
                    # 解析基础数据
                    memory_total = int(float(parts[5])) if parts[5] != '[Not Supported]' else None
                    memory_used = int(float(parts[6])) if parts[6] != '[Not Supported]' else None
                    
                    # 计算真实的显存使用率
                    utilization_memory = None
                    if memory_total and memory_used and memory_total > 0:
                        utilization_memory = round((memory_used / memory_total) * 100, 2)
                    elif parts[4] != '[Not Supported]':
                        # 如果计算失败，使用nvidia-smi的原始值作为备用
                        utilization_memory = float(parts[4])
                    
                    gpu_resource = GpuResource(
                        server_name=server_config.name,
                        gpu_index=int(parts[0]),
                        gpu_name=parts[1],
                        gpu_uuid=parts[2] if parts[2] != '[Not Supported]' else None,
                        utilization_gpu=float(parts[3]) if parts[3] != '[Not Supported]' else None,
                        utilization_memory=utilization_memory,
                        memory_total=memory_total,
                        memory_used=memory_used,
                        memory_free=int(float(parts[7])) if parts[7] != '[Not Supported]' else None,
                        temperature=float(parts[8]) if parts[8] != '[Not Supported]' else None,
                        power_draw=float(parts[9]) if parts[9] != '[Not Supported]' else None,
                        power_limit=float(parts[10]) if parts[10] != '[Not Supported]' else None,
                        created_at=current_time,
                        updated_at=current_time
                    )
                    
                    # 获取GPU进程信息
                    process_count = self._get_gpu_process_count(server_config, gpu_resource.gpu_index)
                    gpu_resource.process_count = process_count
                    
                    # 判断GPU状态
                    if gpu_resource.utilization_gpu is not None:
                        if gpu_resource.utilization_gpu > 80:
                            gpu_resource.status = "BUSY"
                        elif gpu_resource.utilization_gpu > 10:
                            gpu_resource.status = "RUNNING"
                        else:
                            gpu_resource.status = "AVAILABLE"
                    
                    gpu_resources.append(gpu_resource)
                    
            except (ValueError, IndexError) as e:
                logger.warning(f"解析GPU信息失败 {server_config.name}: {line} - {e}")
                continue
        
        return gpu_resources
    
    def _get_gpu_process_count(self, server_config: GpuServerConfig, gpu_index: int) -> int:
        """获取指定GPU的进程数量"""
        cmd = f"nvidia-smi -i {gpu_index} --query-compute-apps=pid --format=csv,noheader,nounits"
        
        exit_code, stdout, stderr = self.ssh_manager.execute_command(
            server_config, cmd, timeout=10
        )
        
        if exit_code != 0:
            return 0
        
        processes = [line.strip() for line in stdout.strip().split('\n') if line.strip()]
        return len(processes)
    
    def _save_gpu_resources(self, gpu_resources: List[GpuResource]):
        """保存GPU资源信息到数据库"""
        try:
            with self.db_manager.get_session() as session:
                session.add_all(gpu_resources)
                
                # 清理历史数据
                self._cleanup_old_data(session)
                
        except Exception as e:
            logger.error(f"保存GPU资源信息失败: {e}")
    
    def _cleanup_old_data(self, session):
        """清理旧的GPU资源数据"""
        cutoff_time = datetime.now() - timedelta(
            hours=self.config.monitoring.gpu_history_retention
        )
        
        try:
            deleted_count = session.query(GpuResource).filter(
                GpuResource.created_at < cutoff_time
            ).delete()
            
            if deleted_count > 0:
                logger.debug(f"已清理{deleted_count}条旧GPU数据")
                
        except Exception as e:
            logger.error(f"清理旧GPU数据失败: {e}")
    
    def get_current_gpu_resources(self) -> List[Dict[str, Any]]:
        """获取当前GPU资源状态"""
        try:
            with self.db_manager.get_session() as session:
                # 获取每个服务器每个GPU的最新记录
                gpu_resources = []
                
                for server_config in self.config.gpu_servers:
                    if not server_config.enabled:
                        continue
                        
                    for gpu_idx in range(server_config.gpu_count):
                        latest_resource = session.query(GpuResource).filter(
                            GpuResource.server_name == server_config.name,
                            GpuResource.gpu_index == gpu_idx
                        ).order_by(GpuResource.created_at.desc()).first()
                        
                        if latest_resource:
                            gpu_resources.append(latest_resource.to_dict())
                
                return gpu_resources
                
        except Exception as e:
            logger.error(f"获取当前GPU资源失败: {e}")
            return []
    
    def get_gpu_resources_by_server(self, server_name: str) -> List[Dict[str, Any]]:
        """获取指定服务器的GPU资源"""
        try:
            with self.db_manager.get_session() as session:
                resources = session.query(GpuResource).filter(
                    GpuResource.server_name == server_name
                ).order_by(
                    GpuResource.gpu_index.asc(),
                    GpuResource.created_at.desc()
                ).all()
                
                # 获取每个GPU的最新记录
                latest_resources = {}
                for resource in resources:
                    key = f"{resource.server_name}-{resource.gpu_index}"
                    if key not in latest_resources:
                        latest_resources[key] = resource
                
                return [resource.to_dict() for resource in latest_resources.values()]
                
        except Exception as e:
            logger.error(f"获取服务器GPU资源失败: {e}")
            return []
    
    def get_gpu_history(self, server_name: str, gpu_index: int, 
                       hours: int = 1) -> List[Dict[str, Any]]:
        """获取GPU历史数据"""
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            
            with self.db_manager.get_session() as session:
                resources = session.query(GpuResource).filter(
                    GpuResource.server_name == server_name,
                    GpuResource.gpu_index == gpu_index,
                    GpuResource.created_at >= start_time
                ).order_by(GpuResource.created_at.asc()).all()
                
                return [resource.to_dict() for resource in resources]
                
        except Exception as e:
            logger.error(f"获取GPU历史数据失败: {e}")
            return []
    
    def get_gpu_summary(self) -> Dict[str, Any]:
        """获取GPU资源摘要"""
        try:
            current_resources = self.get_current_gpu_resources()
            
            total_gpus = len(current_resources)
            available_gpus = len([r for r in current_resources if r['status'] == 'AVAILABLE'])
            busy_gpus = len([r for r in current_resources if r['status'] == 'BUSY'])
            running_gpus = len([r for r in current_resources if r['status'] == 'RUNNING'])
            
            total_memory = sum([r['memory_total'] or 0 for r in current_resources])
            used_memory = sum([r['memory_used'] or 0 for r in current_resources])
            
            avg_utilization = 0
            if current_resources:
                valid_utils = [r['utilization_gpu'] for r in current_resources 
                             if r['utilization_gpu'] is not None]
                if valid_utils:
                    avg_utilization = sum(valid_utils) / len(valid_utils)
            
            return {
                "total_gpus": total_gpus,
                "available_gpus": available_gpus,
                "busy_gpus": busy_gpus,
                "running_gpus": running_gpus,
                "total_memory_mb": total_memory,
                "used_memory_mb": used_memory,
                "memory_utilization": (used_memory / total_memory * 100) if total_memory > 0 else 0,
                "average_gpu_utilization": round(avg_utilization, 2),
                "servers": len(self.config.gpu_servers)
            }
            
        except Exception as e:
            logger.error(f"获取GPU摘要失败: {e}")
            return {
                "total_gpus": 0,
                "available_gpus": 0,
                "busy_gpus": 0,
                "running_gpus": 0,
                "total_memory_mb": 0,
                "used_memory_mb": 0,
                "memory_utilization": 0,
                "average_gpu_utilization": 0,
                "servers": 0
            } 