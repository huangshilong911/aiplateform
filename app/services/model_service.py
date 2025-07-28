"""大模型服务管理器"""

import os
import signal
import json
import threading
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from ..config import AiPlatformConfig, GpuServerConfig
from ..models.model_service import ModelService
from ..database import get_database_manager
from .ssh_manager import get_ssh_manager

logger = logging.getLogger(__name__)

class ModelServiceManager:
    """大模型服务管理器"""
    
    def __init__(self, config: AiPlatformConfig):
        self.config = config
        self.ssh_manager = get_ssh_manager()
        self.db_manager = get_database_manager()
        
        # 用于分配端口的起始位置
        self._port_allocator = {}
        
    def get_all_models(self) -> List[Dict[str, Any]]:
        """获取所有模型服务"""
        try:
            with self.db_manager.get_session() as session:
                services = session.query(ModelService).all()
                return [service.to_dict() for service in services]
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []
    
    def get_model_by_id(self, model_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取模型服务"""
        try:
            with self.db_manager.get_session() as session:
                service = session.query(ModelService).filter(
                    ModelService.id == model_id
                ).first()
                return service.to_dict() if service else None
        except Exception as e:
            logger.error(f"获取模型详情失败: {e}")
            return None
    
    def get_running_models(self) -> List[Dict[str, Any]]:
        """获取正在运行的模型服务"""
        try:
            with self.db_manager.get_session() as session:
                services = session.query(ModelService).filter(
                    ModelService.status == "RUNNING"
                ).all()
                return [service.to_dict() for service in services]
        except Exception as e:
            logger.error(f"获取运行中模型失败: {e}")
            return []
    
    def discover_models(self, server_name: str) -> List[Dict[str, Any]]:
        """自动发现服务器上的模型"""
        server_config = self._get_server_config(server_name)
        if not server_config:
            return []
        
        try:
            # 查找模型目录
            cmd = f"find {server_config.model_path} -maxdepth 2 -type f -name 'config.json' -o -name 'pytorch_model.bin' -o -name 'model.safetensors' | head -20"
            exit_code, stdout, stderr = self.ssh_manager.execute_command(
                server_config, cmd, timeout=30
            )
            
            if exit_code != 0:
                logger.warning(f"模型发现失败 {server_name}: {stderr}")
                return []
            
            discovered_models = []
            model_dirs = set()
            
            for line in stdout.strip().split('\n'):
                if not line.strip():
                    continue
                
                model_dir = os.path.dirname(line.strip())
                if model_dir in model_dirs:
                    continue
                    
                model_dirs.add(model_dir)
                model_name = os.path.basename(model_dir)
                
                # 获取模型详细信息
                model_info = self._get_model_info(server_config, model_dir)
                
                discovered_models.append({
                    'name': model_name,
                    'path': model_dir,
                    'server_name': server_name,
                    'type': model_info.get('model_type', 'LLM'),
                    'size': model_info.get('size', 0),
                    'config': model_info.get('config', {})
                })
            
            return discovered_models
            
        except Exception as e:
            logger.error(f"模型发现过程出错 {server_name}: {e}")
            return []
    
    def _get_model_info(self, server_config: GpuServerConfig, model_path: str) -> Dict[str, Any]:
        """获取模型详细信息"""
        info = {
            'model_type': 'LLM',
            'size': 0,
            'config': {}
        }
        
        try:
            # 获取目录大小
            cmd_size = f"du -sm {model_path} | cut -f1"
            exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd_size)
            if exit_code == 0 and stdout.strip():
                info['size'] = int(stdout.strip())
            
            # 读取配置文件
            config_file = f"{model_path}/config.json"
            cmd_config = f"cat {config_file}"
            exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd_config)
            
            if exit_code == 0 and stdout.strip():
                try:
                    config = json.loads(stdout.strip())
                    info['config'] = config
                    
                    # 根据配置推断模型类型
                    if 'vision' in config.get('model_type', '').lower():
                        info['model_type'] = 'Vision'
                    elif 'chat' in config.get('model_type', '').lower():
                        info['model_type'] = 'Chat'
                    
                except json.JSONDecodeError:
                    pass
            
        except Exception as e:
            logger.warning(f"获取模型信息失败 {model_path}: {e}")
        
        return info
    
    def add_model(self, model_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """添加新的模型服务"""
        try:
            with self.db_manager.get_session() as session:
                # 检查名称是否重复
                existing = session.query(ModelService).filter(
                    ModelService.name == model_data['name']
                ).first()
                
                if existing:
                    raise ValueError(f"模型名称已存在: {model_data['name']}")
                
                # 创建模型服务
                service = ModelService(
                    name=model_data['name'],
                    model_path=model_data['model_path'],
                    model_type=model_data.get('model_type', 'LLM'),
                    server_name=model_data['server_name'],
                    gpu_indices=model_data.get('gpu_indices', ''),
                    max_model_len=model_data.get('max_model_len', 4096),
                    gpu_memory_utilization=model_data.get('gpu_memory_utilization', 0.9),
                    tensor_parallel_size=model_data.get('tensor_parallel_size', 1),
                    extra_params=model_data.get('extra_params', {}),
                    status="STOPPED"
                )
                
                session.add(service)
                session.flush()
                
                return service.to_dict()
                
        except Exception as e:
            logger.error(f"添加模型失败: {e}")
            return None
    
    def start_model(self, model_id: int) -> Tuple[bool, str]:
        """启动模型服务"""
        try:
            with self.db_manager.get_session() as session:
                service = session.query(ModelService).filter(
                    ModelService.id == model_id
                ).first()
                
                if not service:
                    return False, "模型服务不存在"
                
                if service.status == "RUNNING":
                    return False, "模型服务已在运行"
                
                server_config = self._get_server_config(service.server_name)
                if not server_config:
                    return False, f"服务器配置不存在: {service.server_name}"
                
                # 更新状态为启动中
                service.status = "STARTING"
                service.updated_at = datetime.now()
                session.commit()
                
                # 分配端口
                port = self._allocate_port(service.server_name)
                service.port = port
                
                # 构建启动命令
                start_cmd = self._build_start_command(service)
                
                # 执行启动命令
                exit_code, stdout, stderr = self.ssh_manager.execute_command(
                    server_config, start_cmd, timeout=60
                )
                
                if exit_code == 0:
                    # 获取进程ID
                    pid = self._get_service_pid(server_config, port)
                    
                    service.status = "RUNNING"
                    service.pid = pid
                    service.start_time = datetime.now()
                    service.updated_at = datetime.now()
                    session.commit()
                    
                    logger.info(f"模型服务启动成功: {service.name} (PID: {pid}, Port: {port})")
                    return True, f"模型服务启动成功，端口: {port}"
                    
                else:
                    service.status = "ERROR"
                    service.updated_at = datetime.now()
                    session.commit()
                    
                    error_msg = f"启动失败: {stderr}"
                    logger.error(f"模型服务启动失败 {service.name}: {error_msg}")
                    return False, error_msg
                
        except Exception as e:
            logger.error(f"启动模型服务失败: {e}")
            return False, f"启动失败: {str(e)}"
    
    def stop_model(self, model_id: int) -> Tuple[bool, str]:
        """停止模型服务"""
        try:
            with self.db_manager.get_session() as session:
                service = session.query(ModelService).filter(
                    ModelService.id == model_id
                ).first()
                
                if not service:
                    return False, "模型服务不存在"
                
                if service.status == "STOPPED":
                    return False, "模型服务已停止"
                
                server_config = self._get_server_config(service.server_name)
                if not server_config:
                    return False, f"服务器配置不存在: {service.server_name}"
                
                # 更新状态为停止中
                service.status = "STOPPING"
                service.updated_at = datetime.now()
                session.commit()
                
                # 停止服务
                success = self._stop_service(server_config, service)
                
                if success:
                    service.status = "STOPPED"
                    service.pid = None
                    service.start_time = None
                    service.updated_at = datetime.now()
                    session.commit()
                    
                    # 释放端口
                    if service.port:
                        self._release_port(service.server_name, service.port)
                    
                    logger.info(f"模型服务已停止: {service.name}")
                    return True, "模型服务已停止"
                    
                else:
                    service.status = "ERROR"
                    service.updated_at = datetime.now()
                    session.commit()
                    
                    return False, "停止服务失败"
                
        except Exception as e:
            logger.error(f"停止模型服务失败: {e}")
            return False, f"停止失败: {str(e)}"
    
    def _build_start_command(self, service: ModelService) -> str:
        """构建启动命令"""
        vllm_config = self.config.vllm
        
        # 基础命令
        cmd_parts = [
            "python -m vllm.entrypoints.openai.api_server",
            f"--model {service.model_path}",
            f"--port {service.port}",
            f"--max-model-len {service.max_model_len}",
            f"--gpu-memory-utilization {service.gpu_memory_utilization}",
            f"--tensor-parallel-size {service.tensor_parallel_size}",
            "--host 0.0.0.0"
        ]
        
        # GPU设置
        if service.gpu_indices:
            cmd_parts.append(f"--device cuda:{service.gpu_indices}")
        
        # 额外参数
        if service.extra_params:
            for key, value in service.extra_params.items():
                if isinstance(value, bool):
                    if value:
                        cmd_parts.append(f"--{key}")
                else:
                    cmd_parts.append(f"--{key} {value}")
        
        # 后台运行
        cmd_parts.append("&")
        
        return " ".join(cmd_parts)
    
    def _allocate_port(self, server_name: str) -> int:
        """为服务器分配端口"""
        if server_name not in self._port_allocator:
            self._port_allocator[server_name] = self.config.vllm.default_port_range.start
        
        # 检查端口是否被占用
        server_config = self._get_server_config(server_name)
        if server_config:
            for port in range(self._port_allocator[server_name], 
                            self.config.vllm.default_port_range.end):
                if not self._is_port_in_use(server_config, port):
                    self._port_allocator[server_name] = port + 1
                    return port
        
        # 如果所有端口都被占用，返回默认端口
        return self.config.vllm.default_port_range.start
    
    def _is_port_in_use(self, server_config: GpuServerConfig, port: int) -> bool:
        """检查端口是否被占用"""
        cmd = f"netstat -tuln | grep :{port}"
        exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd)
        return exit_code == 0 and stdout.strip()
    
    def _release_port(self, server_name: str, port: int):
        """释放端口"""
        # 这里可以添加端口释放逻辑，目前简单实现
        pass
    
    def _get_service_pid(self, server_config: GpuServerConfig, port: int) -> Optional[int]:
        """获取服务进程ID"""
        cmd = f"lsof -ti :{port}"
        exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd)
        
        if exit_code == 0 and stdout.strip():
            try:
                return int(stdout.strip().split('\n')[0])
            except ValueError:
                pass
        
        return None
    
    def _stop_service(self, server_config: GpuServerConfig, service: ModelService) -> bool:
        """停止服务进程"""
        if service.pid:
            # 通过PID停止
            cmd = f"kill -TERM {service.pid}"
            exit_code, _, _ = self.ssh_manager.execute_command(server_config, cmd)
            
            if exit_code == 0:
                # 等待进程退出
                time.sleep(2)
                
                # 检查进程是否还存在
                cmd_check = f"kill -0 {service.pid} 2>/dev/null"
                exit_code, _, _ = self.ssh_manager.execute_command(server_config, cmd_check)
                
                if exit_code != 0:
                    return True
                
                # 强制杀死
                cmd_kill = f"kill -KILL {service.pid}"
                self.ssh_manager.execute_command(server_config, cmd_kill)
                return True
        
        elif service.port:
            # 通过端口停止
            cmd = f"lsof -ti :{service.port} | xargs kill -TERM"
            exit_code, _, _ = self.ssh_manager.execute_command(server_config, cmd)
            return exit_code == 0
        
        return False
    
    def _get_server_config(self, server_name: str) -> Optional[GpuServerConfig]:
        """获取服务器配置"""
        for server_config in self.config.gpu_servers:
            if server_config.name == server_name:
                return server_config
        return None
    
    def update_model_status(self):
        """更新所有模型服务状态"""
        try:
            with self.db_manager.get_session() as session:
                services = session.query(ModelService).filter(
                    ModelService.status.in_(["RUNNING", "STARTING", "STOPPING"])
                ).all()
                
                for service in services:
                    server_config = self._get_server_config(service.server_name)
                    if not server_config:
                        continue
                    
                    # 检查进程是否还在运行
                    if service.pid:
                        cmd = f"kill -0 {service.pid} 2>/dev/null"
                        exit_code, _, _ = self.ssh_manager.execute_command(server_config, cmd)
                        
                        if exit_code != 0:
                            # 进程已死亡
                            service.status = "STOPPED"
                            service.pid = None
                            service.start_time = None
                            service.updated_at = datetime.now()
                    
                    elif service.port:
                        # 通过端口检查服务状态
                        if not self._is_port_in_use(server_config, service.port):
                            service.status = "STOPPED"
                            service.start_time = None
                            service.updated_at = datetime.now()
                
                session.commit()
                
        except Exception as e:
            logger.error(f"更新模型状态失败: {e}")
    
    def delete_model(self, model_id: int) -> Tuple[bool, str]:
        """删除模型服务"""
        try:
            with self.db_manager.get_session() as session:
                service = session.query(ModelService).filter(
                    ModelService.id == model_id
                ).first()
                
                if not service:
                    return False, "模型服务不存在"
                
                # 如果正在运行，先停止
                if service.status == "RUNNING":
                    success, msg = self.stop_model(model_id)
                    if not success:
                        return False, f"停止服务失败: {msg}"
                
                session.delete(service)
                session.commit()
                
                logger.info(f"模型服务已删除: {service.name}")
                return True, "模型服务已删除"
                
        except Exception as e:
            logger.error(f"删除模型服务失败: {e}")
            return False, f"删除失败: {str(e)}" 