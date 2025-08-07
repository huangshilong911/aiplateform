"""AI平台管理系统主应用"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

# 全局禁用Pydantic受保护命名空间警告
import warnings
warnings.filterwarnings("ignore", message=".*Field.*has conflict with protected namespace.*")

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from .config import AiPlatformConfig
from .database import init_database, get_database_manager
from .api import gpu, models, system, ssh, config as config_api, vllm_management
from .services.gpu_monitor import GpuMonitorService
from .services.system_monitor import SystemMonitorService
from .services.model_service import ModelServiceManager
from .services.websocket_terminal import get_terminal_manager
from .pages import system_monitor_page, dashboard_page, developer_tools_page, terminal_page, vllm_management_page

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 全局变量
app_config: AiPlatformConfig = None
gpu_monitor: GpuMonitorService = None
system_monitor: SystemMonitorService = None
model_manager: ModelServiceManager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("正在启动AI平台管理系统...")
    
    try:
        # 初始化配置
        global app_config, gpu_monitor, system_monitor, model_manager
        app_config = AiPlatformConfig()
        
        # 初始化数据库
        db_manager = init_database(app_config)
        db_manager.create_tables()
        logger.info("数据库初始化完成")
        
        # 初始化服务
        gpu_monitor = GpuMonitorService(app_config)
        system_monitor = SystemMonitorService(app_config)
        model_manager = ModelServiceManager(app_config)
        
        # 初始化API路由
        gpu.init_gpu_router(app_config)
        models.init_models_router(app_config)
        system.init_system_router(app_config)
        ssh.init_ssh_router(app_config)
        config_api.init_config_router(app_config)
        vllm_management.init_vllm_router(app_config)
        
        # 启动监控服务
        gpu_monitor.start_monitoring()
        system_monitor.start_monitoring()
        logger.info("监控服务已启动")
        
        logger.info("AI平台管理系统启动完成")
        
        yield
        
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
        raise
    
    finally:
        # 关闭时清理
        logger.info("正在关闭AI平台管理系统...")
        
        if gpu_monitor:
            gpu_monitor.stop_monitoring()
        if system_monitor:
            system_monitor.stop_monitoring()
            
        logger.info("AI平台管理系统已关闭")

# 创建FastAPI应用
app = FastAPI(
    title="AI平台管理系统",
    description="GPU服务器监控和大模型服务管理平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(gpu.router)
app.include_router(models.router)
app.include_router(system.router)
app.include_router(ssh.router)
app.include_router(config_api.router)
app.include_router(vllm_management.router)

# 挂载静态文件
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# WebSocket路由
@app.websocket("/ws/terminal/{server_name}")
async def websocket_terminal(websocket: WebSocket, server_name: str):
    """WebSocket SSH终端连接"""
    try:
        # 查找服务器配置
        server_config = None
        for server in app_config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
        
        if not server_config:
            await websocket.close(code=4000, reason="服务器不存在")
            return
        
        if not server_config.enabled:
            await websocket.close(code=4001, reason="服务器未启用")
            return
        
        # 生成终端ID
        import uuid
        terminal_id = f"{server_name}_{uuid.uuid4().hex[:8]}"
        
        # 处理WebSocket连接
        terminal_manager = get_terminal_manager()
        await terminal_manager.handle_websocket_connection(
            websocket, server_config, terminal_id
        )
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket终端连接断开: {server_name}")
    except Exception as e:
        logger.error(f"WebSocket终端连接错误: {e}")
        try:
            await websocket.close(code=4002, reason=f"连接错误: {str(e)}")
        except:
            pass

# 页面路由
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """系统监控页面"""
    return system_monitor_page()

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """控制台页面"""
    return dashboard_page()

@app.get("/developer", response_class=HTMLResponse)
async def developer_tools():
    """开发者与管理员工具页面（页面2）"""
    return developer_tools_page()

@app.get("/terminal", response_class=HTMLResponse)
async def terminal_page_route():
    """Web SSH终端页面"""
    return terminal_page()

@app.get("/vllm", response_class=HTMLResponse)
async def vllm_management_page_route():
    """VLLM模型服务管理页面"""
    return vllm_management_page()

@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 检查数据库连接
        db_status = "ok"
        try:
            db_manager = get_database_manager()
            with db_manager.get_session():
                pass
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # 检查服务状态
        services_status = {
            "gpu_monitor": "running" if gpu_monitor and gpu_monitor._monitoring else "stopped",
            "system_monitor": "running" if system_monitor and system_monitor._monitoring else "stopped",
            "model_manager": "ok" if model_manager else "not_initialized"
        }
        
        # 检查配置
        config_status = "ok" if app_config else "not_loaded"
        
        return {
            "status": "healthy",
            "timestamp": str(asyncio.get_event_loop().time()),
            "database": db_status,
            "services": services_status,
            "config": config_status,
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

@app.get("/api/dashboard")
async def get_dashboard_data():
    """获取仪表板数据"""
    try:
        dashboard_data = {}
        
        # GPU摘要
        if gpu_monitor:
            dashboard_data["gpu"] = gpu_monitor.get_gpu_summary()
        else:
            dashboard_data["gpu"] = {"error": "GPU监控未启动"}
        
        # 系统资源摘要
        if system_monitor:
            system_resources = system_monitor.get_current_system_resources()
            dashboard_data["system"] = {
                "servers_count": len(system_resources),
                "resources": system_resources
            }
        else:
            dashboard_data["system"] = {"error": "系统监控未启动"}
        
        # 模型服务摘要
        if model_manager:
            all_models = model_manager.get_all_models()
            running_models = [m for m in all_models if m.get('status') == 'RUNNING']
            dashboard_data["models"] = {
                "total": len(all_models),
                "running": len(running_models),
                "stopped": len(all_models) - len(running_models)
            }
        else:
            dashboard_data["models"] = {"error": "模型管理器未初始化"}
        
        return {
            "success": True,
            "data": dashboard_data,
            "message": "仪表板数据获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板数据失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # 读取配置
    config = AiPlatformConfig()
    
    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host=config.server_host,
        port=config.server_port,
        workers=1,  # 由于使用了全局状态，只能单进程
        reload=False,
        log_level="info"
    )