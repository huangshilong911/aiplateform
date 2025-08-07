"""WebSocket SSH终端服务"""

import asyncio
import json
import logging
import threading
import time
from typing import Optional, Dict, Any
import paramiko
from fastapi import WebSocket, WebSocketDisconnect
from ..config import GpuServerConfig

logger = logging.getLogger(__name__)

class WebSocketSSHTerminal:
    """WebSocket SSH终端处理器"""
    
    def __init__(self, websocket: WebSocket, server_config: GpuServerConfig):
        self.websocket = websocket
        self.server_config = server_config
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.shell_channel: Optional[paramiko.Channel] = None
        self.running = False
        self.read_thread: Optional[threading.Thread] = None
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None  # 保存主线程的事件循环
        
    async def connect(self) -> bool:
        """建立SSH连接和shell会话"""
        try:
            # 保存当前事件循环
            self.event_loop = asyncio.get_running_loop()
            
            # 建立SSH连接
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.ssh_client.connect(
                hostname=self.server_config.host,
                port=self.server_config.port,
                username=self.server_config.username,
                password=self.server_config.password,
                timeout=10
            )
            
            # 创建交互式shell
            self.shell_channel = self.ssh_client.invoke_shell(
                term='xterm-256color',
                width=80,
                height=24
            )
            
            # 设置非阻塞模式
            self.shell_channel.settimeout(0.1)
            
            self.running = True
            
            # 启动读取线程
            self.read_thread = threading.Thread(target=self._read_from_ssh, daemon=True)
            self.read_thread.start()
            
            logger.info(f"WebSocket SSH终端连接已建立: {self.server_config.name}")
            
            # 发送连接成功消息
            await self.websocket.send_text(json.dumps({
                "type": "connected",
                "message": f"已连接到 {self.server_config.name} ({self.server_config.host})\r\n"
            }))
            
            return True
            
        except Exception as e:
            logger.error(f"WebSocket SSH终端连接失败: {e}")
            await self.websocket.send_text(json.dumps({
                "type": "error",
                "message": f"连接失败: {str(e)}\r\n"
            }))
            return False
    
    def _read_from_ssh(self):
        """从SSH读取数据的线程"""
        while self.running and self.shell_channel:
            try:
                if self.shell_channel.recv_ready():
                    data = self.shell_channel.recv(1024)
                    if data:
                        # 通过线程安全的方式发送数据到WebSocket
                        if self.event_loop and not self.event_loop.is_closed():
                            try:
                                future = asyncio.run_coroutine_threadsafe(
                                    self._send_to_websocket(data.decode('utf-8', errors='ignore')), 
                                    self.event_loop
                                )
                                # 可选：等待任务完成并处理异常
                                # future.result(timeout=1.0)
                            except Exception as e:
                                if self.running:
                                    logger.error(f"发送SSH数据到WebSocket失败: {e}")
                        else:
                            if self.running:
                                logger.warning("事件循环不可用，跳过SSH数据发送")
                
                time.sleep(0.01)  # 避免占用过多CPU
                
            except Exception as e:
                if self.running:
                    logger.error(f"SSH读取错误: {e}")
                break
    
    async def _send_to_websocket(self, data: str):
        """发送数据到WebSocket"""
        try:
            await self.websocket.send_text(json.dumps({
                "type": "output",
                "data": data
            }))
        except Exception as e:
            logger.error(f"WebSocket发送错误: {e}")
            self.running = False
    
    async def handle_websocket_message(self, message: str):
        """处理WebSocket消息"""
        try:
            data = json.loads(message)
            
            if data.get("type") == "input":
                # 处理用户输入
                input_data = data.get("data", "")
                if self.shell_channel and self.shell_channel.send_ready():
                    self.shell_channel.send(input_data.encode('utf-8'))
                    
            elif data.get("type") == "resize":
                # 处理终端大小调整
                width = data.get("cols", 80)
                height = data.get("rows", 24)
                if self.shell_channel:
                    self.shell_channel.resize_pty(width=width, height=height)
                    
        except json.JSONDecodeError:
            logger.warning(f"无效的WebSocket消息: {message}")
        except Exception as e:
            logger.error(f"处理WebSocket消息错误: {e}")
    
    async def disconnect(self):
        """断开连接"""
        self.running = False
        
        if self.shell_channel:
            try:
                self.shell_channel.close()
            except:
                pass
            self.shell_channel = None
        
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except:
                pass
            self.ssh_client = None
        
        # 等待读取线程结束
        if self.read_thread and self.read_thread.is_alive():
            # 给线程一些时间自然结束
            self.read_thread.join(timeout=2.0)
        
        logger.info(f"WebSocket SSH终端已断开: {self.server_config.name}")

class WebSocketTerminalManager:
    """WebSocket终端管理器"""
    
    def __init__(self):
        self.active_terminals: Dict[str, WebSocketSSHTerminal] = {}
    
    async def create_terminal(self, websocket: WebSocket, server_config: GpuServerConfig, 
                            terminal_id: str) -> WebSocketSSHTerminal:
        """创建新的终端会话"""
        # 如果已存在，先关闭旧的
        if terminal_id in self.active_terminals:
            await self.active_terminals[terminal_id].disconnect()
            del self.active_terminals[terminal_id]
        
        # 创建新终端
        terminal = WebSocketSSHTerminal(websocket, server_config)
        self.active_terminals[terminal_id] = terminal
        
        return terminal
    
    async def remove_terminal(self, terminal_id: str):
        """移除终端会话"""
        if terminal_id in self.active_terminals:
            await self.active_terminals[terminal_id].disconnect()
            del self.active_terminals[terminal_id]
    
    async def handle_websocket_connection(self, websocket: WebSocket, 
                                        server_config: GpuServerConfig, 
                                        terminal_id: str):
        """处理WebSocket连接"""
        terminal = None
        try:
            await websocket.accept()
            
            # 创建终端
            terminal = await self.create_terminal(websocket, server_config, terminal_id)
            
            # 建立SSH连接
            if not await terminal.connect():
                return
            
            # 处理WebSocket消息
            while terminal.running:
                try:
                    message = await websocket.receive_text()
                    await terminal.handle_websocket_message(message)
                except WebSocketDisconnect:
                    logger.info(f"WebSocket客户端断开连接: {terminal_id}")
                    break
                except Exception as e:
                    logger.error(f"WebSocket消息处理错误: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket连接错误: {e}")
        finally:
            if terminal:
                await terminal.disconnect()
            await self.remove_terminal(terminal_id)

# 全局终端管理器实例
_terminal_manager = None

def get_terminal_manager() -> WebSocketTerminalManager:
    """获取终端管理器实例"""
    global _terminal_manager
    if _terminal_manager is None:
        _terminal_manager = WebSocketTerminalManager()
    return _terminal_manager 