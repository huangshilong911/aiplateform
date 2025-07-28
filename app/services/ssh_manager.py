"""SSH连接管理器"""

import paramiko
import socket
import threading
import time
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager
import logging

from ..config import GpuServerConfig

logger = logging.getLogger(__name__)

class SSHConnection:
    """SSH连接封装"""
    
    def __init__(self, server_config: GpuServerConfig):
        self.config = server_config
        self.client: Optional[paramiko.SSHClient] = None
        self.connected = False
        self.last_activity = time.time()
        self._lock = threading.Lock()
    
    def connect(self, timeout: int = 10) -> bool:
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.client.connect(
                hostname=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                timeout=timeout
            )
            
            self.connected = True
            self.last_activity = time.time()
            logger.info(f"SSH连接已建立: {self.config.name} ({self.config.host})")
            return True
            
        except (paramiko.AuthenticationException, 
                paramiko.SSHException, 
                socket.timeout, 
                ConnectionRefusedError) as e:
            logger.error(f"SSH连接失败 {self.config.name}: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开SSH连接"""
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                logger.warning(f"关闭SSH连接时出错: {e}")
            finally:
                self.client = None
                self.connected = False
    
    def execute_command(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """执行SSH命令"""
        if not self.connected or not self.client:
            if not self.connect():
                return -1, "", "SSH连接失败"
        
        try:
            with self._lock:
                stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
                
                exit_status = stdout.channel.recv_exit_status()
                stdout_data = stdout.read().decode('utf-8', errors='ignore')
                stderr_data = stderr.read().decode('utf-8', errors='ignore')
                
                self.last_activity = time.time()
                
                return exit_status, stdout_data, stderr_data
                
        except Exception as e:
            logger.error(f"执行SSH命令失败 {self.config.name}: {e}")
            self.connected = False
            return -1, "", str(e)
    
    def is_alive(self) -> bool:
        """检查连接是否存活"""
        if not self.connected or not self.client:
            return False
        
        try:
            transport = self.client.get_transport()
            if transport is None:
                return False
            
            transport.send_ignore()
            return True
            
        except Exception:
            self.connected = False
            return False

class SSHManager:
    """SSH连接管理器"""
    
    def __init__(self):
        self.connections: Dict[str, SSHConnection] = {}
        self.connection_timeout = 300  # 5分钟超时
        self._cleanup_thread = None
        self._running = True
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """启动连接清理线程"""
        def cleanup_worker():
            while self._running:
                try:
                    current_time = time.time()
                    to_remove = []
                    
                    for server_name, conn in self.connections.items():
                        # 检查连接超时或不可用
                        if (current_time - conn.last_activity > self.connection_timeout or 
                            not conn.is_alive()):
                            to_remove.append(server_name)
                    
                    # 清理过期连接
                    for server_name in to_remove:
                        self.disconnect_server(server_name)
                        logger.info(f"已清理过期SSH连接: {server_name}")
                    
                    time.sleep(60)  # 每分钟检查一次
                    
                except Exception as e:
                    logger.error(f"SSH连接清理线程出错: {e}")
                    time.sleep(60)
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def get_connection(self, server_config: GpuServerConfig) -> Optional[SSHConnection]:
        """获取SSH连接"""
        server_name = server_config.name
        
        # 如果连接存在且可用，直接返回
        if server_name in self.connections:
            conn = self.connections[server_name]
            if conn.is_alive():
                return conn
            else:
                # 连接不可用，移除并重新建立
                self.disconnect_server(server_name)
        
        # 创建新连接
        conn = SSHConnection(server_config)
        if conn.connect():
            self.connections[server_name] = conn
            return conn
        
        return None
    
    def disconnect_server(self, server_name: str):
        """断开指定服务器的连接"""
        if server_name in self.connections:
            self.connections[server_name].disconnect()
            del self.connections[server_name]
    
    def disconnect_all(self):
        """断开所有连接"""
        for conn in self.connections.values():
            conn.disconnect()
        self.connections.clear()
    
    def execute_command(self, server_config: GpuServerConfig, command: str, 
                       timeout: int = 30) -> Tuple[int, str, str]:
        """在指定服务器上执行命令"""
        conn = self.get_connection(server_config)
        if conn is None:
            return -1, "", f"无法连接到服务器 {server_config.name}"
        
        return conn.execute_command(command, timeout)
    
    @contextmanager
    def ssh_session(self, server_config: GpuServerConfig):
        """SSH会话上下文管理器"""
        conn = self.get_connection(server_config)
        if conn is None:
            raise ConnectionError(f"无法连接到服务器 {server_config.name}")
        
        try:
            yield conn
        finally:
            # 保持连接，由清理线程处理超时
            pass
    
    def get_connection_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有连接状态"""
        status = {}
        for server_name, conn in self.connections.items():
            status[server_name] = {
                "connected": conn.connected,
                "is_alive": conn.is_alive(),
                "last_activity": conn.last_activity,
                "host": conn.config.host,
                "port": conn.config.port
            }
        return status
    
    def shutdown(self):
        """关闭管理器"""
        self._running = False
        self.disconnect_all()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)

# 全局SSH管理器实例
_ssh_manager = None

def get_ssh_manager() -> SSHManager:
    """获取SSH管理器实例"""
    global _ssh_manager
    if _ssh_manager is None:
        _ssh_manager = SSHManager()
    return _ssh_manager 