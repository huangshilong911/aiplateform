"""模型管理API路由"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from ..services.model_service import ModelServiceManager
from ..config import AiPlatformConfig

router = APIRouter(prefix="/api/models", tags=["模型管理"])

# 全局服务实例
_model_service_manager: Optional[ModelServiceManager] = None

def init_models_router(config: AiPlatformConfig):
    """初始化模型路由"""
    global _model_service_manager
    _model_service_manager = ModelServiceManager(config)

def get_model_service() -> ModelServiceManager:
    """获取模型服务管理器实例"""
    if _model_service_manager is None:
        raise HTTPException(status_code=500, detail="模型服务管理器未初始化")
    return _model_service_manager

class ModelCreateRequest(BaseModel):
    """创建模型请求模型"""
    model_config = {"protected_namespaces": ()}
    
    name: str = Field(..., description="模型名称")
    model_path: str = Field(..., description="模型路径")
    model_type: str = Field(default="LLM", description="模型类型")
    server_name: str = Field(..., description="服务器名称")
    gpu_indices: Optional[str] = Field(default="", description="GPU索引（逗号分隔）")
    max_model_len: Optional[int] = Field(default=4096, description="最大模型长度")
    gpu_memory_utilization: Optional[float] = Field(default=0.9, description="GPU内存利用率")
    tensor_parallel_size: Optional[int] = Field(default=1, description="张量并行大小")
    extra_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外参数")

@router.get("/", summary="获取所有模型")
async def get_all_models() -> Dict[str, Any]:
    """获取所有已配置的模型服务"""
    try:
        service = get_model_service()
        models = service.get_all_models()
        
        return {
            "success": True,
            "data": models,
            "message": f"获取到{len(models)}个模型服务"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

@router.get("/{model_id}", summary="获取模型详情")
async def get_model_by_id(model_id: int) -> Dict[str, Any]:
    """根据ID获取模型服务详情"""
    try:
        service = get_model_service()
        model = service.get_model_by_id(model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"未找到ID为{model_id}的模型服务")
        
        return {
            "success": True,
            "data": model,
            "message": "模型详情获取成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型详情失败: {str(e)}")

@router.get("/running/list", summary="获取运行中的模型")
async def get_running_models() -> Dict[str, Any]:
    """获取所有正在运行的模型服务"""
    try:
        service = get_model_service()
        models = service.get_running_models()
        
        return {
            "success": True,
            "data": models,
            "message": f"当前有{len(models)}个模型正在运行"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取运行中模型失败: {str(e)}")

@router.post("/", summary="添加新模型")
async def add_model(model_data: ModelCreateRequest) -> Dict[str, Any]:
    """添加新的模型服务配置"""
    try:
        service = get_model_service()
        model = service.add_model(model_data.dict())
        
        if not model:
            raise HTTPException(status_code=400, detail="添加模型失败，请检查输入参数")
        
        return {
            "success": True,
            "data": model,
            "message": f"模型'{model_data.name}'添加成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加模型失败: {str(e)}")

@router.post("/{model_id}/start", summary="启动模型服务")
async def start_model(model_id: int) -> Dict[str, Any]:
    """启动指定的模型服务"""
    try:
        service = get_model_service()
        success, message = service.start_model(model_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {
            "success": True,
            "data": {"model_id": model_id},
            "message": message
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动模型服务失败: {str(e)}")

@router.post("/{model_id}/stop", summary="停止模型服务")
async def stop_model(model_id: int) -> Dict[str, Any]:
    """停止指定的模型服务"""
    try:
        service = get_model_service()
        success, message = service.stop_model(model_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {
            "success": True,
            "data": {"model_id": model_id},
            "message": message
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止模型服务失败: {str(e)}")

@router.delete("/{model_id}", summary="删除模型服务")
async def delete_model(model_id: int) -> Dict[str, Any]:
    """删除指定的模型服务配置"""
    try:
        service = get_model_service()
        success, message = service.delete_model(model_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {
            "success": True,
            "data": {"model_id": model_id},
            "message": message
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除模型服务失败: {str(e)}")

@router.get("/discover/{server_name}", summary="发现服务器上的模型")
async def discover_models(server_name: str) -> Dict[str, Any]:
    """自动发现指定服务器上的模型文件"""
    try:
        service = get_model_service()
        models = service.discover_models(server_name)
        
        return {
            "success": True,
            "data": {
                "server_name": server_name,
                "discovered_models": models
            },
            "message": f"在服务器'{server_name}'上发现{len(models)}个模型"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型发现失败: {str(e)}")

@router.post("/update-status", summary="更新模型状态")
async def update_model_status() -> Dict[str, Any]:
    """更新所有模型服务的运行状态"""
    try:
        service = get_model_service()
        service.update_model_status()
        
        return {
            "success": True,
            "data": None,
            "message": "模型状态更新成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新模型状态失败: {str(e)}")

@router.get("/stats/summary", summary="获取模型统计摘要")
async def get_model_stats_summary() -> Dict[str, Any]:
    """获取模型服务的统计摘要信息"""
    try:
        service = get_model_service()
        all_models = service.get_all_models()
        
        stats = {
            "total_models": len(all_models),
            "running_models": len([m for m in all_models if m.get('status') == 'RUNNING']),
            "stopped_models": len([m for m in all_models if m.get('status') == 'STOPPED']),
            "error_models": len([m for m in all_models if m.get('status') == 'ERROR']),
            "starting_models": len([m for m in all_models if m.get('status') == 'STARTING']),
            "stopping_models": len([m for m in all_models if m.get('status') == 'STOPPING'])
        }
        
        # 按服务器分组统计
        by_server = {}
        for model in all_models:
            server_name = model.get('server_name')
            if server_name not in by_server:
                by_server[server_name] = {
                    "total": 0,
                    "running": 0,
                    "stopped": 0,
                    "error": 0
                }
            
            by_server[server_name]["total"] += 1
            status = model.get('status', 'STOPPED')
            if status == 'RUNNING':
                by_server[server_name]["running"] += 1
            elif status == 'STOPPED':
                by_server[server_name]["stopped"] += 1
            elif status == 'ERROR':
                by_server[server_name]["error"] += 1
        
        # 按模型类型分组统计
        by_type = {}
        for model in all_models:
            model_type = model.get('model_type', 'Unknown')
            if model_type not in by_type:
                by_type[model_type] = 0
            by_type[model_type] += 1
        
        return {
            "success": True,
            "data": {
                "overview": stats,
                "by_server": by_server,
                "by_type": by_type
            },
            "message": "模型统计摘要获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型统计失败: {str(e)}")

@router.get("/ports/available/{server_name}", summary="获取可用端口")
async def get_available_ports(server_name: str) -> Dict[str, Any]:
    """获取指定服务器的可用端口列表"""
    try:
        service = get_model_service()
        
        # 获取端口范围
        port_range = service.config.vllm.default_port_range
        available_ports = []
        
        # 获取服务器配置
        server_config = None
        for config in service.config.gpu_servers:
            if config.name == server_name:
                server_config = config
                break
        
        if not server_config:
            raise HTTPException(status_code=404, detail=f"未找到服务器: {server_name}")
        
        # 检查端口可用性
        for port in range(port_range.start, min(port_range.end, port_range.start + 20)):
            if not service._is_port_in_use(server_config, port):
                available_ports.append(port)
        
        return {
            "success": True,
            "data": {
                "server_name": server_name,
                "available_ports": available_ports,
                "port_range": {
                    "start": port_range.start,
                    "end": port_range.end
                }
            },
            "message": f"服务器'{server_name}'有{len(available_ports)}个可用端口"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取可用端口失败: {str(e)}")

@router.get("/stats/tokens", summary="获取模型Token使用统计")
async def get_model_token_stats() -> Dict[str, Any]:
    """获取所有运行中模型的Token使用统计"""
    try:
        service = get_model_service()
        all_models = service.get_all_models()
        
        # 过滤运行中的模型
        running_models = [m for m in all_models if m.get('status') == 'RUNNING']
        
        # 计算总体统计
        total_stats = {
            "total_running_models": len(running_models),
            "total_tokens": sum([m.get('total_tokens', 0) for m in running_models]),
            "total_requests": sum([m.get('total_requests', 0) for m in running_models]),
            "avg_tokens_per_request": 0
        }
        
        # 计算平均token数
        if total_stats["total_requests"] > 0:
            total_stats["avg_tokens_per_request"] = round(
                total_stats["total_tokens"] / total_stats["total_requests"], 2
            )
        
        # 按服务器分组统计
        by_server = {}
        for model in running_models:
            server_name = model.get('server_name')
            if server_name not in by_server:
                by_server[server_name] = {
                    "running_models": 0,
                    "total_tokens": 0,
                    "total_requests": 0,
                    "models": []
                }
            
            by_server[server_name]["running_models"] += 1
            by_server[server_name]["total_tokens"] += model.get('total_tokens', 0)
            by_server[server_name]["total_requests"] += model.get('total_requests', 0)
            by_server[server_name]["models"].append({
                "name": model.get('name'),
                "model_type": model.get('model_type'),
                "total_tokens": model.get('total_tokens', 0),
                "total_requests": model.get('total_requests', 0),
                "port": model.get('port'),
                "start_time": model.get('start_time')
            })
        
        # 按模型类型分组统计
        by_type = {}
        for model in running_models:
            model_type = model.get('model_type', 'Unknown')
            if model_type not in by_type:
                by_type[model_type] = {
                    "model_count": 0,
                    "total_tokens": 0,
                    "total_requests": 0
                }
            
            by_type[model_type]["model_count"] += 1
            by_type[model_type]["total_tokens"] += model.get('total_tokens', 0)
            by_type[model_type]["total_requests"] += model.get('total_requests', 0)
        
        # 最活跃的模型（按token数排序）
        top_models = sorted(
            running_models, 
            key=lambda x: x.get('total_tokens', 0), 
            reverse=True
        )[:5]
        
        top_models_data = []
        for model in top_models:
            top_models_data.append({
                "name": model.get('name'),
                "server_name": model.get('server_name'),
                "model_type": model.get('model_type'),
                "total_tokens": model.get('total_tokens', 0),
                "total_requests": model.get('total_requests', 0),
                "avg_tokens": round(
                    model.get('total_tokens', 0) / max(model.get('total_requests', 1), 1), 2
                )
            })
        
        return {
            "success": True,
            "data": {
                "overview": total_stats,
                "by_server": by_server,
                "by_type": by_type,
                "top_models": top_models_data
            },
            "message": "Token统计获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Token统计失败: {str(e)}")

@router.get("/diagnose/{server_name}", summary="诊断服务器环境")
async def diagnose_server_environment(server_name: str) -> Dict[str, Any]:
    """诊断指定服务器的VLLM运行环境"""
    try:
        service = get_model_service()
        diagnosis = service.diagnose_server_environment(server_name)
        
        return {
            "success": diagnosis.get("success", True),
            "data": diagnosis,
            "message": "环境诊断完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"环境诊断失败: {str(e)}")

@router.get("/running/{server_name}", summary="获取运行中的VLLM服务")
async def get_running_vllm_services(server_name: str) -> Dict[str, Any]:
    """获取指定服务器上运行中的VLLM服务"""
    try:
        service = get_model_service()
        result = service.get_running_vllm_services(server_name)
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "message": f"找到{len(result['services'])}个运行中的VLLM服务"
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取运行中服务失败: {str(e)}")

@router.get("/logs/{server_name}/{port}", summary="获取服务日志")
async def get_service_logs(server_name: str, port: int, lines: int = 100) -> Dict[str, Any]:
    """获取指定服务器和端口的VLLM服务日志"""
    try:
        service = get_model_service()
        result = service.get_service_logs(server_name, port, lines)
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "message": "日志获取成功"
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务日志失败: {str(e)}")

@router.get("/ports/{server_name}", summary="检查端口使用情况")
async def check_port_usage(server_name: str) -> Dict[str, Any]:
    """检查指定服务器的端口使用情况"""
    try:
        service = get_model_service()
        result = service.check_port_usage(server_name)
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "message": "端口检查完成"
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"端口检查失败: {str(e)}")

@router.post("/start-vllm", summary="直接启动VLLM服务")
async def start_vllm_service(
    server_name: str = Body(..., description="服务器名称"),
    model_path: str = Body(..., description="模型路径"),
    port: int = Body(..., description="服务端口"),
    gpu_indices: str = Body("", description="GPU索引"),
    max_model_len: int = Body(4096, description="最大模型长度"),
    gpu_memory_utilization: float = Body(0.9, description="GPU内存利用率"),
    tensor_parallel_size: int = Body(1, description="张量并行大小")
) -> Dict[str, Any]:
    """直接启动VLLM服务，无需预先添加到数据库"""
    try:
        service = get_model_service()
        
        # 创建临时模型配置
        model_config = {
            "name": f"临时模型-{port}",
            "model_path": model_path,
            "server_name": server_name,
            "gpu_indices": gpu_indices,
            "max_model_len": max_model_len,
            "gpu_memory_utilization": gpu_memory_utilization,
            "tensor_parallel_size": tensor_parallel_size,
            "port": port
        }
        
        # 先添加到数据库
        model = service.add_model(model_config)
        if not model:
            raise HTTPException(status_code=400, detail="创建模型配置失败")
        
        # 启动服务
        success, message = service.start_model(model["id"])
        
        if success:
            # 获取更新后的模型信息
            updated_model = service.get_model_by_id(model["id"])
            return {
                "success": True,
                "data": {
                    "model": updated_model,
                    "pid": updated_model.get("pid"),
                    "port": updated_model.get("port")
                },
                "message": message
            }
        else:
            # 启动失败，删除刚创建的模型配置
            service.delete_model(model["id"])
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动VLLM服务失败: {str(e)}")

@router.post("/stop-vllm", summary="直接停止VLLM服务")
async def stop_vllm_service(
    server_name: str = Body(..., description="服务器名称"),
    pid: Optional[int] = Body(None, description="进程ID"),
    port: Optional[int] = Body(None, description="端口号")
) -> Dict[str, Any]:
    """直接停止VLLM服务，支持通过PID或端口号停止"""
    try:
        service = get_model_service()
        
        if not pid and not port:
            raise HTTPException(status_code=400, detail="必须提供PID或端口号")
        
        server_config = None
        for config in service.config.gpu_servers:
            if config.name == server_name:
                server_config = config
                break
        
        if not server_config:
            raise HTTPException(status_code=404, detail=f"未找到服务器: {server_name}")
        
        stopped_pids = []
        
        if pid:
            # 通过PID停止
            success = service._stop_service_by_pid(server_config, pid)
            if success:
                stopped_pids.append(pid)
        
        if port:
            # 通过端口停止
            success, stopped_pid = service._stop_service_by_port(server_config, port)
            if success and stopped_pid:
                stopped_pids.append(stopped_pid)
        
        if stopped_pids:
            # 更新数据库中对应的模型状态
            with service.db_manager.get_session() as session:
                for stop_pid in stopped_pids:
                    models = session.query(ModelService).filter(
                        ModelService.server_name == server_name,
                        ModelService.pid == stop_pid
                    ).all()
                    
                    for model in models:
                        model.status = "STOPPED"
                        model.pid = None
                        model.updated_at = datetime.now()
                
                session.commit()
            
            return {
                "success": True,
                "data": {
                    "stopped_pids": stopped_pids,
                    "server_name": server_name
                },
                "message": f"成功停止{len(stopped_pids)}个服务"
            }
        else:
            raise HTTPException(status_code=400, detail="停止服务失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止VLLM服务失败: {str(e)}")