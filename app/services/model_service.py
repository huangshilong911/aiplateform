"""大模型服务管理器"""

import os
import signal
import json
import threading
import time
import subprocess
import tempfile
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
        
        # 服务进程监控缓存
        self._process_cache = {}
        self._cache_timeout = 30  # 30秒缓存超时
        
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
    
    def diagnose_server_environment(self, server_name: str) -> Dict[str, Any]:
        """诊断服务器VLLM运行环境"""
        server_config = self._get_server_config(server_name)
        if not server_config:
            return {
                "success": False,
                "error": f"未找到服务器配置: {server_name}",
                "ssh_connection": False,
                "python_version": None,
                "vllm_installed": False,
                "vllm_version": None,
                "gpu_available": False,
                "nvidia_smi": False,
                "model_path_exists": False,
                "errors": ["服务器配置不存在"],
                "suggestions": ["请检查服务器配置"]
            }
        
        diagnosis = {
            "server_name": server_name,
            "ssh_connection": False,
            "python_version": None,
            "vllm_installed": False,
            "vllm_version": None,
            "gpu_available": False,
            "nvidia_smi": False,
            "model_path_exists": False,
            "errors": [],
            "suggestions": []
        }
        
        try:
            # 测试SSH连接
            exit_code, _, _ = self.ssh_manager.execute_command(
                server_config, "echo 'test'", timeout=10
            )
            diagnosis["ssh_connection"] = (exit_code == 0)
            
            if not diagnosis["ssh_connection"]:
                diagnosis["errors"].append("SSH连接失败")
                diagnosis["suggestions"].append("检查网络连接和SSH配置")
                return diagnosis
            
            # 检查Python版本
            exit_code, stdout, _ = self.ssh_manager.execute_command(
                server_config, "python --version 2>&1", timeout=10
            )
            if exit_code == 0:
                diagnosis["python_version"] = stdout.strip()
            else:
                # 尝试python3
                exit_code, stdout, _ = self.ssh_manager.execute_command(
                    server_config, "python3 --version 2>&1", timeout=10
                )
                if exit_code == 0:
                    diagnosis["python_version"] = stdout.strip()
            
            if not diagnosis["python_version"]:
                diagnosis["errors"].append("Python未安装或不可用")
                diagnosis["suggestions"].append("安装Python 3.8+")
            
            # 检查VLLM是否安装
            exit_code, stdout, _ = self.ssh_manager.execute_command(
                server_config, "python -c 'import vllm; print(vllm.__version__)' 2>/dev/null", timeout=15
            )
            if exit_code == 0:
                diagnosis["vllm_installed"] = True
                diagnosis["vllm_version"] = stdout.strip()
            else:
                # 尝试python3
                exit_code, stdout, _ = self.ssh_manager.execute_command(
                    server_config, "python3 -c 'import vllm; print(vllm.__version__)' 2>/dev/null", timeout=15
                )
                if exit_code == 0:
                    diagnosis["vllm_installed"] = True
                    diagnosis["vllm_version"] = stdout.strip()
            
            if not diagnosis["vllm_installed"]:
                diagnosis["errors"].append("VLLM未安装")
                diagnosis["suggestions"].append("安装VLLM: pip install vllm")
            
            # 检查GPU可用性 - 优先使用nvidia-smi检测
            # 首先检查nvidia-smi是否能检测到GPU
            exit_code, stdout, _ = self.ssh_manager.execute_command(
                server_config, "nvidia-smi --query-gpu=index,name --format=csv,noheader", timeout=10
            )
            
            if exit_code == 0 and stdout.strip():
                # nvidia-smi能检测到GPU，认为GPU硬件可用
                diagnosis["gpu_available"] = True
                logger.info(f"通过nvidia-smi检测到GPU: {stdout.strip()}")
            else:
                # nvidia-smi检测失败，尝试PyTorch检测作为备用
                exit_code, stdout, _ = self.ssh_manager.execute_command(
                    server_config, "python -c 'import torch; print(torch.cuda.is_available())' 2>/dev/null", timeout=10
                )
                if exit_code == 0 and "True" in stdout:
                    diagnosis["gpu_available"] = True
                else:
                    # 尝试python3
                    exit_code, stdout, _ = self.ssh_manager.execute_command(
                        server_config, "python3 -c 'import torch; print(torch.cuda.is_available())' 2>/dev/null", timeout=10
                    )
                    if exit_code == 0 and "True" in stdout:
                        diagnosis["gpu_available"] = True
            
            if not diagnosis["gpu_available"]:
                diagnosis["errors"].append("GPU不可用：nvidia-smi无法检测到GPU且PyTorch CUDA支持不可用")
                diagnosis["suggestions"].append("检查NVIDIA驱动安装或安装支持CUDA的PyTorch")
            
            # 检查nvidia-smi
            exit_code, _, _ = self.ssh_manager.execute_command(
                server_config, "nvidia-smi", timeout=10
            )
            diagnosis["nvidia_smi"] = (exit_code == 0)
            
            if not diagnosis["nvidia_smi"]:
                diagnosis["suggestions"].append("安装NVIDIA驱动和CUDA工具包")
            
            # 检查模型路径
            if server_config.model_path:
                exit_code, _, _ = self.ssh_manager.execute_command(
                    server_config, f"test -d '{server_config.model_path}'", timeout=5
                )
                diagnosis["model_path_exists"] = (exit_code == 0)
                
                if not diagnosis["model_path_exists"]:
                    diagnosis["errors"].append(f"模型路径不存在: {server_config.model_path}")
                    diagnosis["suggestions"].append("创建模型目录或检查路径配置")
            
            diagnosis["success"] = len(diagnosis["errors"]) == 0
            
        except Exception as e:
            logger.error(f"服务器环境诊断失败 {server_name}: {e}")
            diagnosis["errors"].append(f"诊断过程出错: {str(e)}")
            diagnosis["success"] = False
        
        return diagnosis
    
    def get_running_vllm_services(self, server_name: str) -> Dict[str, Any]:
        """获取指定服务器上运行中的VLLM服务列表"""
        server_config = self._get_server_config(server_name)
        if not server_config:
            return {
                "success": False,
                "error": f"未找到服务器配置: {server_name}",
                "services": []
            }
        
        try:
            # 查找VLLM进程
            cmd = """ps aux | grep -E '(vllm|api_server)' | grep -v grep | awk '{print $2, $3, $4, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20}'"""
            exit_code, stdout, stderr = self.ssh_manager.execute_command(
                server_config, cmd, timeout=30
            )
            
            if exit_code != 0:
                return {
                    "success": False,
                    "error": f"获取进程列表失败: {stderr}",
                    "services": []
                }
            
            services = []
            
            for line in stdout.strip().split('\n'):
                if not line.strip():
                    continue
                
                parts = line.strip().split()
                if len(parts) < 4:
                    continue
                
                pid = parts[0]
                cpu_usage = parts[1]
                memory_usage = parts[2]
                command_parts = parts[3:]
                
                # 提取端口号
                port = None
                for i, part in enumerate(command_parts):
                    if part == '--port' and i + 1 < len(command_parts):
                        port = command_parts[i + 1]
                        break
                
                services.append({
                    "pid": int(pid),
                    "port": port,
                    "cpu_usage": float(cpu_usage),
                    "memory_usage": float(memory_usage),
                    "command": " ".join(command_parts)
                })
            
            return {
                "success": True,
                "services": services,
                "server_name": server_name
            }
            
        except Exception as e:
            logger.error(f"获取运行中VLLM服务失败 {server_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "services": []
            }
    
    def get_service_logs(self, server_name: str, port: int, lines: int = 100) -> Dict[str, Any]:
        """获取VLLM服务日志"""
        server_config = self._get_server_config(server_name)
        if not server_config:
            return {
                "success": False,
                "error": f"未找到服务器配置: {server_name}",
                "logs": ""
            }
        
        try:
            # 通过端口找到进程ID
            cmd = f"lsof -ti :{port}"
            exit_code, stdout, _ = self.ssh_manager.execute_command(
                server_config, cmd, timeout=10
            )
            
            if exit_code != 0 or not stdout.strip():
                return {
                    "success": False,
                    "error": f"端口{port}上没有运行的服务",
                    "logs": ""
                }
            
            pid = stdout.strip().split('\n')[0]
            
            # 尝试获取日志文件路径
            log_paths = [
                f"/tmp/vllm_server_{port}.log",
                f"/var/log/vllm/server_{port}.log",
                f"~/vllm_{port}.log",
                f"/tmp/vllm_{port}.log"
            ]
            
            logs = ""
            for log_path in log_paths:
                cmd = f"test -f {log_path} && tail -n {lines} {log_path}"
                exit_code, stdout, _ = self.ssh_manager.execute_command(
                    server_config, cmd, timeout=10
                )
                if exit_code == 0 and stdout.strip():
                    logs = stdout.strip()
                    break
            
            # 如果没有找到日志文件，尝试从进程输出获取
            if not logs:
                # 检查是否有nohup输出
                cmd = f"ls -la /tmp/nohup.out /tmp/vllm*.out ~/nohup.out 2>/dev/null | head -5"
                exit_code, stdout, _ = self.ssh_manager.execute_command(
                    server_config, cmd, timeout=10
                )
                if exit_code == 0 and stdout.strip():
                    # 尝试从nohup.out获取最新日志
                    cmd = f"tail -n {lines} /tmp/nohup.out"
                    exit_code, stdout, _ = self.ssh_manager.execute_command(
                        server_config, cmd, timeout=10
                    )
                    if exit_code == 0:
                        logs = stdout.strip()
            
            if not logs:
                logs = f"未找到端口{port}的日志文件，可能需要手动配置日志路径"
            
            return {
                "success": True,
                "logs": logs,
                "pid": pid,
                "port": port
            }
            
        except Exception as e:
            logger.error(f"获取服务日志失败 {server_name}:{port}: {e}")
            return {
                "success": False,
                "error": str(e),
                "logs": ""
            }
    
    def check_port_usage(self, server_name: str) -> Dict[str, Any]:
        """检查服务器端口使用情况"""
        server_config = self._get_server_config(server_name)
        if not server_config:
            return {
                "success": False,
                "error": f"未找到服务器配置: {server_name}",
                "ports": []
            }
        
        try:
            # 检查端口使用情况
            port_range = self.config.vllm.default_port_range
            cmd = f"netstat -tuln | grep -E ':({port_range.start}|{port_range.start+1}|{port_range.start+2}|{port_range.start+3}|{port_range.start+4})\\b'"
            exit_code, stdout, _ = self.ssh_manager.execute_command(
                server_config, cmd, timeout=10
            )
            
            used_ports = []
            if exit_code == 0 and stdout.strip():
                for line in stdout.strip().split('\n'):
                    if ':' in line:
                        parts = line.split()
                        for part in parts:
                            if ':' in part and part.split(':')[-1].isdigit():
                                port = int(part.split(':')[-1])
                                if port_range.start <= port <= port_range.end:
                                    used_ports.append(port)
            
            # 生成可用端口列表
            available_ports = []
            for port in range(port_range.start, min(port_range.end, port_range.start + 20)):
                if port not in used_ports:
                    available_ports.append(port)
            
            return {
                "success": True,
                "used_ports": used_ports,
                "available_ports": available_ports[:10],  # 只返回前10个可用端口
                "port_range": {
                    "start": port_range.start,
                    "end": port_range.end
                }
            }
            
        except Exception as e:
            logger.error(f"检查端口使用情况失败 {server_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "ports": []
            }
    
    def _stop_service_by_pid(self, server_config: GpuServerConfig, pid: int) -> bool:
        """通过PID停止服务"""
        try:
            # 先尝试温和终止
            cmd = f"kill {pid}"
            exit_code, _, _ = self.ssh_manager.execute_command(server_config, cmd, timeout=10)
            
            if exit_code == 0:
                # 等待进程结束
                time.sleep(2)
                
                # 检查进程是否还存在
                cmd = f"kill -0 {pid} 2>/dev/null"
                exit_code, _, _ = self.ssh_manager.execute_command(server_config, cmd, timeout=5)
                
                if exit_code != 0:  # 进程不存在，说明停止成功
                    logger.info(f"成功停止服务进程 PID: {pid}")
                    return True
                else:
                    # 强制终止
                    cmd = f"kill -9 {pid}"
                    exit_code, _, _ = self.ssh_manager.execute_command(server_config, cmd, timeout=5)
                    
                    if exit_code == 0:
                        logger.info(f"强制停止服务进程 PID: {pid}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"停止服务进程失败 PID {pid}: {e}")
            return False
    
    def _stop_service_by_port(self, server_config: GpuServerConfig, port: int) -> Tuple[bool, Optional[int]]:
        """通过端口停止服务，返回(成功状态, 停止的PID)"""
        try:
            # 先找到占用端口的进程
            cmd = f"lsof -ti :{port}"
            exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd, timeout=10)
            
            if exit_code != 0 or not stdout.strip():
                logger.warning(f"端口{port}上没有运行的服务")
                return False, None
            
            pids = [int(pid.strip()) for pid in stdout.strip().split('\n') if pid.strip().isdigit()]
            
            if not pids:
                return False, None
            
            stopped_pids = []
            for pid in pids:
                if self._stop_service_by_pid(server_config, pid):
                    stopped_pids.append(pid)
            
            if stopped_pids:
                logger.info(f"通过端口{port}停止了进程: {stopped_pids}")
                return True, stopped_pids[0]  # 返回第一个停止的PID
            
            return False, None
            
        except Exception as e:
            logger.error(f"通过端口停止服务失败 {port}: {e}")
            return False, None
    
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
                
                # 检查是否有对应的持久化会话（Conda环境已激活）
                conda_env = None
                if service.extra_params and 'conda_env' in service.extra_params:
                    conda_env = service.extra_params['conda_env']
                
                use_persistent_session = False
                if conda_env and conda_env not in ['system-python', 'python3', 'vllm-builtin']:
                    # 检查是否存在活跃的持久化会话（按服务器名称检查）
                    session_status = self.ssh_manager.get_session_status(service.server_name)
                    if session_status and session_status.get('is_alive', False):
                        # 检查会话中是否已激活了环境
                        activated_env = session_status.get('activated_env')
                        if activated_env:
                            # 提取环境名称（处理完整路径格式）
                            activated_env_name = activated_env.split('/')[-1] if '/' in activated_env else activated_env
                            target_env_name = conda_env.strip()
                            
                            # 智能环境匹配：如果已激活任何有效的conda环境，都可以使用持久化会话
                            if (activated_env_name == target_env_name or 
                                activated_env.endswith(f"/{target_env_name}") or
                                (target_env_name == 'base' and activated_env_name and activated_env_name != 'base')):
                                logger.info(f"发现活跃的持久化会话，已激活环境: {activated_env}，将在会话中启动服务")
                                use_persistent_session = True
                            else:
                                logger.warning(f"发现持久化会话但环境不匹配（当前: {activated_env}，需要: {target_env_name}），将使用普通命令执行")
                        else:
                            logger.warning(f"发现持久化会话但未检测到激活的环境，将使用普通命令执行")
                    else:
                        logger.warning(f"未找到活跃的持久化会话，将使用普通命令执行")
                
                # 根据是否有持久化会话选择执行方式
                if use_persistent_session:
                    logger.info(f"在持久化会话中启动模型服务")
                    # 构建启动命令（持久化会话模式，不需要环境激活）
                    start_cmd = self._build_start_command(service, use_persistent_session=True)
                    logger.info(f"启动命令: {start_cmd}")
                    exit_code, stdout, stderr = self.ssh_manager.execute_in_persistent_session(
                        server_config, start_cmd, timeout=60
                    )
                    logger.info(f"命令执行结果 - 退出码: {exit_code}, 标准输出: {stdout}, 错误输出: {stderr}")
                else:
                    logger.info("使用普通SSH连接启动模型服务")
                    # 构建启动命令（普通模式，需要环境激活）
                    start_cmd = self._build_start_command(service, use_persistent_session=False)
                    exit_code, stdout, stderr = self.ssh_manager.execute_command(
                        server_config, start_cmd, timeout=60
                    )
                
                if exit_code == 0:
                    # 从输出中获取进程ID
                    pid = None
                    if stdout.strip():
                        try:
                            pid = int(stdout.strip().split('\n')[-1])
                        except (ValueError, IndexError):
                            logger.warning(f"无法从标准输出解析PID: {stdout}")
                    
                    # 如果从标准输出无法获取PID，尝试其他方法
                    if not pid:
                        # 对于持久化会话，尝试从PID文件读取
                        if use_persistent_session:
                            pid_file = f"/tmp/vllm_{service.name}_pid.txt"
                            time.sleep(1)  # 等待PID文件写入
                            try:
                                cmd_read_pid = f"cat {pid_file} 2>/dev/null"
                                exit_code_pid, stdout_pid, _ = self.ssh_manager.execute_command(server_config, cmd_read_pid, timeout=5)
                                if exit_code_pid == 0 and stdout_pid.strip():
                                    pid = int(stdout_pid.strip())
                                    logger.info(f"从PID文件获取到进程ID: {pid}")
                            except (ValueError, Exception) as e:
                                logger.warning(f"从PID文件读取失败: {e}")
                        
                        # 如果仍然没有PID，尝试通过端口查找
                        if not pid:
                            time.sleep(2)
                            pid = self._get_service_pid(server_config, port)
                            if pid:
                                logger.info(f"通过端口查找获取到进程ID: {pid}")
                    
                    if pid:
                        # 先设置为启动中状态
                        service.status = "STARTING"
                        service.pid = pid
                        service.updated_at = datetime.now()
                        session.commit()
                        
                        logger.info(f"模型服务PID获取成功: {service.name} (PID: {pid})，等待服务启动...")
                        
                        # 等待服务启动，增加等待时间并分阶段验证
                        max_wait_time = 180  # 最大等待180秒，大模型需要更长启动时间
                        check_interval = 3   # 每3秒检查一次
                        waited_time = 0
                        
                        while waited_time < max_wait_time:
                            time.sleep(check_interval)
                            waited_time += check_interval
                            
                            # 检查进程是否还存在
                            if not self._is_process_running(server_config, pid):
                                logger.warning(f"进程 {pid} 已退出，检查启动日志")
                                break
                            
                            # 检查端口是否开始监听
                            if self._is_port_in_use(server_config, port):
                                logger.info(f"端口 {port} 已开始监听，服务启动成功")
                                service.status = "RUNNING"
                                service.start_time = datetime.now()
                                service.updated_at = datetime.now()
                                session.commit()
                                
                                logger.info(f"模型服务启动成功: {service.name} (PID: {pid}, Port: {port})")
                                return True, f"模型服务启动成功，端口: {port}, PID: {pid}"
                            
                            logger.info(f"等待服务启动... ({waited_time}/{max_wait_time}秒)")
                        
                        # 超时或进程退出
                        service.status = "ERROR"
                        service.updated_at = datetime.now()
                        session.commit()
                        
                        # 获取启动日志以便调试
                        log_file = f"/tmp/vllm_{service.name}_{service.port}.log"
                        cmd_log = f"tail -20 {log_file} 2>/dev/null || echo '日志文件不存在'"
                        _, log_output, _ = self.ssh_manager.execute_command(server_config, cmd_log, timeout=5)
                        
                        logger.error(f"服务启动验证失败，最后20行日志:\n{log_output}")
                        return False, f"服务启动超时或启动过程中出错，请检查日志: {log_file}"
                    else:
                        service.status = "ERROR"
                        service.updated_at = datetime.now()
                        session.commit()
                        return False, "无法获取服务进程ID"
                    
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
    
    def _build_start_command(self, service: ModelService, use_persistent_session: bool = False) -> str:
        """构建启动命令"""
        vllm_config = self.config.vllm
        
        # 获取conda环境
        conda_env = None
        if service.extra_params and 'conda_env' in service.extra_params:
            conda_env = service.extra_params['conda_env']
        
        # 环境变量设置
        env_vars = []
        if service.gpu_indices:
            env_vars.append(f"CUDA_VISIBLE_DEVICES={service.gpu_indices}")
        
        # 根据环境选择Python命令
        if conda_env == 'vllm-builtin':
            python_cmd = "python3.10 -m vllm.entrypoints.openai.api_server || python3 -m vllm.entrypoints.openai.api_server || python -m vllm.entrypoints.openai.api_server"
        elif use_persistent_session:
            # 持久化会话中获取并使用Python的完整路径
            python_path = self._get_python_path_from_session(service.server_name)
            if python_path and python_path.strip():
                python_cmd = f"{python_path.strip()} -m vllm.entrypoints.openai.api_server"
                logger.info(f"✅ 使用完整Python路径: {python_path.strip()}")
            else:
                # 持久化会话模式：创建临时脚本确保环境传递
                session_status = self.ssh_manager.get_session_status(service.server_name)
                activated_env = session_status.get('activated_env') if session_status else None
                if activated_env:
                    env_name = activated_env.split('/')[-1] if '/' in activated_env else activated_env
                    python_cmd = f"bash -c 'source /opt/miniconda3/etc/profile.d/conda.sh && conda activate {env_name} && exec python -m vllm.entrypoints.openai.api_server'"
                    logger.info(f"🔧 使用bash脚本确保环境传递: conda activate {env_name}")
                else:
                    python_cmd = "python -m vllm.entrypoints.openai.api_server"
                    logger.warning(f"⚠️ 无法获取环境信息，使用相对路径: python")
        else:
            python_cmd = "python -m vllm.entrypoints.openai.api_server"
        
        # 基础命令 - 使用screen替代nohup
        if use_persistent_session:
            # 在持久会话的screen中直接运行，不需要nohup
            cmd_parts = [
                python_cmd,
                f"--model {service.model_path}",
                f"--port {service.port}",
                f"--max-model-len {service.max_model_len}",
                f"--gpu-memory-utilization {service.gpu_memory_utilization}",
                f"--tensor-parallel-size {service.tensor_parallel_size}",
                "--host 0.0.0.0",
                "--trust-remote-code"  # 允许远程代码
            ]
        else:
            # 普通SSH连接仍使用nohup
            cmd_parts = [
                f"nohup {python_cmd}",
                f"--model {service.model_path}",
                f"--port {service.port}",
                f"--max-model-len {service.max_model_len}",
                f"--gpu-memory-utilization {service.gpu_memory_utilization}",
                f"--tensor-parallel-size {service.tensor_parallel_size}",
                "--host 0.0.0.0",
                "--trust-remote-code"  # 允许远程代码
            ]
        
        # 额外参数（排除conda_env，因为它不是vllm的参数）
        if service.extra_params:
            for key, value in service.extra_params.items():
                if key == 'conda_env':  # 跳过conda_env参数
                    continue
                
                # 将下划线转换为连字符（vLLM参数格式）
                param_name = key.replace('_', '-')
                
                # 特殊处理worker-use-ray参数
                if key == 'worker_use_ray':
                    # worker_use_ray如果值大于0，则添加--worker-use-ray标志
                    if isinstance(value, (int, str)) and int(value) > 0:
                        cmd_parts.append("--worker-use-ray")
                elif isinstance(value, bool):
                    if value:
                        cmd_parts.append(f"--{param_name}")
                else:
                    cmd_parts.append(f"--{param_name} {value}")
        
        # 日志重定向和后台运行
        log_file = f"/tmp/vllm_{service.name}_{service.port}.log"
        if use_persistent_session:
            # 持久化会话的screen中直接运行，不需要后台符号&
            # screen会话本身就是持久的，进程会在screen中运行
            pid_file = f"/tmp/vllm_{service.name}_pid.txt"
            cmd_parts.extend([
                f"> {log_file} 2>&1",
                f"& PID=$! && echo $PID && echo $PID > {pid_file}"
            ])
        else:
            cmd_parts.extend([
                f"> {log_file} 2>&1",
                "&",
                "echo $!"  # 输出进程ID
            ])
        
        # 组合完整命令
        cmd_components = []
        
        # 注意：环境激活由调用方负责处理
        # - 持久化会话：环境已在会话中激活
        # - 普通SSH连接：由vllm_management.py的activate_conda_environment处理
        # 这里只处理vllm-builtin的特殊情况
        if not use_persistent_session and conda_env == 'vllm-builtin':
            # 内置vLLM环境：确保使用Python 3.10并安装vLLM
            setup_cmd = (
                "python3.10 -c 'import sys; print(sys.version)' || python3 -c 'import sys; print(sys.version)' && "
                "python3.10 -c 'import vllm' 2>/dev/null || python3 -c 'import vllm' 2>/dev/null || "
                "(echo '正在安装vLLM...' && pip install vllm)"
            )
            cmd_components.append(setup_cmd)
        
        # 添加环境变量
        if env_vars:
            cmd_components.append(" ".join(env_vars))
        
        # 添加主命令
        cmd_components.append(" ".join(cmd_parts))
        
        # 用 && 连接所有组件
        full_cmd = " && ".join(cmd_components)
        
        return full_cmd
    
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
        # 尝试多种方法获取PID
        for cmd in [
            f"lsof -ti :{port}",
            f"netstat -tlnp | grep :{port} | awk '{{print $7}}' | cut -d'/' -f1",
            f"ss -tlnp | grep :{port} | grep -o 'pid=[0-9]*' | cut -d'=' -f2"
        ]:
            exit_code, stdout, _ = self.ssh_manager.execute_command(server_config, cmd, timeout=10)
            
            if exit_code == 0 and stdout.strip():
                try:
                    return int(stdout.strip().split('\n')[0])
                except ValueError:
                    continue
        
        return None
    
    def _is_process_running(self, server_config: GpuServerConfig, pid: int) -> bool:
        """检查进程是否正在运行"""
        cmd = f"kill -0 {pid} 2>/dev/null"
        exit_code, _, _ = self.ssh_manager.execute_command(server_config, cmd, timeout=5)
        return exit_code == 0
    
    def _verify_service_running(self, server_config: GpuServerConfig, pid: int, port: int) -> bool:
        """验证服务是否正在运行"""
        # 检查进程是否存在
        if not self._is_process_running(server_config, pid):
            return False
        
        # 检查端口是否被占用
        return self._is_port_in_use(server_config, port)
    
    def _stop_service(self, server_config: GpuServerConfig, service: ModelService) -> bool:
        """停止服务进程"""
        # 检查是否有持久会话（可能在screen中运行）
        session_status = self.ssh_manager.get_session_status(service.server_name)
        use_persistent_session = session_status and session_status.get('is_alive', False)
        
        if service.pid:
            # 通过PID停止
            if use_persistent_session:
                # 在持久会话中执行停止命令
                cmd = f"kill -TERM {service.pid}"
                exit_code, _, _ = self.ssh_manager.execute_in_persistent_session(
                    server_config, cmd, timeout=10
                )
            else:
                # 普通SSH连接
                cmd = f"kill -TERM {service.pid}"
                exit_code, _, _ = self.ssh_manager.execute_command(server_config, cmd)
            
            if exit_code == 0:
                # 等待进程退出
                time.sleep(2)
                
                # 检查进程是否还存在
                cmd_check = f"kill -0 {service.pid} 2>/dev/null"
                if use_persistent_session:
                    exit_code, _, _ = self.ssh_manager.execute_in_persistent_session(
                        server_config, cmd_check, timeout=5
                    )
                else:
                    exit_code, _, _ = self.ssh_manager.execute_command(server_config, cmd_check)
                
                if exit_code != 0:
                    return True
                
                # 强制杀死
                cmd_kill = f"kill -KILL {service.pid}"
                if use_persistent_session:
                    self.ssh_manager.execute_in_persistent_session(
                        server_config, cmd_kill, timeout=5
                    )
                else:
                    self.ssh_manager.execute_command(server_config, cmd_kill)
                return True
        
        elif service.port:
            # 通过端口停止
            cmd = f"lsof -ti :{service.port} | xargs kill -TERM"
            if use_persistent_session:
                exit_code, _, _ = self.ssh_manager.execute_in_persistent_session(
                    server_config, cmd, timeout=10
                )
            else:
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
                
                return True, "删除成功"
                
        except Exception as e:
            logger.error(f"删除模型失败: {e}")
            return False, f"删除失败: {str(e)}"
    
    def _get_python_path_from_session(self, server_name: str) -> Optional[str]:
        """从持久化会话中获取Python的完整路径"""
        try:
            # 获取会话状态
            session_status = self.ssh_manager.get_session_status(server_name)
            if not session_status or not session_status.get('is_alive', False):
                logger.warning(f"无法获取服务器 {server_name} 的活跃会话")
                return None
            
            # 直接使用已知的环境路径构建Python路径（最可靠的方法）
            activated_env = session_status.get('activated_env')
            if activated_env and activated_env.startswith('/'):
                potential_python = f"{activated_env}/bin/python"
                logger.info(f"🎯 直接使用环境路径构建Python路径: {potential_python}")
                return potential_python
            
            # 获取服务器配置
            server_config = self._get_server_config(server_name)
            if not server_config:
                logger.warning(f"无法获取服务器 {server_name} 的配置")
                return None
            
            # 尝试 which python（作为备选方案）
            exit_code, stdout, stderr = self.ssh_manager.execute_in_persistent_session(
                server_config, "which python", timeout=10
            )
            
            logger.info(f"🔍 which python 执行结果 - 退出码: {exit_code}, 输出: '{stdout}', 错误: '{stderr}'")
            
            if exit_code == 0 and stdout.strip():
                python_path = stdout.strip()
                logger.info(f"📍 从持久化会话获取Python路径: {python_path}")
                
                # 简单验证：检查python可执行性
                test_cmd = f"{python_path} --version"
                test_exit_code, test_stdout, _ = self.ssh_manager.execute_in_persistent_session(
                    server_config, test_cmd, timeout=5
                )
                if test_exit_code == 0:
                    logger.info(f"✅ Python路径验证成功: {python_path} -> {test_stdout.strip()}")
                    return python_path
                else:
                    logger.warning(f"⚠️ Python路径验证失败: {python_path}")
            else:
                if exit_code == 0:
                    logger.warning(f"⚠️ which python 成功但无输出 - 输出为空: '{stdout}'")
                else:
                    logger.warning(f"⚠️ which python 命令失败 - 退出码: {exit_code}, 错误: {stderr}")
            
            logger.warning(f"⚠️ 无法从持久化会话获取有效的Python路径")
            return None
                
        except Exception as e:
            logger.error(f"获取Python路径失败: {e}")
            return None