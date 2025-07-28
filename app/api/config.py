"""配置管理API路由"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..config import AiPlatformConfig, GpuServerConfig
from ..services.ssh_manager import get_ssh_manager

router = APIRouter(prefix="/api/config", tags=["配置管理"])

_config: Optional[AiPlatformConfig] = None

def init_config_router(config: AiPlatformConfig):
    """初始化配置路由"""
    global _config
    _config = config

def get_config() -> AiPlatformConfig:
    """获取配置实例"""
    if _config is None:
        raise HTTPException(status_code=500, detail="配置未初始化")
    return _config

class GpuServerCreateRequest(BaseModel):
    """创建GPU服务器请求模型"""
    name: str = Field(..., description="服务器名称")
    host: str = Field(..., description="服务器地址")
    port: int = Field(default=22, description="SSH端口")
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    gpu_count: int = Field(..., description="GPU数量", ge=1)
    enabled: bool = Field(default=True, description="是否启用")
    model_path: str = Field(..., description="模型存储路径")

class GpuServerUpdateRequest(BaseModel):
    """更新GPU服务器请求模型"""
    host: Optional[str] = Field(None, description="服务器地址")
    port: Optional[int] = Field(None, description="SSH端口")
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    gpu_count: Optional[int] = Field(None, description="GPU数量", ge=1)
    enabled: Optional[bool] = Field(None, description="是否启用")
    model_path: Optional[str] = Field(None, description="模型存储路径")

@router.get("/servers", summary="获取GPU服务器配置")
async def get_gpu_servers_config() -> Dict[str, Any]:
    """获取所有GPU服务器配置"""
    try:
        config = get_config()
        servers = []
        
        for server_config in config.gpu_servers:
            servers.append({
                "name": server_config.name,
                "host": server_config.host,
                "port": server_config.port,
                "username": server_config.username,
                "gpu_count": server_config.gpu_count,
                "enabled": server_config.enabled,
                "model_path": server_config.model_path
                # 注意：不返回密码信息
            })
        
        return {
            "success": True,
            "data": servers,
            "message": f"获取到{len(servers)}个GPU服务器配置"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务器配置失败: {str(e)}")

@router.post("/servers", summary="添加GPU服务器")
async def add_gpu_server(request: GpuServerCreateRequest) -> Dict[str, Any]:
    """添加新的GPU服务器配置"""
    try:
        config = get_config()
        
        # 创建服务器配置
        server_config = GpuServerConfig(
            name=request.name,
            host=request.host,
            port=request.port,
            username=request.username,
            password=request.password,
            gpu_count=request.gpu_count,
            enabled=request.enabled,
            model_path=request.model_path
        )
        
        # 测试SSH连接
        ssh_manager = get_ssh_manager()
        exit_code, stdout, stderr = ssh_manager.execute_command(
            server_config, "echo 'connection_test'", 5
        )
        
        if exit_code != 0:
            raise HTTPException(
                status_code=400, 
                detail=f"SSH连接测试失败: {stderr}"
            )
        
        # 添加到配置
        success = config.add_gpu_server(server_config)
        if not success:
            raise HTTPException(
                status_code=400, 
                detail=f"服务器名称'{request.name}'已存在"
            )
        
        return {
            "success": True,
            "data": {
                "name": request.name,
                "host": request.host,
                "port": request.port,
                "username": request.username,
                "gpu_count": request.gpu_count,
                "enabled": request.enabled,
                "model_path": request.model_path
            },
            "message": f"GPU服务器'{request.name}'添加成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加GPU服务器失败: {str(e)}")

@router.put("/servers/{server_name}", summary="更新GPU服务器配置")
async def update_gpu_server(
    server_name: str, 
    request: GpuServerUpdateRequest
) -> Dict[str, Any]:
    """更新指定GPU服务器的配置"""
    try:
        config = get_config()
        
        # 构建更新数据
        updates = {}
        if request.host is not None:
            updates["host"] = request.host
        if request.port is not None:
            updates["port"] = request.port
        if request.username is not None:
            updates["username"] = request.username
        if request.password is not None:
            updates["password"] = request.password
        if request.gpu_count is not None:
            updates["gpu_count"] = request.gpu_count
        if request.enabled is not None:
            updates["enabled"] = request.enabled
        if request.model_path is not None:
            updates["model_path"] = request.model_path
        
        if not updates:
            raise HTTPException(status_code=400, detail="没有提供要更新的字段")
        
        # 更新配置
        success = config.update_gpu_server(server_name, updates)
        if not success:
            raise HTTPException(status_code=404, detail=f"未找到服务器: {server_name}")
        
        return {
            "success": True,
            "data": {
                "server_name": server_name,
                "updates": updates
            },
            "message": f"GPU服务器'{server_name}'配置更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新GPU服务器配置失败: {str(e)}")

@router.delete("/servers/{server_name}", summary="删除GPU服务器")
async def delete_gpu_server(server_name: str) -> Dict[str, Any]:
    """删除指定的GPU服务器配置"""
    try:
        config = get_config()
        
        success = config.remove_gpu_server(server_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"未找到服务器: {server_name}")
        
        # 断开SSH连接
        ssh_manager = get_ssh_manager()
        ssh_manager.disconnect_server(server_name)
        
        return {
            "success": True,
            "data": {"server_name": server_name},
            "message": f"GPU服务器'{server_name}'删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除GPU服务器失败: {str(e)}")

@router.post("/servers/{server_name}/test", summary="测试服务器连接")
async def test_server_connection(server_name: str) -> Dict[str, Any]:
    """测试指定服务器的连接"""
    try:
        config = get_config()
        
        # 找到服务器配置
        server_config = None
        for server in config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
        
        if not server_config:
            raise HTTPException(status_code=404, detail=f"未找到服务器: {server_name}")
        
        # 测试连接
        ssh_manager = get_ssh_manager()
        
        # 基本连接测试
        exit_code, stdout, stderr = ssh_manager.execute_command(
            server_config, "echo 'connection_test'", 10
        )
        
        connection_success = exit_code == 0 and "connection_test" in stdout
        
        # 测试GPU信息
        gpu_test_result = None
        if connection_success:
            gpu_exit_code, gpu_stdout, gpu_stderr = ssh_manager.execute_command(
                server_config, "nvidia-smi --list-gpus", 10
            )
            gpu_test_result = {
                "success": gpu_exit_code == 0,
                "output": gpu_stdout.strip() if gpu_stdout else "",
                "error": gpu_stderr.strip() if gpu_stderr else ""
            }
        
        # 测试模型路径
        path_test_result = None
        if connection_success:
            path_exit_code, path_stdout, path_stderr = ssh_manager.execute_command(
                server_config, f"ls -la {server_config.model_path}", 10
            )
            path_test_result = {
                "success": path_exit_code == 0,
                "output": path_stdout.strip() if path_stdout else "",
                "error": path_stderr.strip() if path_stderr else ""
            }
        
        return {
            "success": True,
            "data": {
                "server_name": server_name,
                "connection_test": {
                    "success": connection_success,
                    "exit_code": exit_code,
                    "stdout": stdout.strip() if stdout else "",
                    "stderr": stderr.strip() if stderr else ""
                },
                "gpu_test": gpu_test_result,
                "model_path_test": path_test_result
            },
            "message": f"服务器'{server_name}'连接测试{'成功' if connection_success else '失败'}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试服务器连接失败: {str(e)}")

@router.get("/monitoring", summary="获取监控配置")
async def get_monitoring_config() -> Dict[str, Any]:
    """获取监控相关配置"""
    try:
        config = get_config()
        monitoring = config.monitoring
        
        return {
            "success": True,
            "data": {
                "gpu": {
                    "interval": monitoring.gpu_interval,
                    "history_retention": monitoring.gpu_history_retention,
                    "push_interval": monitoring.gpu_push_interval
                },
                "system": {
                    "interval": monitoring.system_interval,
                    "history_retention": monitoring.system_history_retention,
                    "push_interval": monitoring.system_push_interval
                },
                "token": {
                    "interval": monitoring.token_interval,
                    "history_retention": monitoring.token_history_retention,
                    "push_interval": monitoring.token_push_interval
                },
                "max_error_count": monitoring.max_error_count
            },
            "message": "监控配置获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取监控配置失败: {str(e)}")

@router.get("/vllm", summary="获取VLLM配置")
async def get_vllm_config() -> Dict[str, Any]:
    """获取VLLM相关配置"""
    try:
        config = get_config()
        vllm = config.vllm
        
        return {
            "success": True,
            "data": {
                "default_port_range": {
                    "start": vllm.default_port_range.start,
                    "end": vllm.default_port_range.end
                },
                "default_gpu_memory_utilization": vllm.default_gpu_memory_utilization,
                "default_max_model_len": vllm.default_max_model_len
            },
            "message": "VLLM配置获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取VLLM配置失败: {str(e)}")

@router.get("/model-storage", summary="获取模型存储配置")
async def get_model_storage_config() -> Dict[str, Any]:
    """获取模型存储相关配置"""
    try:
        config = get_config()
        storage = config.model_storage
        
        return {
            "success": True,
            "data": {
                "base_path": storage.base_path,
                "max_storage_gb": storage.max_storage_gb
            },
            "message": "模型存储配置获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型存储配置失败: {str(e)}")

@router.get("/all", summary="获取所有配置")
async def get_all_config() -> Dict[str, Any]:
    """获取系统的所有配置信息"""
    try:
        config = get_config()
        
        return {
            "success": True,
            "data": {
                "server": {
                    "host": config.server_host,
                    "port": config.server_port,
                    "workers": config.server_workers
                },
                "database": {
                    "url": config.database_url,
                    "echo": config.database_echo
                },
                "gpu_servers_count": len(config.gpu_servers),
                "monitoring": {
                    "gpu_interval": config.monitoring.gpu_interval,
                    "system_interval": config.monitoring.system_interval,
                    "token_interval": config.monitoring.token_interval
                },
                "vllm": {
                    "port_range_start": config.vllm.default_port_range.start,
                    "port_range_end": config.vllm.default_port_range.end,
                    "gpu_memory_utilization": config.vllm.default_gpu_memory_utilization
                },
                "model_storage": {
                    "base_path": config.model_storage.base_path,
                    "max_storage_gb": config.model_storage.max_storage_gb
                }
            },
            "message": "系统配置获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统配置失败: {str(e)}") 