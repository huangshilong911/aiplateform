"""系统监控API路由"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query

from ..services.system_monitor import SystemMonitorService
from ..services.gpu_monitor import GpuMonitorService
from ..config import AiPlatformConfig

router = APIRouter(prefix="/api/system", tags=["系统监控"])

_system_monitor_service: Optional[SystemMonitorService] = None
_gpu_monitor_service: Optional[GpuMonitorService] = None

def init_system_router(config: AiPlatformConfig):
    """初始化系统路由"""
    global _system_monitor_service, _gpu_monitor_service
    _system_monitor_service = SystemMonitorService(config)
    _gpu_monitor_service = GpuMonitorService(config)

def get_system_service() -> SystemMonitorService:
    """获取系统监控服务实例"""
    if _system_monitor_service is None:
        raise HTTPException(status_code=500, detail="系统监控服务未初始化")
    return _system_monitor_service

def get_gpu_service() -> GpuMonitorService:
    """获取GPU监控服务实例"""
    if _gpu_monitor_service is None:
        raise HTTPException(status_code=500, detail="GPU监控服务未初始化")
    return _gpu_monitor_service

@router.get("/current", summary="获取当前系统资源状态")
async def get_current_system_resources() -> Dict[str, Any]:
    """获取所有服务器的当前系统资源状态"""
    try:
        system_service = get_system_service()
        gpu_service = get_gpu_service()
        
        # 获取系统资源
        system_resources = system_service.get_current_system_resources()
        # 获取GPU资源
        gpu_resources = gpu_service.get_current_gpu_resources()
        
        # 整合数据：为每个服务器添加GPU信息
        enhanced_resources = []
        for system_resource in system_resources:
            server_name = system_resource.get('server_name')
            
            # 获取该服务器的GPU信息
            server_gpus = [gpu for gpu in gpu_resources if gpu.get('server_name') == server_name]
            
            # 计算GPU汇总信息
            gpu_summary = {
                'total_gpus': len(server_gpus),
                'available_gpus': len([gpu for gpu in server_gpus if gpu.get('status') == 'AVAILABLE']),
                'busy_gpus': len([gpu for gpu in server_gpus if gpu.get('status') == 'BUSY']),
                'avg_gpu_utilization': 0,
                'avg_memory_utilization': 0,
                'total_gpu_memory': 0,
                'used_gpu_memory': 0,
                'max_temperature': 0,
                'total_power_draw': 0
            }
            
            if server_gpus:
                valid_gpu_utils = [gpu.get('utilization_gpu', 0) for gpu in server_gpus if gpu.get('utilization_gpu') is not None]
                valid_mem_utils = [gpu.get('utilization_memory', 0) for gpu in server_gpus if gpu.get('utilization_memory') is not None]
                
                gpu_summary.update({
                    'avg_gpu_utilization': sum(valid_gpu_utils) / len(valid_gpu_utils) if valid_gpu_utils else 0,
                    'avg_memory_utilization': sum(valid_mem_utils) / len(valid_mem_utils) if valid_mem_utils else 0,
                    'total_gpu_memory': sum([gpu.get('memory_total', 0) or 0 for gpu in server_gpus]),
                    'used_gpu_memory': sum([gpu.get('memory_used', 0) or 0 for gpu in server_gpus]),
                    'max_temperature': max([gpu.get('temperature', 0) or 0 for gpu in server_gpus], default=0),
                    'total_power_draw': sum([gpu.get('power_draw', 0) or 0 for gpu in server_gpus])
                })
            
            # 检测服务器状态（基于数据有效性和更新时间）
            from datetime import datetime, timedelta
            last_update = system_resource.get('updated_at')
            cpu_usage = system_resource.get('cpu_usage')
            memory_percent = system_resource.get('memory_percent')
            
            if last_update:
                if isinstance(last_update, str):
                    from datetime import datetime
                    try:
                        last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                    except:
                        last_update = datetime.now()
                
                # 检查数据有效性：CPU或内存数据不为空，且最近5分钟内有更新
                time_diff = datetime.now() - last_update.replace(tzinfo=None)
                has_valid_data = (cpu_usage is not None) or (memory_percent is not None)
                is_recent = time_diff.total_seconds() < 300
                
                # 只有在有有效数据且时间最近的情况下才认为在线
                server_status = 'online' if (has_valid_data and is_recent) else 'offline'
            else:
                server_status = 'offline'
            
            # 将GPU信息添加到系统资源中
            enhanced_resource = {**system_resource}
            enhanced_resource['gpu_summary'] = gpu_summary
            enhanced_resource['gpu_details'] = server_gpus
            enhanced_resource['server_status'] = server_status
            
            enhanced_resources.append(enhanced_resource)
        
        return {
            "success": True,
            "data": enhanced_resources,
            "message": f"获取到{len(enhanced_resources)}个服务器的系统资源"
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