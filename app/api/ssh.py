"""SSH管理API路由"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from ..services.ssh_manager import get_ssh_manager
from ..config import AiPlatformConfig

router = APIRouter(prefix="/api/ssh", tags=["SSH管理"])

_config: Optional[AiPlatformConfig] = None

def init_ssh_router(config: AiPlatformConfig):
    """初始化SSH路由"""
    global _config
    _config = config

def get_config() -> AiPlatformConfig:
    """获取配置实例"""
    if _config is None:
        raise HTTPException(status_code=500, detail="配置未初始化")
    return _config

class CommandRequest(BaseModel):
    """命令执行请求模型"""
    command: str = Field(..., description="要执行的命令")
    timeout: int = Field(default=30, description="超时时间（秒）", ge=1, le=300)

@router.get("/servers", summary="获取SSH服务器列表")
async def get_ssh_servers() -> Dict[str, Any]:
    """获取配置的SSH服务器列表"""
    try:
        config = get_config()
        servers = []
        
        for server_config in config.gpu_servers:
            servers.append({
                "name": server_config.name,
                "host": server_config.host,
                "port": server_config.port,
                "username": server_config.username,
                "enabled": server_config.enabled
            })
        
        return {
            "success": True,
            "data": servers,
            "message": f"获取到{len(servers)}个SSH服务器"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取SSH服务器列表失败: {str(e)}")

@router.post("/servers/{server_name}/execute", summary="执行SSH命令")
async def execute_ssh_command(
    server_name: str, 
    request: CommandRequest
) -> Dict[str, Any]:
    """在指定服务器上执行SSH命令"""
    try:
        config = get_config()
        ssh_manager = get_ssh_manager()
        
        # 找到服务器配置
        server_config = None
        for server in config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
        
        if not server_config:
            raise HTTPException(status_code=404, detail=f"未找到服务器: {server_name}")
        
        if not server_config.enabled:
            raise HTTPException(status_code=400, detail=f"服务器'{server_name}'未启用")
        
        # 执行命令
        exit_code, stdout, stderr = ssh_manager.execute_command(
            server_config, request.command, request.timeout
        )
        
        return {
            "success": True,
            "data": {
                "server_name": server_name,
                "command": request.command,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "success": exit_code == 0
            },
            "message": f"命令执行{'成功' if exit_code == 0 else '失败'}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行SSH命令失败: {str(e)}")

@router.get("/servers/{server_name}/status", summary="检查SSH连接状态")
async def check_ssh_status(server_name: str) -> Dict[str, Any]:
    """检查指定服务器的SSH连接状态"""
    try:
        config = get_config()
        ssh_manager = get_ssh_manager()
        
        # 找到服务器配置
        server_config = None
        for server in config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
        
        if not server_config:
            raise HTTPException(status_code=404, detail=f"未找到服务器: {server_name}")
        
        # 测试连接
        exit_code, stdout, stderr = ssh_manager.execute_command(
            server_config, "echo 'connection_test'", 5
        )
        
        connected = exit_code == 0 and "connection_test" in stdout
        
        return {
            "success": True,
            "data": {
                "server_name": server_name,
                "host": server_config.host,
                "port": server_config.port,
                "connected": connected,
                "enabled": server_config.enabled,
                "test_result": {
                    "exit_code": exit_code,
                    "stdout": stdout.strip() if stdout else "",
                    "stderr": stderr.strip() if stderr else ""
                }
            },
            "message": f"服务器'{server_name}'连接{'正常' if connected else '异常'}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查SSH状态失败: {str(e)}")

@router.get("/connections", summary="获取所有SSH连接状态")
async def get_all_ssh_connections() -> Dict[str, Any]:
    """获取所有SSH连接的状态信息"""
    try:
        ssh_manager = get_ssh_manager()
        connection_status = ssh_manager.get_connection_status()
        
        return {
            "success": True,
            "data": connection_status,
            "message": f"获取到{len(connection_status)}个SSH连接状态"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取SSH连接状态失败: {str(e)}")

@router.post("/servers/{server_name}/disconnect", summary="断开SSH连接")
async def disconnect_ssh_server(server_name: str) -> Dict[str, Any]:
    """断开指定服务器的SSH连接"""
    try:
        ssh_manager = get_ssh_manager()
        ssh_manager.disconnect_server(server_name)
        
        return {
            "success": True,
            "data": {"server_name": server_name},
            "message": f"服务器'{server_name}'的SSH连接已断开"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"断开SSH连接失败: {str(e)}")

@router.post("/disconnect-all", summary="断开所有SSH连接")
async def disconnect_all_ssh() -> Dict[str, Any]:
    """断开所有SSH连接"""
    try:
        ssh_manager = get_ssh_manager()
        ssh_manager.disconnect_all()
        
        return {
            "success": True,
            "data": None,
            "message": "所有SSH连接已断开"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"断开所有SSH连接失败: {str(e)}")

@router.get("/servers/{server_name}/system-info", summary="获取服务器系统信息")
async def get_server_system_info(server_name: str) -> Dict[str, Any]:
    """获取指定服务器的系统信息"""
    try:
        config = get_config()
        ssh_manager = get_ssh_manager()
        
        # 找到服务器配置
        server_config = None
        for server in config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
        
        if not server_config:
            raise HTTPException(status_code=404, detail=f"未找到服务器: {server_name}")
        
        # 收集系统信息
        system_info = {}
        
        # 系统基本信息
        commands = {
            "hostname": "hostname",
            "uptime": "uptime",
            "kernel": "uname -r",
            "os": "cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"'",
            "cpu_info": "cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d':' -f2 | xargs",
            "memory_info": "free -h | grep Mem",
            "disk_info": "df -h /",
            "gpu_info": "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits"
        }
        
        for key, command in commands.items():
            try:
                exit_code, stdout, stderr = ssh_manager.execute_command(
                    server_config, command, 10
                )
                system_info[key] = {
                    "success": exit_code == 0,
                    "output": stdout.strip() if stdout else "",
                    "error": stderr.strip() if stderr else ""
                }
            except Exception as e:
                system_info[key] = {
                    "success": False,
                    "output": "",
                    "error": str(e)
                }
        
        return {
            "success": True,
            "data": {
                "server_name": server_name,
                "system_info": system_info
            },
            "message": f"获取服务器'{server_name}'系统信息成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}") 