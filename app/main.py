"""AI平台管理系统主应用"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from .config import AiPlatformConfig
from .database import init_database, get_database_manager
from .api import gpu, models, system, ssh, config as config_api
from .services.gpu_monitor import GpuMonitorService
from .services.system_monitor import SystemMonitorService
from .services.model_service import ModelServiceManager

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

# 挂载静态文件
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """主页"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI平台管理系统</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .feature-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #007bff;
            }
            .feature-card h3 {
                color: #007bff;
                margin-top: 0;
            }
            .api-links {
                text-align: center;
                margin-top: 30px;
            }
            .api-links a {
                display: inline-block;
                margin: 0 10px;
                padding: 10px 20px;
                background: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background-color 0.3s;
            }
            .api-links a:hover {
                background: #0056b3;
            }
            .status {
                background: #e7f3ff;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                border-left: 4px solid #17a2b8;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 AI平台管理系统</h1>
            
            <div class="status">
                <strong>系统状态：</strong> 运行中 ✅
                <br>
                <strong>版本：</strong> v1.0.0
                <br>
                <strong>构建时间：</strong> Python FastAPI
            </div>
            
            <div class="features">
                <div class="feature-card">
                    <h3>🖥️ GPU监控</h3>
                    <p>实时监控GPU服务器的使用率、内存、温度等关键指标，支持历史数据查询和趋势分析。</p>
                </div>
                
                <div class="feature-card">
                    <h3>🤖 模型管理</h3>
                    <p>管理大模型服务的启动、停止、配置，支持自动发现服务器上的模型文件。</p>
                </div>
                
                <div class="feature-card">
                    <h3>📊 系统监控</h3>
                    <p>监控服务器的CPU、内存、磁盘、网络等系统资源使用情况。</p>
                </div>
                
                <div class="feature-card">
                    <h3>🔐 SSH管理</h3>
                    <p>提供安全的远程SSH连接功能，支持在线终端和命令执行。</p>
                </div>
                
                <div class="feature-card">
                    <h3>⚙️ 配置管理</h3>
                    <p>动态管理GPU服务器配置，支持添加、修改、删除服务器连接信息。</p>
                </div>
                
                <div class="feature-card">
                    <h3>📈 实时数据</h3>
                    <p>通过WebSocket提供实时数据推送，确保监控数据的及时性。</p>
                </div>
            </div>
            
            <div class="api-links">
                <a href="/docs" target="_blank">📚 API文档</a>
                <a href="/redoc" target="_blank">📖 ReDoc文档</a>
                <a href="/api/gpu/current" target="_blank">🖥️ GPU状态</a>
                <a href="/api/models/" target="_blank">🤖 模型列表</a>
                <a href="/api/system/current" target="_blank">📊 系统状态</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

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