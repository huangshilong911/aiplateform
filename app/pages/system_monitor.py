"""系统资源监控页面"""

from fastapi.responses import HTMLResponse

def system_monitor_page():
    """系统资源监控页面（页面0）"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI平台管理系统 - 系统资源监控</title>
        <link rel="stylesheet" href="/static/css/system_monitor.css">
    </head>
    <body>
        <!-- 顶部导航栏 -->
        <div class="header">
            <div class="header-content">
            <h1>🚀 AI平台管理系统</h1>
                <div class="nav-buttons">
                    <button class="nav-btn active" onclick="showPage(0)">📊 系统监控</button>
                    <button class="nav-btn" onclick="showPage(1)">🎛️ 控制台</button>
                    <button class="nav-btn" onclick="showPage(2)">🔧 开发工具</button>
                </div>
            </div>
        </div>
        
        <!-- 页面内容 -->
        <div class="container">
            <div class="page-title">
                <h2>系统资源监控</h2>
                <p>实时监控所有服务器的资源使用情况</p>
            </div>
            
            <!-- 控制面板 -->
            <div class="controls-section">
            <div class="auto-refresh">
                <label>
                        <input type="checkbox" id="autoRefresh" checked> 自动刷新（3秒）
                </label>
                </div>
                <button class="refresh-btn" onclick="refreshData()">🔄 立即刷新</button>
                </div>
                
            <!-- 系统指标汇总 -->
            <div class="system-metrics-section">
                <div class="section-title">
                    <span>📊</span>
                    系统指标汇总
                </div>
                <div id="system-metrics" class="system-metrics">
                    <div class="loading">正在加载系统指标数据...</div>
                </div>
            </div>
            
            <!-- Token使用统计 -->
            <div class="token-stats-section">
                <div class="section-title">
                    <span>🎯</span>
                    模型Token使用统计
                </div>
                <div id="token-stats" class="token-stats">
                    <div class="loading">正在加载Token统计数据...</div>
                </div>
            </div>
                
            <!-- 服务器详情 -->
            <div class="servers-section">
                <div class="section-title">
                    <span>🖥️</span>
                    服务器资源详情
                </div>
                <div id="system-servers">
                    <div class="loading">正在加载服务器数据...</div>
                </div>
            </div>
                </div>
        <script src="/static/js/system_monitor.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content) 