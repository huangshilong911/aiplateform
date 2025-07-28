"""系统监控API路由"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query

from ..services.system_monitor import SystemMonitorService
from ..config import AiPlatformConfig

router = APIRouter(prefix="/api/system", tags=["系统监控"])

_system_monitor_service: Optional[SystemMonitorService] = None

def init_system_router(config: AiPlatformConfig):
    """初始化系统路由"""
    global _system_monitor_service
    _system_monitor_service = SystemMonitorService(config)

def get_system_service() -> SystemMonitorService:
    """获取系统监控服务实例"""
    if _system_monitor_service is None:
        raise HTTPException(status_code=500, detail="系统监控服务未初始化")
    return _system_monitor_service

@router.get("/current", summary="获取当前系统资源状态")
async def get_current_system_resources() -> Dict[str, Any]:
    """获取所有服务器的当前系统资源状态"""
    try:
        service = get_system_service()
        resources = service.get_current_system_resources()
        
        return {
            "success": True,
            "data": resources,
            "message": f"获取到{len(resources)}个服务器的系统资源"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统资源失败: {str(e)}")

@router.get("/servers/{server_name}", summary="获取指定服务器的系统资源")
async def get_system_resource_by_server(server_name: str) -> Dict[str, Any]:
    """获取指定服务器的系统资源状态"""
    try:
        service = get_system_service()
        resource = service.get_system_resource_by_server(server_name)
        
        if not resource:
            raise HTTPException(status_code=404, detail=f"未找到服务器'{server_name}'的系统资源")
        
        return {
            "success": True,
            "data": resource,
            "message": f"获取服务器'{server_name}'的系统资源成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统资源失败: {str(e)}")

@router.get("/history/{server_name}", summary="获取系统历史数据")
async def get_system_history(
    server_name: str,
    hours: int = Query(default=1, description="历史数据时长（小时）", ge=1, le=24)
) -> Dict[str, Any]:
    """获取指定服务器的系统资源历史数据"""
    try:
        service = get_system_service()
        history = service.get_system_history(server_name, hours)
        
        return {
            "success": True,
            "data": {
                "server_name": server_name,
                "hours": hours,
                "history": history
            },
            "message": f"获取到{len(history)}条历史记录"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统历史数据失败: {str(e)}")

@router.post("/start-monitoring", summary="启动系统监控")
async def start_system_monitoring() -> Dict[str, Any]:
    """启动系统监控服务"""
    try:
        service = get_system_service()
        service.start_monitoring()
        
        return {
            "success": True,
            "data": None,
            "message": "系统监控服务已启动"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动系统监控失败: {str(e)}")

@router.post("/stop-monitoring", summary="停止系统监控")
async def stop_system_monitoring() -> Dict[str, Any]:
    """停止系统监控服务"""
    try:
        service = get_system_service()
        service.stop_monitoring()
        
        return {
            "success": True,
            "data": None,
            "message": "系统监控服务已停止"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止系统监控失败: {str(e)}") 