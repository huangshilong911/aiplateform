"""系统监控服务"""

import threading
import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ..config import AiPlatformConfig, GpuServerConfig  
from ..models.system_resource import SystemResource
from ..database import get_database_manager
from .ssh_manager import get_ssh_manager

logger = logging.getLogger(__name__)

class SystemMonitorService:
    """系统监控服务"""
    
    def __init__(self, config: AiPlatformConfig):
        self.config = config
        self.ssh_manager = get_ssh_manager()
        self.db_manager = get_database_manager()
        
        self._monitoring = False
        self._monitor_thread = None
        
    def start_monitoring(self):
        """启动系统监控"""
        if self._monitoring:
            logger.warning("系统监控已在运行")
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self._monitor_thread.start()
        logger.info("系统监控服务已启动")
    
    def stop_monitoring(self):
        """停止系统监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=10)
        logger.info("系统监控服务已停止")
    
    def _monitor_worker(self):
        """监控工作线程"""
        while self._monitoring:
            try:
                self._collect_all_system_info()
                time.sleep(self.config.monitoring.system_interval)
            except Exception as e:
                logger.error(f"系统监控循环出错: {e}")
                time.sleep(5)
    
    def _collect_all_system_info(self):
        """收集所有服务器的系统信息"""
        for server_config in self.config.gpu_servers:
            if server_config.enabled:
                try:
                    system_resource = self._collect_system_info(server_config)
                    if system_resource:
                        self._save_system_resource(system_resource)
                        logger.debug(f"已收集系统信息: {server_config.name}")
                except Exception as e:
                    logger.error(f"收集系统信息失败 {server_config.name}: {e}")
    
    def _collect_system_info(self, server_config: GpuServerConfig) -> Optional[SystemResource]:
        """收集单个服务器的系统信息"""
        current_time = datetime.now()
        
        # 收集CPU信息
        cpu_info = self._get_cpu_info(server_config)
        
        # 收集内存信息
        memory_info = self._get_memory_info(server_config)
        
        # 收集磁盘信息
        disk_info = self._get_disk_info(server_config)
        
        # 收集网络信息
        network_info = self._get_network_info(server_config)
        
        # 收集系统运行信息
        system_info = self._get_system_info(server_config)
        
        # 收集进程信息
        process_info = self._get_process_info(server_config)
        
        if not any([cpu_info, memory_info, disk_info, system_info]):
            return None
        
        system_resource = SystemResource(
            server_name=server_config.name,
            created_at=current_time,
            updated_at=current_time
        )
        
        # 设置CPU信息
        if cpu_info:
            system_resource.cpu_count = cpu_info.get('cpu_count')
            system_resource.cpu_usage = cpu_info.get('cpu_usage')
            system_resource.load_average = cpu_info.get('load_average')
        
        # 设置内存信息
        if memory_info:
            system_resource.memory_total = memory_info.get('total')
            system_resource.memory_used = memory_info.get('used')
            system_resource.memory_free = memory_info.get('free')
            system_resource.memory_percent = memory_info.get('percent')
        
        # 设置磁盘信息
        if disk_info:
            system_resource.disk_total = disk_info.get('total')
            system_resource.disk_used = disk_info.get('used')
            system_resource.disk_free = disk_info.get('free')
            system_resource.disk_percent = disk_info.get('percent')
        
        # 设置网络信息
        if network_info:
            system_resource.network_sent = network_info.get('sent')
            system_resource.network_recv = network_info.get('recv')
        
        # 设置系统信息
        if system_info:
            system_resource.uptime = system_info.get('uptime')
            system_resource.boot_time = system_info.get('boot_time')
        
        # 设置进程信息
        if process_info:
            system_resource.process_count = process_info.get('process_count')
        
        # 设置详细信息（处理datetime序列化）
        details = {
            'cpu': cpu_info,
            'memory': memory_info,
            'disk': disk_info,
            'network': network_info,
            'system': system_info,
            'process': process_info
        }
        
        # 处理datetime对象
        if 'system' in details and 'boot_time' in details['system']:
            boot_time = details['system']['boot_time']
            if boot_time:
                details['system']['boot_time'] = boot_time.isoformat() if hasattr(boot_time, 'isoformat') else str(boot_time)
        
        system_resource.details = details
        
        return system_resource
    
    def _get_cpu_info(self, server_config: GpuServerConfig) -> Dict[str, Any]:
        """获取CPU信息"""
        try:
            # 获取CPU核心数
            cmd_cpu_count = "nproc"
            exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd_cpu_count)
            cpu_count = int(stdout.strip()) if exit_code == 0 and stdout.strip() else None
            
            # 获取CPU使用率（使用top命令）
            cmd_cpu_usage = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1"
            exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd_cpu_usage)
            cpu_usage_str = stdout.strip()
            cpu_usage = float(cpu_usage_str) if exit_code == 0 and cpu_usage_str else None
            
            # 获取负载平均值
            cmd_load = "uptime | awk -F'load average:' '{print $2}' | sed 's/^ *//'"
            exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd_load)
            load_average = stdout.strip() if exit_code == 0 else None
            
            return {
                'cpu_count': cpu_count,
                'cpu_usage': cpu_usage,
                'load_average': load_average
            }
            
        except Exception as e:
            logger.warning(f"获取CPU信息失败 {server_config.name}: {e}")
            return {}
    
    def _get_memory_info(self, server_config: GpuServerConfig) -> Dict[str, Any]:
        """获取内存信息"""
        try:
            cmd = "free -m | grep '^Mem:'"
            exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd)
            
            if exit_code != 0 or not stdout.strip():
                return {}
            
            parts = stdout.strip().split()
            if len(parts) >= 7:
                total = int(parts[1])
                used = int(parts[2])
                free = int(parts[3])
                percent = (used / total * 100) if total > 0 else 0
                
                return {
                    'total': total,
                    'used': used,
                    'free': free,
                    'percent': round(percent, 2)
                }
            
        except Exception as e:
            logger.warning(f"获取内存信息失败 {server_config.name}: {e}")
        
        return {}
    
    def _get_disk_info(self, server_config: GpuServerConfig) -> Dict[str, Any]:
        """获取磁盘信息"""
        try:
            cmd = "df -h / | tail -1"
            exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd)
            
            if exit_code != 0 or not stdout.strip():
                return {}
            
            parts = stdout.strip().split()
            if len(parts) >= 6:
                total_str = parts[1].replace('G', '').replace('T', '000')
                used_str = parts[2].replace('G', '').replace('T', '000')
                free_str = parts[3].replace('G', '').replace('T', '000')
                percent_str = parts[4].replace('%', '')
                
                try:
                    total = int(float(total_str))
                    used = int(float(used_str))
                    free = int(float(free_str))
                    percent = float(percent_str)
                    
                    return {
                        'total': total,
                        'used': used,
                        'free': free,
                        'percent': percent
                    }
                except ValueError:
                    pass
            
        except Exception as e:
            logger.warning(f"获取磁盘信息失败 {server_config.name}: {e}")
        
        return {}
    
    def _get_network_info(self, server_config: GpuServerConfig) -> Dict[str, Any]:
        """获取网络信息"""
        try:
            cmd = "cat /proc/net/dev | grep -v 'lo:' | awk 'NR>2 {sent+=$10; recv+=$2} END {print recv/1024/1024, sent/1024/1024}'"
            exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd)
            
            if exit_code != 0 or not stdout.strip():
                return {}
            
            parts = stdout.strip().split()
            if len(parts) >= 2:
                recv = int(float(parts[0]))
                sent = int(float(parts[1]))
                
                return {
                    'recv': recv,
                    'sent': sent
                }
            
        except Exception as e:
            logger.warning(f"获取网络信息失败 {server_config.name}: {e}")
        
        return {}
    
    def _get_system_info(self, server_config: GpuServerConfig) -> Dict[str, Any]:
        """获取系统运行信息"""
        try:
            # 获取系统运行时间
            cmd_uptime = "cat /proc/uptime | awk '{print int($1)}'"
            exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd_uptime)
            uptime = int(stdout.strip()) if exit_code == 0 and stdout.strip() else None
            
            # 获取启动时间
            cmd_boot = "uptime -s"
            exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd_boot)
            boot_time_str = stdout.strip()
            boot_time = None
            if exit_code == 0 and boot_time_str:
                try:
                    boot_time = datetime.strptime(boot_time_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
            
            return {
                'uptime': uptime,
                'boot_time': boot_time
            }
            
        except Exception as e:
            logger.warning(f"获取系统信息失败 {server_config.name}: {e}")
            return {}
    
    def _get_process_info(self, server_config: GpuServerConfig) -> Dict[str, Any]:
        """获取进程信息"""
        try:
            cmd = "ps aux | wc -l"
            exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd)
            
            if exit_code == 0 and stdout.strip():
                process_count = int(stdout.strip()) - 1  # 减去标题行
                return {'process_count': process_count}
            
        except Exception as e:
            logger.warning(f"获取进程信息失败 {server_config.name}: {e}")
        
        return {}
    
    def _save_system_resource(self, system_resource: SystemResource):
        """保存系统资源信息到数据库"""
        try:
            with self.db_manager.get_session() as session:
                session.add(system_resource)
                
                # 清理历史数据
                self._cleanup_old_data(session)
                
        except Exception as e:
            logger.error(f"保存系统资源信息失败: {e}")
    
    def _cleanup_old_data(self, session):
        """清理旧的系统资源数据"""
        cutoff_time = datetime.now() - timedelta(
            hours=self.config.monitoring.system_history_retention
        )
        
        try:
            deleted_count = session.query(SystemResource).filter(
                SystemResource.created_at < cutoff_time
            ).delete()
            
            if deleted_count > 0:
                logger.debug(f"已清理{deleted_count}条旧系统数据")
                
        except Exception as e:
            logger.error(f"清理旧系统数据失败: {e}")
    
    def get_current_system_resources(self) -> List[Dict[str, Any]]:
        """获取当前系统资源状态"""
        try:
            with self.db_manager.get_session() as session:
                resources = []
                
                for server_config in self.config.gpu_servers:
                    if not server_config.enabled:
                        continue
                        
                    latest_resource = session.query(SystemResource).filter(
                        SystemResource.server_name == server_config.name
                    ).order_by(SystemResource.created_at.desc()).first()
                    
                    if latest_resource:
                        resources.append(latest_resource.to_dict())
                
                return resources
                
        except Exception as e:
            logger.error(f"获取当前系统资源失败: {e}")
            return []
    
    def get_system_resource_by_server(self, server_name: str) -> Optional[Dict[str, Any]]:
        """获取指定服务器的系统资源"""
        try:
            with self.db_manager.get_session() as session:
                resource = session.query(SystemResource).filter(
                    SystemResource.server_name == server_name
                ).order_by(SystemResource.created_at.desc()).first()
                
                return resource.to_dict() if resource else None
                
        except Exception as e:
            logger.error(f"获取服务器系统资源失败: {e}")
            return None
    
    def get_system_history(self, server_name: str, hours: int = 1) -> List[Dict[str, Any]]:
        """获取系统历史数据"""
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            
            with self.db_manager.get_session() as session:
                resources = session.query(SystemResource).filter(
                    SystemResource.server_name == server_name,
                    SystemResource.created_at >= start_time
                ).order_by(SystemResource.created_at.asc()).all()
                
                return [resource.to_dict() for resource in resources]
                
        except Exception as e:
            logger.error(f"获取系统历史数据失败: {e}")
            return [] 