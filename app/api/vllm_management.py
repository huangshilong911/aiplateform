"""VLLM模型服务管理API路由"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import traceback
import time

from ..services.model_service import ModelServiceManager
from ..config import AiPlatformConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vllm", tags=["VLLM管理"])

# 全局变量
app_config: Optional[AiPlatformConfig] = None
model_service: Optional[ModelServiceManager] = None

# 环境总数缓存
_env_count_cache = {}
_cache_expiry_time = 300  # 缓存5分钟

def init_vllm_router(config: AiPlatformConfig):
    """初始化VLLM路由"""
    global app_config, model_service
    app_config = config
    model_service = ModelServiceManager(config)
    logger.info("✅ VLLM管理路由初始化完成")

def create_success_response(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
    """创建成功响应"""
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

def create_error_response(message: str, error_code: str = "UNKNOWN_ERROR") -> Dict[str, Any]:
    """创建错误响应"""
    return {
        "success": False,
        "data": None,
        "message": message,
        "error_code": error_code,
        "timestamp": datetime.now().isoformat()
    }

def validate_dependencies():
    """验证依赖是否已初始化"""
    if not app_config:
        raise HTTPException(status_code=500, detail="配置未初始化")
    if not model_service:
        raise HTTPException(status_code=500, detail="模型服务未初始化")

@router.get("/servers", summary="获取服务器列表")
async def get_servers() -> Dict[str, Any]:
    """获取可用的GPU服务器列表"""
    try:
        logger.info("🔄 开始获取服务器列表")
        validate_dependencies()
        
        logger.info(f"GPU服务器配置数量: {len(app_config.gpu_servers)}")
        
        servers = []
        for i, server in enumerate(app_config.gpu_servers):
            logger.info(f"  处理服务器 {i+1}: {server.name} ({server.host}) - 启用: {server.enabled}")
            if server.enabled:  # 只包含启用的服务器
                servers.append({
                    "name": server.name,
                    "host": server.host,
                    "port": server.port,
                    "gpu_count": server.gpu_count,
                    "model_path": getattr(server, 'model_path', ''),
                    "enabled": server.enabled
                })
        
        logger.info(f"✅ 返回 {len(servers)} 个可用服务器")
        return create_success_response(
            data=servers,
            message=f"获取到 {len(servers)} 个可用服务器"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取服务器列表失败: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"获取服务器列表失败: {str(e)}", "SERVER_LIST_ERROR")
        )

@router.get("/diagnose/{server_name}", summary="诊断服务器VLLM环境")
async def diagnose_environment(server_name: str) -> Dict[str, Any]:
    """诊断指定服务器的VLLM运行环境"""
    try:
        logger.info(f"🔍 开始诊断服务器环境: {server_name}")
        validate_dependencies()
        
        # 验证服务器名称
        server_config = None
        for server in app_config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
        
        if not server_config:
            return create_error_response(f"未找到服务器配置: {server_name}", "SERVER_NOT_FOUND")
        
        diagnosis = model_service.diagnose_server_environment(server_name)
        
        return create_success_response(
            data=diagnosis,
            message="环境诊断完成"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 环境诊断失败 {server_name}: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"环境诊断失败: {str(e)}", "DIAGNOSIS_ERROR")
        )

@router.get("/models/{server_name}", summary="发现服务器上的模型")
async def discover_models(server_name: str) -> Dict[str, Any]:
    """发现指定服务器上的可用模型"""
    try:
        logger.info(f"🔎 开始发现模型: {server_name}")
        validate_dependencies()
        
        models = model_service.discover_models(server_name)
        
        return create_success_response(
            data={
                "discovered_models": models,
                "count": len(models),
                "server_name": server_name
            },
            message=f"发现 {len(models)} 个模型"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 模型发现失败 {server_name}: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"模型发现失败: {str(e)}", "MODEL_DISCOVERY_ERROR")
        )

@router.get("/running/{server_name}", summary="获取运行中的VLLM服务")
async def get_running_services(server_name: str) -> Dict[str, Any]:
    """获取指定服务器上运行中的VLLM服务"""
    try:
        logger.info(f"📊 开始获取运行服务: {server_name}")
        validate_dependencies()
        
        services_info = model_service.get_running_vllm_services(server_name)
        
        return create_success_response(
            data=services_info,
            message=f"获取到 {len(services_info.get('services', []))} 个运行中的服务"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取运行服务失败 {server_name}: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"获取运行服务失败: {str(e)}", "RUNNING_SERVICES_ERROR")
        )

@router.get("/logs/{server_name}/{port}", summary="获取服务日志")
async def get_service_logs(
    server_name: str,
    port: int,
    lines: int = 100
) -> Dict[str, Any]:
    """获取指定端口服务的日志"""
    try:
        logger.info(f"📝 开始获取服务日志: {server_name}:{port}")
        validate_dependencies()
        
        # 验证端口范围
        if port < 1000 or port > 65535:
            return create_error_response("端口号应在1000-65535之间", "INVALID_PORT")
        
        logs_info = model_service.get_service_logs(server_name, port, lines)
        
        return create_success_response(
            data=logs_info,
            message=f"获取日志成功 ({lines} 行)"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取日志失败 {server_name}:{port}: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"获取日志失败: {str(e)}", "LOGS_ERROR")
        )

@router.get("/conda-envs/{server_name}", summary="获取Conda环境列表")
async def get_conda_environments(server_name: str) -> Dict[str, Any]:
    """获取指定服务器上的Conda环境列表"""
    try:
        logger.info(f"🐍 开始获取Conda环境: {server_name}")
        validate_dependencies()
        
        # 验证服务器名称
        server_config = None
        for server in app_config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
        
        if not server_config:
            return create_error_response(f"未找到服务器配置: {server_name}", "SERVER_NOT_FOUND")
        
        ssh_manager = model_service.ssh_manager
        
        # 首先检查conda是否可用
        conda_check_cmd = "which conda || where conda"
        check_exit_code, check_result, check_error = ssh_manager.execute_command(server_config, conda_check_cmd)
        
        envs = []
        
        # 如果当前用户找不到conda，尝试使用sudo命令或检查常见路径
        if check_exit_code != 0 or not check_result.strip():
            logger.info(f"当前用户未找到conda，尝试其他方法查找")
            # 尝试常见的conda安装路径
            common_paths = [
                "/root/anaconda3/bin/conda",
                "/root/miniconda3/bin/conda", 
                "/opt/anaconda3/bin/conda",
                "/opt/miniconda3/bin/conda",
                "/usr/local/anaconda3/bin/conda",
                "/usr/local/miniconda3/bin/conda"
            ]
            
            for conda_path in common_paths:
                check_cmd = f"test -f {conda_path} && echo {conda_path}"
                check_exit_code, check_result, check_error = ssh_manager.execute_command(server_config, check_cmd)
                if check_exit_code == 0 and check_result.strip():
                    logger.info(f"在路径 {conda_path} 找到conda")
                    break
            
            # 如果还是找不到，尝试sudo which conda（如果用户有sudo权限且无需密码）
            if check_exit_code != 0 or not check_result.strip():
                sudo_check_cmd = "sudo -n which conda 2>/dev/null"
                check_exit_code, check_result, check_error = ssh_manager.execute_command(server_config, sudo_check_cmd)
        
        if check_exit_code == 0 and check_result.strip():
            # conda可用，尝试获取环境列表
            conda_path = check_result.strip()
            
            # 如果找到的是完整路径，直接使用；否则使用conda命令
            if conda_path.startswith('/'):
                conda_cmd = f"{conda_path} env list --json"
            else:
                conda_cmd = "conda env list --json"
            
            exit_code, result, error = ssh_manager.execute_command(server_config, conda_cmd)
            
            # 如果JSON格式失败，尝试使用info命令
            if exit_code != 0:
                if conda_path.startswith('/'):
                    conda_cmd = f"{conda_path} info --envs"
                else:
                    conda_cmd = "conda info --envs"
                exit_code, result, error = ssh_manager.execute_command(server_config, conda_cmd)
                
                # 如果还是失败，尝试sudo（如果之前是通过sudo找到的）
                if exit_code != 0 and not conda_path.startswith('/'):
                    conda_cmd = "sudo -n conda info --envs 2>/dev/null"
                    exit_code, result, error = ssh_manager.execute_command(server_config, conda_cmd)
                
                if exit_code == 0 and result:
                    # 解析文本格式的conda info输出
                    lines = result.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#') and '*' not in line and line != '':
                            parts = line.split()
                            if len(parts) >= 1:
                                env_name = parts[0]
                                is_default = env_name == 'base'
                                envs.append({
                                    "name": env_name,
                                    "is_default": is_default
                                })
            else:
                # 解析JSON格式的conda env list输出
                import json
                try:
                    conda_data = json.loads(result)
                    for env_path in conda_data.get('envs', []):
                        env_name = env_path.split('/')[-1] if '/' in env_path else env_path.split('\\')[-1]
                        is_default = env_name == 'base' or 'base' in env_path
                        envs.append({
                            "name": env_name,
                            "path": env_path,
                            "is_default": is_default
                        })
                except json.JSONDecodeError:
                    logger.warning(f"解析Conda环境JSON失败: {result}")
        
        # 如果没有找到conda环境或conda不可用，提供默认的Python环境选项
        if not envs:
            logger.warning(f"服务器 {server_name} 上未找到conda或conda环境，提供默认Python环境")
            envs = [
                {"name": "vllm-builtin", "is_default": True, "description": "内置vLLM环境 (Python 3.10 + vLLM)"},
                {"name": "system-python", "is_default": False, "description": "系统默认Python环境"},
                {"name": "python3", "is_default": False, "description": "Python3环境"}
            ]
        else:
            # 即使有conda环境，也添加内置vLLM环境作为备选
            has_builtin = any(env['name'] == 'vllm-builtin' for env in envs)
            if not has_builtin:
                envs.append({"name": "vllm-builtin", "is_default": False, "description": "内置vLLM环境 (Python 3.10 + vLLM)"})
        
        # 确保至少有一个默认环境
        if not any(env.get('is_default', False) for env in envs):
            if envs:
                envs[0]['is_default'] = True
            else:
                envs.append({"name": "system-python", "is_default": True, "description": "系统默认Python环境"})
        
        # 缓存环境总数
        current_time = time.time()
        _env_count_cache[server_name] = {
            'count': len(envs),
            'timestamp': current_time
        }
        logger.info(f"📊 缓存环境总数: {server_name} -> {len(envs)} 个环境")
        
        return create_success_response(
            data=envs,
            message=f"获取到 {len(envs)} 个Conda环境"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取Conda环境失败 {server_name}: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"获取Conda环境失败: {str(e)}", "CONDA_ENVS_ERROR")
        )

@router.post("/start", summary="启动VLLM服务")
async def start_vllm_service(
    server_name: str = Body(..., description="服务器名称"),
    conda_env: str = Body(..., description="Conda虚拟环境"),
    model_path: str = Body(..., description="模型路径"),
    port: int = Body(..., description="服务端口"),
    gpu_indices: str = Body("", description="GPU索引"),
    max_model_len: int = Body(4096, description="最大模型长度"),
    gpu_memory_utilization: float = Body(0.9, description="GPU内存利用率"),
    tensor_parallel_size: int = Body(1, description="张量并行大小"),
    dtype: str = Body("auto", description="数据类型"),
    quantization: Optional[str] = Body(None, description="量化方式"),
    trust_remote_code: bool = Body(False, description="是否信任远程代码"),
    worker_use_ray: int = Body(0, description="Ray工作进程数")
) -> Dict[str, Any]:
    """启动VLLM服务"""
    try:
        logger.info(f"🚀 开始启动VLLM服务: {server_name}:{port}")
        validate_dependencies()
        
        # 参数验证
        if not conda_env.strip():
            return create_error_response("Conda虚拟环境不能为空", "INVALID_CONDA_ENV")
            
        if not model_path.strip():
            return create_error_response("模型路径不能为空", "INVALID_MODEL_PATH")
        
        if port < 1000 or port > 65535:
            return create_error_response("端口号应在1000-65535之间", "INVALID_PORT")
        
        if tensor_parallel_size < 1 or tensor_parallel_size > 8:
            return create_error_response("张量并行大小应在1-8之间", "INVALID_TENSOR_PARALLEL")
        
        if gpu_memory_utilization < 0.1 or gpu_memory_utilization > 1.0:
            return create_error_response("GPU内存利用率应在0.1-1.0之间", "INVALID_GPU_MEMORY_UTIL")
        
        # 组织高级参数
        extra_params = {
            "conda_env": conda_env.strip(),
            "dtype": dtype,
            "quantization": quantization if quantization else None,
            "trust_remote_code": trust_remote_code,
            "worker_use_ray": worker_use_ray
        }
        
        # 检查是否需要激活conda环境和持久化会话
        if conda_env.strip() not in ['system-python', 'python3', 'vllm-builtin']:
            logger.info(f"🐍 检查Conda环境和持久化会话: {conda_env}")
            
            # 获取服务器配置
            server_config = None
            for server in app_config.gpu_servers:
                if server.name == server_name:
                    server_config = server
                    break
            
            if not server_config:
                return create_error_response(f"服务器 {server_name} 未找到", "SERVER_NOT_FOUND")
            
            # 检查是否存在对应的持久化会话（按服务器名称检查）
            session_status = model_service.ssh_manager.get_session_status(server_name)
            
            if session_status and session_status.get('is_alive', False):
                # 检查会话中是否已激活了环境
                activated_env = session_status.get('activated_env')
                if activated_env:
                    # 提取环境名称（处理完整路径格式）
                    activated_env_name = activated_env.split('/')[-1] if '/' in activated_env else activated_env
                    target_env_name = conda_env.strip()
                    
                    # 如果目标环境是base，但已激活了其他有效环境（如vllm），则使用已激活的环境
                    if target_env_name == 'base' and activated_env_name != 'base' and activated_env_name:
                        logger.info(f"✅ 发现活跃的持久化会话，已激活环境: {activated_env}，将使用此环境启动服务（而非base环境）")
                        # 更新conda_env为实际激活的环境，确保后续逻辑使用正确的环境
                        conda_env = activated_env_name
                    elif activated_env_name == target_env_name or activated_env.endswith(f"/{target_env_name}"):
                        logger.info(f"✅ 发现活跃的持久化会话，且已激活正确环境: {activated_env}，将在会话中启动服务")
                    else:
                        logger.info(f"⚠️ 发现持久化会话但环境不匹配（当前: {activated_env}，需要: {target_env_name}），尝试激活正确环境")
                        # 激活正确的环境
                        activation_result = await activate_conda_environment(server_name, target_env_name)
                        if not activation_result.get('success', False):
                            logger.error(f"❌ 激活Conda环境失败: {activation_result.get('message', '未知错误')}")
                            return create_error_response(f"激活Conda环境失败: {activation_result.get('message', '未知错误')}", "CONDA_ACTIVATION_FAILED")
                else:
                    logger.info(f"⚠️ 发现持久化会话但未检测到激活的环境，尝试激活Conda环境")
                    # 激活环境
                    activation_result = await activate_conda_environment(server_name, conda_env.strip())
                    if not activation_result.get('success', False):
                        logger.error(f"❌ 激活Conda环境失败: {activation_result.get('message', '未知错误')}")
                        return create_error_response(f"激活Conda环境失败: {activation_result.get('message', '未知错误')}", "CONDA_ACTIVATION_FAILED")
            else:
                logger.info(f"⚠️ 未发现活跃的持久化会话，尝试激活Conda环境")
                
                # 激活环境（这会创建持久化会话）
                activation_result = await activate_conda_environment(
                    server_name=server_name,
                    env_name=conda_env.strip(),
                    use_sudo=False,
                    sudo_password=""
                )
                
                if not activation_result.get("success", False):
                    return create_error_response(
                        f"激活Conda环境失败: {activation_result.get('message', '未知错误')}",
                        "CONDA_ACTIVATION_FAILED"
                    )
                
                logger.info(f"✅ Conda环境激活成功，已创建持久化会话: {conda_env}")
        
        # 先将临时配置添加到数据库
        temp_model_data = {
            "name": f"临时模型-{port}",
            "model_path": model_path.strip(),
            "server_name": server_name,
            "gpu_indices": gpu_indices.strip(),
            "max_model_len": max_model_len,
            "gpu_memory_utilization": gpu_memory_utilization,
            "tensor_parallel_size": tensor_parallel_size,
            "extra_params": extra_params
        }
        
        # 添加模型到数据库
        model = model_service.add_model(temp_model_data)
        if not model:
            return create_error_response("创建模型配置失败", "CREATE_MODEL_FAILED")
        
        try:
            # 启动服务（model_service会自动检测和使用持久化会话）
            success, message = model_service.start_model(model["id"])
            
            if not success:
                # 启动失败，删除刚创建的模型配置
                model_service.delete_model(model["id"])
                return create_error_response(f"启动服务失败: {message}", "START_SERVICE_FAILED")
            
            # 获取更新后的模型信息
            updated_model = model_service.get_model_by_id(model["id"])
            
            result = {
                "model_id": model["id"],
                "pid": updated_model.get("pid") if updated_model else None,
                "port": port,
                "message": message
            }
            
        except Exception as e:
            # 发生异常，删除刚创建的模型配置
            try:
                model_service.delete_model(model["id"])
            except:
                pass
            raise e
        
        return create_success_response(
            data={
                "server_name": server_name,
                "conda_env": conda_env,
                "model_path": model_path,
                "port": port,
                "pid": result.get("pid"),
                "model_id": result.get("model_id"),
                "message": result.get("message"),
                "config": {
                    "conda_env": conda_env,
                    "tensor_parallel_size": tensor_parallel_size,
                    "max_model_len": max_model_len,
                    "gpu_memory_utilization": gpu_memory_utilization,
                    "dtype": dtype
                }
            },
            message="VLLM服务启动成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 启动VLLM服务失败: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"启动VLLM服务失败: {str(e)}", "START_SERVICE_ERROR")
        )

@router.post("/stop", summary="停止VLLM服务")
async def stop_vllm_service(
    server_name: str = Body(..., description="服务器名称"),
    pid: Optional[int] = Body(None, description="进程ID"),
    port: Optional[int] = Body(None, description="端口号")
) -> Dict[str, Any]:
    """停止VLLM服务"""
    try:
        logger.info(f"⏹️ 开始停止VLLM服务: {server_name}")
        validate_dependencies()
        
        if not pid and not port:
            return create_error_response("必须提供PID或端口号", "MISSING_IDENTIFIER")
        
        # 获取服务器配置
        server_config = None
        for server in app_config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
        
        if not server_config:
            return create_error_response(f"服务器 {server_name} 未找到", "SERVER_NOT_FOUND")
        
        success = False
        stopped_pid = None
        
        if pid:
            # 通过PID停止
            success = model_service._stop_service_by_pid(server_config, pid)
            stopped_pid = pid
        else:
            # 通过端口停止
            success, stopped_pid = model_service._stop_service_by_port(server_config, port)
        
        if success:
            return create_success_response(
                data={
                    "server_name": server_name,
                    "stopped_pid": stopped_pid,
                    "method": "pid" if pid else "port",
                    "identifier": pid if pid else port
                },
                message=f"服务停止成功 (PID: {stopped_pid})"
            )
        else:
            return create_error_response("服务停止失败，可能进程已经停止", "STOP_FAILED")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 停止VLLM服务失败: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"停止VLLM服务失败: {str(e)}", "STOP_SERVICE_ERROR")
        )

@router.get("/performance/{server_name}", summary="获取性能监控信息")
async def get_performance_metrics(server_name: str) -> Dict[str, Any]:
    """获取服务器性能指标"""
    try:
        logger.info(f"📈 开始获取性能数据: {server_name}")
        validate_dependencies()
        
        server_config = None
        for server in app_config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
                
        if not server_config:
            return create_error_response(f"服务器 {server_name} 不存在", "SERVER_NOT_FOUND")
        
        ssh_manager = model_service.ssh_manager
        
        # 获取GPU使用情况
        gpu_cmd = "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits"
        gpu_exit_code, gpu_result, gpu_error = ssh_manager.execute_command(server_config, gpu_cmd)
        
        # 获取系统负载
        load_cmd = "cat /proc/loadavg"
        load_exit_code, load_result, load_error = ssh_manager.execute_command(server_config, load_cmd)
        
        # 获取内存使用情况
        mem_cmd = "free -m | grep Mem:"
        mem_exit_code, mem_result, mem_error = ssh_manager.execute_command(server_config, mem_cmd)
        
        # 解析GPU信息
        gpu_metrics = []
        if gpu_exit_code == 0 and gpu_result and gpu_result.strip():
            for i, line in enumerate(gpu_result.strip().split('\n')):
                try:
                    parts = line.split(', ')
                    if len(parts) >= 4:
                        gpu_metrics.append({
                            "gpu_id": i,
                            "utilization": int(float(parts[0])),
                            "memory_used": int(float(parts[1])),
                            "memory_total": int(float(parts[2])),
                            "temperature": int(float(parts[3]))
                        })
                except (ValueError, IndexError) as e:
                    logger.warning(f"解析GPU数据失败: {line}, 错误: {e}")
        
        # 解析系统负载
        load_avg = [0.0, 0.0, 0.0]
        if load_exit_code == 0 and load_result:
            try:
                load_parts = load_result.strip().split()
                if len(load_parts) >= 3:
                    load_avg = [float(load_parts[0]), float(load_parts[1]), float(load_parts[2])]
            except (ValueError, IndexError) as e:
                logger.warning(f"解析负载数据失败: {load_result}, 错误: {e}")
        
        # 解析内存使用
        memory_info = {"used": 0, "total": 0, "available": 0}
        if mem_exit_code == 0 and mem_result:
            try:
                mem_parts = mem_result.strip().split()
                if len(mem_parts) >= 7:
                    memory_info = {
                        "total": int(mem_parts[1]),
                        "used": int(mem_parts[2]),
                        "available": int(mem_parts[6])
                    }
            except (ValueError, IndexError) as e:
                logger.warning(f"解析内存数据失败: {mem_result}, 错误: {e}")
        
        return create_success_response(
            data={
                "server_name": server_name,
                "gpu_metrics": gpu_metrics,
                "load_average": load_avg,
                "memory": memory_info,
                "timestamp": datetime.now().isoformat()
            },
            message="性能监控数据获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取性能监控失败: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"获取性能监控失败: {str(e)}", "PERFORMANCE_ERROR")
        )

@router.get("/health/{server_name}/{port}", summary="健康检查")
async def health_check(server_name: str, port: int) -> Dict[str, Any]:
    """检查VLLM服务健康状态"""
    try:
        logger.info(f"❤️ 开始健康检查: {server_name}:{port}")
        validate_dependencies()
        
        if port < 1000 or port > 65535:
            return create_error_response("端口号应在1000-65535之间", "INVALID_PORT")
        
        server_config = None
        for server in app_config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
                
        if not server_config:
            return create_error_response(f"服务器 {server_name} 不存在", "SERVER_NOT_FOUND")
        
        # 检查端口是否在使用
        port_in_use = model_service._is_port_in_use(server_config, port)
        
        if not port_in_use:
            return create_success_response(
                data={"status": "停止", "port": port, "healthy": False},
                message="服务未运行"
            )
        
        # 获取进程ID
        pid = model_service._get_service_pid(server_config, port)
        
        # 验证服务是否正常运行
        if pid:
            is_running = model_service._verify_service_running(server_config, pid, port)
            if is_running:
                return create_success_response(
                    data={
                        "status": "健康",
                        "port": port,
                        "pid": pid,
                        "healthy": True,
                        "check_time": datetime.now().isoformat()
                    },
                    message="服务运行正常"
                )
        
        return create_success_response(
            data={"status": "异常", "port": port, "healthy": False},
            message="服务状态异常"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"健康检查失败: {str(e)}", "HEALTH_CHECK_ERROR")
        )

@router.post("/test-connection", summary="测试服务连接")
async def test_service_connection(
    server_name: str = Body(..., description="服务器名称"),
    port: int = Body(..., description="服务端口")
) -> Dict[str, Any]:
    """测试VLLM服务连接"""
    try:
        logger.info(f"🔗 开始连接测试: {server_name}:{port}")
        validate_dependencies()
        
        if port < 1000 or port > 65535:
            return create_error_response("端口号应在1000-65535之间", "INVALID_PORT")
        
        server_config = None
        for server in app_config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
                
        if not server_config:
            return create_error_response(f"服务器 {server_name} 不存在", "SERVER_NOT_FOUND")
        
        # 测试HTTP连接
        test_cmd = f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port}/health --connect-timeout 5 --max-time 10 || echo 'failed'"
        exit_code, result, error = model_service.ssh_manager.execute_command(server_config, test_cmd)
        
        if exit_code == 0 and result and result.strip() == "200":
            return create_success_response(
                data={"status": "连接正常", "response_code": 200, "port": port},
                message="服务连接测试成功"
            )
        elif exit_code == 0 and result and result.strip().isdigit():
            return create_success_response(
                data={"status": "服务响应异常", "response_code": int(result.strip()), "port": port},
                message=f"服务返回HTTP {result.strip()}"
            )
        else:
            error_msg = error if error else (result if result else '无响应')
            return create_error_response(
                f"连接失败: {error_msg}", 
                "CONNECTION_FAILED"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 连接测试失败: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"连接测试失败: {str(e)}", "CONNECTION_TEST_ERROR")
        )

# 保留其他现有的API端点（saved-models等）但进行错误处理增强
@router.get("/saved-models", summary="获取已保存的模型配置")
async def get_saved_models() -> Dict[str, Any]:
    """获取数据库中保存的所有模型配置"""
    try:
        validate_dependencies()
        
        models = model_service.get_all_models()
        
        return create_success_response(
            data=models,
            message=f"获取到 {len(models)} 个已保存的模型配置"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取已保存模型失败: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"获取已保存模型失败: {str(e)}", "SAVED_MODELS_ERROR")
        )

@router.post("/save-model", summary="保存模型配置")
async def save_model_config(
    name: str = Body(..., description="模型名称"),
    model_path: str = Body(..., description="模型路径"),
    server_name: str = Body(..., description="服务器名称"),
    port: Optional[int] = Body(None, description="固定端口"),
    gpu_indices: str = Body("", description="GPU索引"),
    max_model_len: int = Body(4096, description="最大模型长度"),
    gpu_memory_utilization: float = Body(0.9, description="GPU内存利用率"),
    tensor_parallel_size: int = Body(1, description="张量并行大小"),
    dtype: str = Body("auto", description="数据类型"),
    quantization: Optional[str] = Body(None, description="量化方式"),
    trust_remote_code: bool = Body(False, description="是否信任远程代码"),
    worker_use_ray: int = Body(0, description="Ray工作进程数")
) -> Dict[str, Any]:
    """保存模型配置到数据库"""
    try:
        validate_dependencies()
        
        if not name.strip() or not model_path.strip():
            return create_error_response("模型名称和路径不能为空", "INVALID_INPUT")
        
        model_data = {
            "name": name.strip(),
            "model_path": model_path.strip(),
            "server_name": server_name,
            "port": port,
            "gpu_indices": gpu_indices.strip(),
            "max_model_len": max_model_len,
            "gpu_memory_utilization": gpu_memory_utilization,
            "tensor_parallel_size": tensor_parallel_size,
            "extra_params": {
                "dtype": dtype,
                "quantization": quantization,
                "trust_remote_code": trust_remote_code,
                "worker_use_ray": worker_use_ray
            }
        }
        
        result = model_service.add_model(model_data)
        
        if result:
            return create_success_response(
                data=result,
                message="模型配置保存成功"
            )
        else:
            return create_error_response("模型配置保存失败", "SAVE_FAILED")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 保存模型配置失败: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"保存模型配置失败: {str(e)}", "SAVE_MODEL_ERROR")
        )

@router.delete("/models/{model_id}", summary="删除模型配置")
async def delete_model_config(model_id: int) -> Dict[str, Any]:
    """删除模型配置"""
    try:
        validate_dependencies()
        
        if model_id <= 0:
            return create_error_response("无效的模型ID", "INVALID_MODEL_ID")
        
        success, message = model_service.delete_model(model_id)
        
        if success:
            return create_success_response(
                data=None,
                message=message
            )
        else:
            return create_error_response(message, "DELETE_FAILED")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除模型配置失败: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"删除模型配置失败: {str(e)}", "DELETE_MODEL_ERROR")
        )

# Conda环境管理相关API
@router.post("/activate-conda-env", summary="激活Conda环境")
async def activate_conda_environment(
    server_name: str = Body(..., description="服务器名称"),
    env_name: str = Body(..., description="环境名称"),
    use_sudo: bool = Body(False, description="是否使用sudo权限"),
    sudo_password: str = Body("", description="sudo密码")
) -> Dict[str, Any]:
    """激活指定的Conda环境"""
    try:
        logger.info(f"🐍 开始激活Conda环境: {server_name} -> {env_name}")
        validate_dependencies()
        
        # 验证服务器名称
        server_config = None
        for server in app_config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
        
        if not server_config:
            return create_error_response(f"未找到服务器配置: {server_name}", "SERVER_NOT_FOUND")
        
        if not env_name or not env_name.strip():
            return create_error_response("环境名称不能为空", "INVALID_ENV_NAME")
        
        ssh_manager = model_service.ssh_manager
        
        # 构建命令前缀
        if use_sudo and sudo_password:
            logger.info("🔐 使用su权限执行命令")
        
        # 首先检查conda是否可用
        conda_path = None
        
        if use_sudo and sudo_password:
            # su模式下直接尝试常见路径，因为su环境下PATH可能不包含用户的conda
            logger.info("🔍 su模式下直接搜索常见Conda路径")
            common_paths = [
                "/opt/miniconda3/bin/conda",  # 优先搜索这个路径，因为日志显示在这里找到了
                "/opt/anaconda3/bin/conda",
                "/root/anaconda3/bin/conda",
                "/root/miniconda3/bin/conda",
                "/usr/local/anaconda3/bin/conda",
                "/usr/local/miniconda3/bin/conda",
                "/home/anaconda3/bin/conda"
            ]
            
            for path in common_paths:
                # 改用su命令，直接传递密码
                check_cmd = f"echo '{sudo_password}' | su -c 'test -f {path} && echo {path}'"
                logger.info(f"🔍 检查路径: {path}")
                check_exit_code, check_result, check_error = ssh_manager.execute_command(server_config, check_cmd)
                logger.info(f"📋 检查结果 - 退出码: {check_exit_code}, 输出: '{check_result.strip()}', 错误: '{check_error}'")
                if check_exit_code == 0 and check_result.strip():
                    conda_path = check_result.strip()
                    logger.info(f"✅ 在su模式下找到Conda: {conda_path}")
                    break
                else:
                    logger.info(f"❌ 路径 {path} 不存在或无法访问")
        else:
            # 非sudo模式下先尝试which conda
            conda_check_cmd = "which conda || echo 'not_found'"
            exit_code, result, error = ssh_manager.execute_command(server_config, conda_check_cmd)
            
            if "not_found" not in result and result.strip():
                conda_path = "conda"  # 使用系统PATH中的conda
                logger.info("✅ 在PATH中找到Conda")
            else:
                # 尝试常见路径
                logger.info("🔍 在PATH中未找到Conda，尝试常见路径")
                common_paths = [
                    "/home/anaconda3/bin/conda",
                    "/opt/anaconda3/bin/conda",
                    "/opt/miniconda3/bin/conda",
                    "/usr/local/anaconda3/bin/conda",
                    "/usr/local/miniconda3/bin/conda"
                ]
                
                for path in common_paths:
                    check_cmd = f"test -f {path} && echo {path}"
                    check_exit_code, check_result, check_error = ssh_manager.execute_command(server_config, check_cmd)
                    if check_exit_code == 0 and check_result.strip():
                        conda_path = check_result.strip()
                        logger.info(f"✅ 在常见路径中找到Conda: {conda_path}")
                        break
        
        if not conda_path:
            error_msg = "未找到Conda安装，请确保Conda已正确安装"
            if use_sudo:
                error_msg += "。su模式下已搜索常见路径：/root/anaconda3, /root/miniconda3, /opt/anaconda3, /opt/miniconda3 等"
            logger.error(f"❌ {error_msg}")
            return create_error_response(error_msg, "CONDA_NOT_FOUND")
        
        # 获取conda base路径
        if conda_path.startswith('/'):
            # 使用完整路径，从/path/to/conda/bin/conda获取/path/to/conda
            if use_sudo and sudo_password:
                conda_base_cmd = f"echo '{sudo_password}' | su -c 'dirname $(dirname {conda_path})'"
            else:
                conda_base_cmd = f"dirname $(dirname {conda_path})"
        else:
            # 使用系统PATH中的conda
            if use_sudo and sudo_password:
                conda_base_cmd = f"echo '{sudo_password}' | su -c '{conda_path} info --base'"
            else:
                conda_base_cmd = f"{conda_path} info --base"
        
        # 获取conda base路径
        base_exit_code, base_result, base_error = ssh_manager.execute_command(server_config, conda_base_cmd)
        
        if base_exit_code != 0:
            logger.error(f"❌ 无法获取conda base路径: {base_error}")
            return create_error_response(f"无法获取conda base路径: {base_error}", "CONDA_BASE_ERROR")
        
        conda_base = base_result.strip()
        logger.info(f"📍 Conda base路径: {conda_base}")
        
        # 检查环境是否存在
        logger.info(f"🔍 检查环境是否存在: {env_name}")
        if use_sudo and sudo_password:
            # 修改正则表达式以匹配路径格式的环境名，如 /path/to/envs/vllm
            env_check_cmd = f"echo '{sudo_password}' | su -c '{conda_path} env list | grep -E \"/{env_name}$|^{env_name}\\s+\" || echo ENV_NOT_FOUND'"
        else:
            env_check_cmd = f"{conda_path} env list | grep -E '/{env_name}$|^{env_name}\\s+' || echo 'ENV_NOT_FOUND'"
        
        logger.info(f"🔧 环境检查命令: {env_check_cmd}")
        env_exit_code, env_result, env_error = ssh_manager.execute_command(server_config, env_check_cmd)
        logger.info(f"📋 环境检查结果 - 退出码: {env_exit_code}, 输出: '{env_result.strip()}', 错误: '{env_error}'")
        
        # 如果环境检查失败，先列出所有可用环境
        if "ENV_NOT_FOUND" in env_result:
            logger.info(f"❌ 环境 '{env_name}' 未找到，列出所有可用环境:")
            if use_sudo and sudo_password:
                list_envs_cmd = f"echo '{sudo_password}' | su -c '{conda_path} env list'"
            else:
                list_envs_cmd = f"{conda_path} env list"
            
            list_exit_code, list_result, list_error = ssh_manager.execute_command(server_config, list_envs_cmd)
            logger.info(f"📋 可用环境列表:\n{list_result}")
            
            return create_error_response(f"Conda环境 '{env_name}' 不存在。可用环境: {list_result.strip()}", "ENV_NOT_FOUND")
        
        # 从环境检查结果中提取环境路径
        env_path = env_result.strip()
        logger.info(f"🎯 找到环境路径: {env_path}")
        
        # 确定激活目标：如果是完整路径则使用路径，否则使用环境名
        activation_target = env_path if env_path.startswith('/') else env_name
        logger.info(f"🚀 激活目标: {activation_target}")
        
        # 使用持久化会话激活环境
        logger.info(f"🔧 尝试在持久化会话中激活环境: {env_name}")
        
        # 创建或获取持久化会话
        session_id = f"{server_name}_conda_{env_name}"
        session = ssh_manager.get_persistent_session(server_config)
        
        if not session:
            logger.error(f"❌ 无法创建持久化会话")
            return create_error_response("无法创建持久化会话", "SESSION_CREATION_FAILED")
        
        # 检查是否最近已经激活过相同环境
        if hasattr(session, 'is_env_recently_activated') and session.is_env_recently_activated(env_name):
            logger.info(f"🔄 环境 {env_name} 最近已激活，返回成功状态")
            return create_success_response(
                data={
                    "env_name": env_name,
                    "server_name": server_name,
                    "session_id": session_id,
                    "activation_time": datetime.now().isoformat(),
                    "cached": True
                },
                message=f"Conda环境 '{env_name}' 已在持久化会话中激活（缓存状态）"
            )
        
        # 在持久化会话中激活Conda环境
        success = ssh_manager.activate_conda_in_session(
            server_config,
            activation_target,
            conda_path,
            conda_base,
            sudo_password
        )
        
        if success:
            logger.info(f"✅ Conda环境在持久化会话中激活成功: {env_name}")
            return create_success_response(
                data={
                    "env_name": env_name,
                    "server_name": server_name,
                    "session_id": session_id,
                    "activation_time": datetime.now().isoformat(),
                    "cached": False
                },
                message=f"Conda环境 '{env_name}' 在持久化会话中激活成功"
            )
        else:
            logger.error(f"❌ Conda环境在持久化会话中激活失败")
            return create_error_response(
                "在持久化会话中激活环境失败", 
                "ACTIVATION_FAILED"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 激活Conda环境异常: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"激活Conda环境失败: {str(e)}", "CONDA_ACTIVATION_ERROR")
        )

@router.get("/conda-status/{server_name}", summary="获取Conda状态")
async def get_conda_status(server_name: str) -> Dict[str, Any]:
    """获取指定服务器的Conda状态信息"""
    try:
        logger.info(f"📊 开始获取Conda状态: {server_name}")
        validate_dependencies()
        
        # 验证服务器名称
        server_config = None
        for server in app_config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
        
        if not server_config:
            return create_error_response(f"未找到服务器配置: {server_name}", "SERVER_NOT_FOUND")
        
        ssh_manager = model_service.ssh_manager
        status_info = {
            "conda_available": False,
            "conda_version": None,
            "current_env": None,
            "python_version": None,
            "python_path": None,
            "total_envs": 0,
            "session_status": "no_session"  # 添加会话状态信息
        }
        
        # 优先使用持久化会话获取状态
        session = ssh_manager.get_persistent_session(server_config)
        
        if session and session.connected and session.is_alive():
            logger.info(f"📊 使用持久化会话检查Conda状态 (会话ID: {session.session_id})")
            status_info["session_status"] = "persistent_session"
            
            # 在持久化会话中检查conda状态 - 使用更智能的检测方法
            # 首先尝试直接使用conda命令
            # 不再检测conda命令，直接假设conda可用并进行环境检测
            conda_available = True
            logger.info(f"📊 跳过conda命令检测，直接进行环境检测")
            
            if conda_available:
                status_info["conda_available"] = True
                # status_info["conda_version"] = conda_version  # 注释掉版本检测
                
                # 优化的环境检测逻辑 - 优先使用会话状态
                current_env = None
                
                # 首先检查会话的激活状态
                if hasattr(session, 'env_activated') and session.env_activated and session.activated_env:
                    logger.info(f"📊 会话显示已激活环境: {session.activated_env}")
                    # 验证会话状态是否准确
                    if session._verify_current_env(session.activated_env):
                        current_env = session.activated_env.split('/')[-1] if '/' in session.activated_env else session.activated_env
                        logger.info(f"📊 会话状态验证通过，当前环境: {current_env}")
                        status_info["session_status"] = "verified_active"
                    else:
                        logger.info(f"📊 会话状态验证失败，清除无效状态")
                        session.env_activated = False
                        session.activated_env = None
                        status_info["session_status"] = "verification_failed"
                
                # 如果会话状态无效或不存在，使用简化的环境变量检测
                if not current_env:
                    logger.info(f"📊 在持久化会话中进行简化环境检测")
                    # 只检查环境变量，不再使用复杂的检测方法
                    exit_code, result, error = session.execute_in_session("echo $CONDA_DEFAULT_ENV")
                    
                    if exit_code == 0 and result.strip():
                        clean_result = result.strip()
                        if clean_result and clean_result not in ["", "base", "(base)"]:
                            current_env = clean_result
                            logger.info(f"📊 通过环境变量检测到环境: {current_env}")
                            status_info["session_status"] = "env_var_detected"
                        else:
                            logger.info(f"📊 环境变量显示为base或空，无激活环境")
                            status_info["session_status"] = "no_env_detected"
                    else:
                        logger.info(f"📊 无法获取环境变量，无激活环境")
                        status_info["session_status"] = "no_env_detected"
                
                # 设置检测结果
                if current_env:
                    status_info["current_env"] = current_env
                    logger.info(f"📊 最终确定当前激活环境: {current_env}")
                else:
                    logger.info(f"📊 持久化会话中未检测到激活的环境")
                    status_info["session_status"] = "no_env_detected"
                
                # 获取Python信息（在持久化会话中）
                # python_version_cmd = "python --version"  # 注释掉版本检测
                # exit_code, result, error = session.execute_in_session(python_version_cmd)
                # if exit_code == 0:
                #     status_info["python_version"] = result.strip()
                
                python_path_cmd = "which python"
                exit_code, result, error = session.execute_in_session(python_path_cmd)
                if exit_code == 0:
                    status_info["python_path"] = result.strip()
                
                # 获取环境总数（优先使用缓存）
                current_time = time.time()
                cached_data = _env_count_cache.get(server_name)
                
                if cached_data and (current_time - cached_data['timestamp']) < _cache_expiry_time:
                    # 使用缓存的环境总数
                    status_info["total_envs"] = cached_data['count']
                    logger.info(f"📊 使用缓存的环境总数: {status_info['total_envs']} (缓存时间: {int(current_time - cached_data['timestamp'])}秒前)")
                else:
                    # 缓存过期或不存在，重新获取
                    logger.info(f"📊 缓存过期或不存在，重新获取环境总数")
                    env_count_cmd = "conda env list --json"
                    exit_code, result, error = session.execute_in_session(env_count_cmd)
                    logger.info(f"📊 JSON命令执行结果 - 退出码: {exit_code}, 输出长度: {len(result) if result else 0}, 错误: {error}")
                    
                    if exit_code == 0 and result and result.strip():
                        try:
                            import json
                            # 记录原始输出用于调试
                            logger.info(f"📊 尝试解析JSON输出: {result[:200]}..." if len(result) > 200 else f"📊 尝试解析JSON输出: {result}")
                            env_data = json.loads(result)
                            if 'envs' in env_data:
                                env_count = len(env_data['envs'])
                                status_info["total_envs"] = env_count
                                # 更新缓存
                                _env_count_cache[server_name] = {
                                    'count': env_count,
                                    'timestamp': current_time
                                }
                                logger.info(f"📊 通过JSON格式获取并缓存环境总数: {status_info['total_envs']}")
                            else:
                                logger.warning(f"📊 JSON输出中没有'envs'字段，回退到文本解析")
                                # 回退到文本解析方法
                                env_count_cmd_fallback = "conda env list | grep -v '^#' | grep -v '^$' | wc -l"
                                exit_code, result, error = session.execute_in_session(env_count_cmd_fallback)
                                if exit_code == 0 and result.strip().isdigit():
                                    count = int(result.strip())
                                    # 减去标题行
                                    env_count = max(0, count - 1) if count > 0 else 0
                                    status_info["total_envs"] = env_count
                                    # 更新缓存
                                    _env_count_cache[server_name] = {
                                        'count': env_count,
                                        'timestamp': current_time
                                    }
                                    logger.info(f"📊 通过文本解析获取并缓存环境总数: {status_info['total_envs']}")
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.warning(f"📊 JSON解析失败，原因: {e}, 原始输出: '{result[:100]}...' (长度: {len(result)})")
                            # 回退到文本解析方法
                            env_count_cmd_fallback = "conda env list | grep -v '^#' | grep -v '^$' | wc -l"
                            exit_code, result, error = session.execute_in_session(env_count_cmd_fallback)
                            if exit_code == 0 and result.strip().isdigit():
                                count = int(result.strip())
                                # 减去标题行
                                env_count = max(0, count - 1) if count > 0 else 0
                                status_info["total_envs"] = env_count
                                # 更新缓存
                                _env_count_cache[server_name] = {
                                    'count': env_count,
                                    'timestamp': current_time
                                }
                                logger.info(f"📊 通过文本解析获取并缓存环境总数: {status_info['total_envs']}")
                    else:
                        logger.warning(f"📊 JSON命令执行失败或返回空结果，直接使用文本解析")
                        # 直接使用文本解析方法
                        env_count_cmd_fallback = "conda env list | grep -v '^#' | grep -v '^$' | wc -l"
                        exit_code, result, error = session.execute_in_session(env_count_cmd_fallback)
                        if exit_code == 0 and result.strip().isdigit():
                            count = int(result.strip())
                            # 减去标题行
                            env_count = max(0, count - 1) if count > 0 else 0
                            status_info["total_envs"] = env_count
                            # 更新缓存
                            _env_count_cache[server_name] = {
                                'count': env_count,
                                'timestamp': current_time
                            }
                            logger.info(f"📊 通过文本解析获取并缓存环境总数: {status_info['total_envs']}")
                        else:
                            logger.warning(f"📊 获取环境总数失败: 退出码 {exit_code}, 错误: {error}")
                            # 如果有旧缓存，使用旧缓存
                            if cached_data:
                                status_info["total_envs"] = cached_data['count']
                                logger.info(f"📊 获取失败，使用过期缓存: {status_info['total_envs']}")
            else:
                logger.warning(f"📊 持久化会话中conda不可用")
                status_info["session_status"] = "conda_unavailable"
        else:
            logger.info(f"📊 没有可用的持久化会话，使用普通SSH连接检查Conda状态")
            status_info["session_status"] = "fallback_ssh"
            
            # 不再检测conda命令，直接假设conda可用并进行环境检测
            status_info["conda_available"] = True
            logger.info(f"📊 跳过conda命令检测，直接进行环境检测")
            
            # 获取当前激活的环境（使用多种方法检测）
            current_env_methods = [
                "echo $CONDA_DEFAULT_ENV",
                "conda info --envs | grep '*' | awk '{print $1}'",
                "which python | grep -o '/envs/[^/]*' | cut -d'/' -f3"
            ]
            
            current_env = None
            for method in current_env_methods:
                exit_code, result, error = ssh_manager.execute_command(server_config, method)
                if exit_code == 0 and result.strip() and result.strip() not in ["", "base", "(base)"]:
                    current_env = result.strip()
                    logger.info(f"📊 通过方法 '{method}' 检测到当前环境: {current_env}")
                    break
            
            # 如果检测到激活的环境，进一步验证
            if current_env:
                # 验证环境是否真的激活
                verify_cmd = f"conda info | grep 'active environment' | awk '{{print $4}}'"
                exit_code, verify_result, error = ssh_manager.execute_command(server_config, verify_cmd)
                if exit_code == 0 and verify_result.strip():
                    verified_env = verify_result.strip()
                    if verified_env != "base":
                        status_info["current_env"] = verified_env
                        logger.info(f"📊 验证确认当前激活环境: {verified_env}")
                    else:
                        status_info["current_env"] = current_env
                        logger.info(f"📊 使用检测结果作为当前环境: {current_env}")
                else:
                    status_info["current_env"] = current_env
                    logger.info(f"📊 验证失败，使用检测结果: {current_env}")
            else:
                logger.info(f"📊 普通SSH连接中未检测到激活的环境")
            
            # 获取Python信息
            # python_version_cmd = "python --version"  # 注释掉版本检测
            # exit_code, result, error = ssh_manager.execute_command(server_config, python_version_cmd)
            # if exit_code == 0:
            #     status_info["python_version"] = result.strip()
            
            python_path_cmd = "which python"
            exit_code, result, error = ssh_manager.execute_command(server_config, python_path_cmd)
            if exit_code == 0:
                status_info["python_path"] = result.strip()
            
            # 获取环境总数
            # 使用更可靠的方法获取环境总数
            env_count_cmd = "conda env list --json"
            exit_code, result, error = ssh_manager.execute_command(server_config, env_count_cmd)
            if exit_code == 0:
                try:
                    import json
                    env_data = json.loads(result)
                    if 'envs' in env_data:
                        status_info["total_envs"] = len(env_data['envs'])
                        logger.info(f"📊 通过JSON格式获取到环境总数: {status_info['total_envs']}")
                    else:
                        # 回退到文本解析方法
                        env_count_cmd_fallback = "conda env list | grep -v '^#' | grep -v '^$' | wc -l"
                        exit_code, result, error = ssh_manager.execute_command(server_config, env_count_cmd_fallback)
                        if exit_code == 0 and result.strip().isdigit():
                            count = int(result.strip())
                            # 减去标题行
                            status_info["total_envs"] = max(0, count - 1) if count > 0 else 0
                            logger.info(f"📊 通过文本解析获取到环境总数: {status_info['total_envs']}")
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"📊 JSON解析失败，使用文本解析: {e}")
                    # 回退到文本解析方法
                    env_count_cmd_fallback = "conda env list | grep -v '^#' | grep -v '^$' | wc -l"
                    exit_code, result, error = ssh_manager.execute_command(server_config, env_count_cmd_fallback)
                    if exit_code == 0 and result.strip().isdigit():
                        count = int(result.strip())
                        # 减去标题行
                        status_info["total_envs"] = max(0, count - 1) if count > 0 else 0
                        logger.info(f"📊 通过文本解析获取到环境总数: {status_info['total_envs']}")
            else:
                logger.warning(f"📊 获取环境总数失败: 退出码 {exit_code}, 错误: {error}")
        
        return create_success_response(
            data=status_info,
            message="Conda状态获取完成"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取Conda状态失败: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response(f"获取Conda状态失败: {str(e)}", "CONDA_STATUS_ERROR")
        )