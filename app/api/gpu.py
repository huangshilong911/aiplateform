"""GPU监控API路由"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta

from ..services.gpu_monitor import GpuMonitorService
from ..config import AiPlatformConfig

router = APIRouter(prefix="/api/gpu", tags=["GPU监控"])

# 全局服务实例
_gpu_monitor_service: Optional[GpuMonitorService] = None

def init_gpu_router(config: AiPlatformConfig):
    """初始化GPU路由"""
    global _gpu_monitor_service
    _gpu_monitor_service = GpuMonitorService(config)

def get_gpu_service() -> GpuMonitorService:
    """获取GPU监控服务实例"""
    if _gpu_monitor_service is None:
        raise HTTPException(status_code=500, detail="GPU监控服务未初始化")
    return _gpu_monitor_service

@router.get("/current", summary="获取当前GPU资源状态")
async def get_current_gpu_resources() -> Dict[str, Any]:
    """获取所有服务器的当前GPU资源状态"""
    try:
        service = get_gpu_service()
        resources = service.get_current_gpu_resources()
        
        return {
            "success": True,
            "data": resources,
            "message": f"获取到{len(resources)}个GPU资源"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取GPU资源失败: {str(e)}")

@router.get("/servers/{server_name}", summary="获取指定服务器的GPU资源")
async def get_gpu_resources_by_server(server_name: str) -> Dict[str, Any]:
    """获取指定服务器的GPU资源状态"""
    try:
        service = get_gpu_service()
        resources = service.get_gpu_resources_by_server(server_name)
        
        if not resources:
            raise HTTPException(status_code=404, detail=f"未找到服务器'{server_name}'的GPU资源")
        
        return {
            "success": True,
            "data": resources,
            "message": f"获取到服务器'{server_name}'的{len(resources)}个GPU资源"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取GPU资源失败: {str(e)}")

@router.get("/history/{server_name}/{gpu_index}", summary="获取GPU历史数据")
async def get_gpu_history(
    server_name: str,
    gpu_index: int,
    hours: int = Query(default=1, description="历史数据时长（小时）", ge=1, le=24)
) -> Dict[str, Any]:
    """获取指定GPU的历史监控数据"""
    try:
        service = get_gpu_service()
        history = service.get_gpu_history(server_name, gpu_index, hours)
        
        return {
            "success": True,
            "data": {
                "server_name": server_name,
                "gpu_index": gpu_index,
                "hours": hours,
                "history": history
            },
            "message": f"获取到{len(history)}条历史记录"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取GPU历史数据失败: {str(e)}")

@router.get("/summary", summary="获取GPU资源摘要")
async def get_gpu_summary() -> Dict[str, Any]:
    """获取所有GPU资源的摘要统计信息"""
    try:
        service = get_gpu_service()
        summary = service.get_gpu_summary()
        
        return {
            "success": True,
            "data": summary,
            "message": "GPU摘要信息获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取GPU摘要失败: {str(e)}")

@router.post("/start-monitoring", summary="启动GPU监控")
async def start_gpu_monitoring() -> Dict[str, Any]:
    """启动GPU监控服务"""
    try:
        service = get_gpu_service()
        service.start_monitoring()
        
        return {
            "success": True,
            "data": None,
            "message": "GPU监控服务已启动"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动GPU监控失败: {str(e)}")

@router.post("/stop-monitoring", summary="停止GPU监控")
async def stop_gpu_monitoring() -> Dict[str, Any]:
    """停止GPU监控服务"""
    try:
        service = get_gpu_service()
        service.stop_monitoring()
        
        return {
            "success": True,
            "data": None,
            "message": "GPU监控服务已停止"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止GPU监控失败: {str(e)}")

@router.get("/servers", summary="获取GPU服务器列表")
async def get_gpu_servers() -> Dict[str, Any]:
    """获取配置的GPU服务器列表"""
    try:
        service = get_gpu_service()
        servers = []
        
        for server_config in service.config.gpu_servers:
            servers.append({
                "name": server_config.name,
                "host": server_config.host,
                "port": server_config.port,
                "gpu_count": server_config.gpu_count,
                "enabled": server_config.enabled,
                "model_path": server_config.model_path
            })
        
        return {
            "success": True,
            "data": servers,
            "message": f"获取到{len(servers)}个GPU服务器"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取GPU服务器列表失败: {str(e)}")

@router.get("/utilization", summary="获取GPU利用率统计")
async def get_gpu_utilization_stats() -> Dict[str, Any]:
    """获取GPU利用率统计信息"""
    try:
        service = get_gpu_service()
        resources = service.get_current_gpu_resources()
        
        # 按服务器分组统计
        server_stats = {}
        total_stats = {
            "total_gpus": 0,
            "avg_gpu_utilization": 0,
            "avg_memory_utilization": 0,
            "busy_gpus": 0,
            "available_gpus": 0
        }
        
        for resource in resources:
            server_name = resource['server_name']
            if server_name not in server_stats:
                server_stats[server_name] = {
                    "gpu_count": 0,
                    "avg_gpu_utilization": 0,
                    "avg_memory_utilization": 0,
                    "busy_gpus": 0,
                    "available_gpus": 0
                }
            
            server_stats[server_name]["gpu_count"] += 1
            total_stats["total_gpus"] += 1
            
            gpu_util = resource.get('utilization_gpu', 0) or 0
            mem_util = resource.get('utilization_memory', 0) or 0
            
            server_stats[server_name]["avg_gpu_utilization"] += gpu_util
            server_stats[server_name]["avg_memory_utilization"] += mem_util
            total_stats["avg_gpu_utilization"] += gpu_util
            total_stats["avg_memory_utilization"] += mem_util
            
            if resource.get('status') == 'BUSY':
                server_stats[server_name]["busy_gpus"] += 1
                total_stats["busy_gpus"] += 1
            elif resource.get('status') == 'AVAILABLE':
                server_stats[server_name]["available_gpus"] += 1
                total_stats["available_gpus"] += 1
        
        # 计算平均值
        for server_name, stats in server_stats.items():
            if stats["gpu_count"] > 0:
                stats["avg_gpu_utilization"] = round(stats["avg_gpu_utilization"] / stats["gpu_count"], 2)
                stats["avg_memory_utilization"] = round(stats["avg_memory_utilization"] / stats["gpu_count"], 2)
        
        if total_stats["total_gpus"] > 0:
            total_stats["avg_gpu_utilization"] = round(total_stats["avg_gpu_utilization"] / total_stats["total_gpus"], 2)
            total_stats["avg_memory_utilization"] = round(total_stats["avg_memory_utilization"] / total_stats["total_gpus"], 2)
        
        return {
            "success": True,
            "data": {
                "total": total_stats,
                "by_server": server_stats
            },
            "message": "GPU利用率统计获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取GPU利用率统计失败: {str(e)}") 