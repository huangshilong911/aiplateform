"""综合管理仪表板页面"""

from fastapi.responses import HTMLResponse

def dashboard_page():
    """综合管理仪表板"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI平台管理系统 - 控制仪表板</title>
        <link rel="stylesheet" href="/static/css/dashboard.css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css" />
        <style>
            /* 覆盖导航样式以保持页面一致性 */
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                min-height: 100vh !important;
                color: #333 !important;
                overflow-x: hidden !important;
            }
            
            .top-header {
                background: rgba(255, 255, 255, 0.95) !important;
                backdrop-filter: blur(10px) !important;
                padding: 20px 0 !important;
                box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1) !important;
                position: sticky !important;
                top: 0 !important;
                z-index: 100 !important;
                border-radius: 0 !important;
                margin-bottom: 0 !important;
                border: none !important;
            }
            
            .header-content {
                max-width: 1400px !important;
                margin: 0 auto !important;
                padding: 0 20px !important;
                display: flex !important;
                justify-content: space-between !important;
                align-items: center !important;
            }
            
            .top-header h1 {
                font-size: 28px !important;
                color: #333 !important;
                font-weight: 600 !important;
                margin-bottom: 0 !important;
                text-align: left !important;
            }
            
            .nav-buttons {
                display: flex !important;
                gap: 15px !important;
            }
            
            .nav-btn {
                background: linear-gradient(45deg, #667eea, #764ba2) !important;
                color: white !important;
                padding: 12px 24px !important;
                border: none !important;
                border-radius: 25px !important;
                cursor: pointer !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                text-decoration: none !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
            }
            
            .nav-btn:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
            }
            
            .nav-btn.active {
                background: linear-gradient(45deg, #ff6b6b, #ee5a24) !important;
            }
            
            .dashboard-container {
                max-width: 1400px !important;
                margin: 0 auto !important;
                padding: 20px !important;
            }
            
            /* 页面标题样式已在外部CSS文件中定义，这里保留基本覆盖 */
            .page-title-section {
                text-align: center !important;
                margin: 30px 0 40px !important;
            }
            
            .page-title-section h2 {
                font-size: 36px !important;
                margin-bottom: 10px !important;
            }
            
            .page-title-section p {
                font-size: 18px !important;
                opacity: 0.95 !important;
            }
        </style>
    </head>
    <body>
        <!-- 顶部导航栏 -->
        <div class="top-header">
            <div class="header-content">
                <h1>🚀 AI平台管理系统</h1>
                <div class="nav-buttons">
                    <button class="nav-btn" onclick="showPage(0)">📊 系统监控</button>
                    <button class="nav-btn active" onclick="showPage(1)">🎛️ 控制台</button>
                    <button class="nav-btn" onclick="showPage(2)">🔧 开发工具</button>
                </div>
            </div>
        </div>
        
        <div class="dashboard-container">
            <!-- 页面标题 -->
            <div class="page-title-section">
                <h2>AI平台管理控制台</h2>
                <p>GPU服务器监控 | 大模型服务管理 | 远程控制中心</p>
            </div>

            <!-- 主要内容网格 -->
            <div class="main-grid">
                <!-- GPU监控面板 -->
                <div class="panel gpu-panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            🖥️ GPU服务器监控
                        </div>
                        <button id="refresh-gpu" class="btn btn-primary btn-sm">刷新</button>
                    </div>
                    <div class="panel-content">
                        <div id="gpu-grid" class="gpu-grid">
                            <div class="loading"></div>
                        </div>
                    </div>
                </div>

                <!-- 模型管理面板 -->
                <div class="panel models-panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            🤖 大模型服务管理
                        </div>
                        <div style="display: flex; gap: 10px;">
                            <button id="refresh-models" class="btn btn-primary btn-sm">刷新</button>
                            <a href="/vllm" class="btn btn-success btn-sm" style="text-decoration: none;">
                                🚀 VLLM管理
                            </a>
                        </div>
                    </div>
                    <div class="panel-content">
                        <div class="models-status-summary" style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span>📊 模型服务状态概览</span>
                                <div id="models-summary" style="font-size: 14px; color: #666;">
                                    加载中...
                                </div>
                            </div>
                        </div>
                        <div id="models-list" class="models-list">
                            <div class="loading"></div>
                        </div>
                    </div>
                </div>

                <!-- 系统监控面板 -->
                <div class="panel system-panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            📊 系统资源监控
                        </div>
                        <button id="refresh-system" class="btn btn-primary btn-sm">刷新</button>
                    </div>
                    <div class="panel-content">
                        <div id="system-metrics" class="system-metrics">
                            <div class="loading"></div>
                        </div>
                        <div class="token-stats-section">
                            <h4>🎯 模型Token使用统计</h4>
                            <div id="token-stats" class="token-stats">
                                <div class="loading"></div>
                            </div>
                        </div>
                        <div class="system-servers">
                            <h4>服务器详细状态</h4>
                            <div id="system-servers">
                                <div class="loading"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- SSH远程终端面板 -->
                <div class="panel ssh-panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            🔐 SSH远程终端
                        </div>
                        <div class="ssh-terminal-controls">
                            <select id="ssh-server-select" class="ssh-server-select">
                                <option value="">选择服务器...</option>
                            </select>
                            <button id="ssh-connect-btn" class="btn btn-success btn-sm">连接</button>
                            <button id="ssh-disconnect-btn" class="btn btn-danger btn-sm" disabled>断开</button>
                            <button id="ssh-clear-btn" class="btn btn-primary btn-sm">清屏</button>
                            <a href="/terminal" class="btn btn-primary btn-sm" target="_blank">独立窗口</a>
                        </div>
                    </div>
                    <div class="panel-content">
                        <div id="ssh-status" class="ssh-status">未连接</div>
                        <div id="ssh-web-terminal" class="ssh-web-terminal">
                            <div class="terminal-placeholder">
                                请选择服务器并点击连接以启动终端...
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 配置管理面板 -->
                <div class="panel config-panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            ⚙️ 服务器配置管理
                        </div>
                        <button id="refresh-config" class="btn btn-primary btn-sm">刷新</button>
                    </div>
                    <div class="panel-content">
                        <div class="config-sections">
                            <!-- 服务器列表 -->
                            <div class="config-section">
                                <div class="config-section-title">GPU服务器列表</div>
                                <button id="add-server" class="btn btn-success" style="margin-bottom: 15px;">添加服务器</button>
                                <div id="server-config-list" class="server-config-list">
                                    <div class="loading"></div>
                                </div>
                            </div>

                            <!-- 添加/编辑服务器表单 -->
                            <div class="config-section">
                                <div class="config-section-title">服务器配置</div>
                                <form id="server-config-form">
                                    <div class="form-group">
                                        <label class="form-label">服务器名称</label>
                                        <input type="text" id="server-name" class="form-control" placeholder="例: GPU-Server-1">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">主机地址</label>
                                        <input type="text" id="server-host" class="form-control" placeholder="例: 192.168.1.100">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">SSH端口</label>
                                        <input type="number" id="server-port" class="form-control" value="22">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">用户名</label>
                                        <input type="text" id="server-username" class="form-control" placeholder="SSH用户名">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">密码</label>
                                        <input type="password" id="server-password" class="form-control" placeholder="SSH密码">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">GPU数量</label>
                                        <input type="number" id="server-gpu-count" class="form-control" value="1" min="1" max="16">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">模型路径</label>
                                        <input type="text" id="server-model-path" class="form-control" placeholder="例: /home/models">
                                    </div>
                                    <div class="form-group">
                                        <button type="button" id="test-server-connection" class="btn btn-primary">测试连接</button>
                                        <button type="button" id="save-server-config" class="btn btn-success">保存配置</button>
                                        <button type="button" id="cancel-server-config" class="btn btn-danger">取消</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"></script>
        <script src="/static/js/dashboard.js"></script>
        <script>
            // 页面切换功能
            function showPage(pageNum) {
                if (pageNum === 0) {
                    // 跳转到系统监控页面
                    window.location.href = '/';
                } else if (pageNum === 1) {
                    // 当前就是控制台页面，不需要切换
                    return;
                } else if (pageNum === 2) {
                    // 跳转到开发者工具页面
                    window.location.href = '/developer';
                }
                
                // 更新导航按钮状态
                const buttons = document.querySelectorAll('.nav-btn');
                buttons.forEach((btn, index) => {
                    if (index === pageNum) {
                        btn.classList.add('active');
                    } else {
                        btn.classList.remove('active');
                    }
                });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)