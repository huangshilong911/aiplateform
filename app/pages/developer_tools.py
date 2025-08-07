"""开发者与管理员工具页面"""

from fastapi.responses import HTMLResponse

def developer_tools_page():
    """开发者与管理员工具页面（页面2）"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI平台管理系统 - 开发者工具</title>
        <link rel="stylesheet" href="/static/css/developer_tools.css">
    </head>
    <body>
        <!-- 顶部导航栏 -->
        <div class="header">
            <div class="header-content">
                <h1>🚀 AI平台管理系统</h1>
                <div class="nav-buttons">
                    <button class="nav-btn" onclick="showPage(0)">📊 系统监控</button>
                    <button class="nav-btn" onclick="showPage(1)">🎛️ 控制台</button>
                    <button class="nav-btn active" onclick="showPage(2)">🔧 开发工具</button>
                </div>
            </div>
        </div>
        
        <!-- 页面内容 -->
        <div class="container">
            <div class="page-title">
                <h2>开发者 & 管理员工具</h2>
                <p>系统底层控制、API文档、状态监控与故障排查工具</p>
            </div>
            
            <!-- 开发者工具区域 -->
            <div class="tools-section">
                <div class="section-title">
                    <span>🛠️</span>
                    工具集合
                </div>
                
                <div class="tools-grid">
                    <!-- API文档工具 -->
                    <div class="tool-category">
                        <h4>📚 API文档与调试</h4>
                        <div class="tool-links">
                            <a href="/docs" target="_blank" class="tool-link">
                                <span class="tool-icon">📖</span>
                                <div class="tool-info">
                                    <div class="tool-name">Swagger文档</div>
                                    <div class="tool-desc">交互式API文档，支持在线测试所有接口</div>
                                </div>
                                <span class="tool-status status-online">可用</span>
                            </a>
                            <a href="/redoc" target="_blank" class="tool-link">
                                <span class="tool-icon">📑</span>
                                <div class="tool-info">
                                    <div class="tool-name">ReDoc文档</div>
                                    <div class="tool-desc">详细API参考手册，完整的接口说明</div>
                                </div>
                                <span class="tool-status status-online">可用</span>
                            </a>
                        </div>
                    </div>
                    
                    <!-- 原始数据API -->
                    <div class="tool-category">
                        <h4>🔍 原始数据访问</h4>
                        <div class="tool-links">
                            <a href="/api/gpu/current" target="_blank" class="tool-link">
                                <span class="tool-icon">🖥️</span>
                                <div class="tool-info">
                                    <div class="tool-name">GPU状态API</div>
                                    <div class="tool-desc">实时GPU使用率、内存、温度等原始数据</div>
                                </div>
                                <span class="tool-status status-checking" id="gpu-status">检查中</span>
                            </a>
                            <a href="/api/system/current" target="_blank" class="tool-link">
                                <span class="tool-icon">📊</span>
                                <div class="tool-info">
                                    <div class="tool-name">系统状态API</div>
                                    <div class="tool-desc">服务器CPU、内存、磁盘等资源数据</div>
                                </div>
                                <span class="tool-status status-checking" id="system-status">检查中</span>
                            </a>
                            <a href="/api/models/" target="_blank" class="tool-link">
                                <span class="tool-icon">🤖</span>
                                <div class="tool-info">
                                    <div class="tool-name">模型列表API</div>
                                    <div class="tool-desc">所有大模型服务的详细信息和状态</div>
                                </div>
                                <span class="tool-status status-checking" id="models-status">检查中</span>
                            </a>
                            <a href="/api/dashboard" target="_blank" class="tool-link">
                                <span class="tool-icon">📈</span>
                                <div class="tool-info">
                                    <div class="tool-name">仪表板API</div>
                                    <div class="tool-desc">综合数据接口，包含GPU、系统、模型摘要</div>
                                </div>
                                <span class="tool-status status-checking" id="dashboard-status">检查中</span>
                            </a>
                        </div>
                    </div>
                    
                    <!-- 系统管理工具 -->
                    <div class="tool-category">
                        <h4>⚙️ 系统管理控制</h4>
                        <div class="tool-links">
                            <a href="/health" target="_blank" class="tool-link">
                                <span class="tool-icon">❤️</span>
                                <div class="tool-info">
                                    <div class="tool-name">健康检查</div>
                                    <div class="tool-desc">系统整体健康状态、服务运行情况</div>
                                </div>
                                <span class="tool-status status-checking" id="health-status">检查中</span>
                            </a>
                            <a href="/terminal" target="_blank" class="tool-link">
                                <span class="tool-icon">🔐</span>
                                <div class="tool-info">
                                    <div class="tool-name">独立SSH终端</div>
                                    <div class="tool-desc">专用SSH终端窗口，更大显示区域</div>
                                </div>
                                <span class="tool-status status-online">可用</span>
                            </a>
                        </div>
                    </div>
                    
                    <!-- 配置管理 -->
                    <div class="tool-category">
                        <h4>⚙️ 配置管理API</h4>
                        <div class="tool-links">
                            <a href="/api/config/servers" target="_blank" class="tool-link">
                                <span class="tool-icon">🌐</span>
                                <div class="tool-info">
                                    <div class="tool-name">服务器配置</div>
                                    <div class="tool-desc">查看和管理GPU服务器配置信息</div>
                                </div>
                                <span class="tool-status status-checking" id="config-status">检查中</span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 快速状态检查 -->
            <div class="quick-status-section">
                <div class="section-title">
                    <span>⚡</span>
                    系统状态实时监控
                    <button class="refresh-btn" onclick="refreshStatus()">🔄 刷新状态</button>
                </div>
                
                <div class="status-grid" id="statusGrid">
                    <div class="status-card">
                        <div class="status-header">
                            <div class="status-label">🏥 系统健康</div>
                            <div class="status-value loading" id="health-indicator">检查中...</div>
                        </div>
                        <div class="status-details" id="health-details">正在检查系统整体健康状态...</div>
                    </div>
                    
                    <div class="status-card">
                        <div class="status-header">
                            <div class="status-label">⚡ API响应</div>
                            <div class="status-value loading" id="api-indicator">检查中...</div>
                        </div>
                        <div class="status-details" id="api-details">正在测试API响应时间...</div>
                    </div>
                    
                    <div class="status-card">
                        <div class="status-header">
                            <div class="status-label">🌐 服务器连接</div>
                            <div class="status-value loading" id="server-indicator">检查中...</div>
                        </div>
                        <div class="status-details" id="server-details">正在检查GPU服务器连接状态...</div>
                    </div>
                    
                    <div class="status-card">
                        <div class="status-header">
                            <div class="status-label">🖥️ GPU监控</div>
                            <div class="status-value loading" id="gpu-indicator">检查中...</div>
                        </div>
                        <div class="status-details" id="gpu-details">正在检查GPU监控服务状态...</div>
                    </div>
                    
                    <div class="status-card">
                        <div class="status-header">
                            <div class="status-label">🤖 模型服务</div>
                            <div class="status-value loading" id="model-indicator">检查中...</div>
                        </div>
                        <div class="status-details" id="model-details">正在检查模型管理服务状态...</div>
                    </div>
                    
                    <div class="status-card">
                        <div class="status-header">
                            <div class="status-label">🗄️ 数据库</div>
                            <div class="status-value loading" id="db-indicator">检查中...</div>
                        </div>
                        <div class="status-details" id="db-details">正在检查数据库连接状态...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="/static/js/developer_tools.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content) 