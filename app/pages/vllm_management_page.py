"""VLLM模型服务管理页面"""

from fastapi.responses import HTMLResponse

def vllm_management_page():
    """VLLM模型服务管理页面"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VLLM模型服务管理 - AI平台管理系统</title>
        <link rel="stylesheet" href="/static/css/dashboard.css">
        <style>
            :root {
                --primary-color: #667eea;
                --secondary-color: #764ba2;
                --success-color: #28a745;
                --warning-color: #ffc107;
                --danger-color: #dc3545;
                --info-color: #007bff;
                --light-bg: rgba(255, 255, 255, 0.95);
                --shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                --border-radius: 12px;
            }

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                min-height: 100vh;
                color: #333;
                line-height: 1.6;
            }
            
            .vllm-header {
                background: var(--light-bg);
                backdrop-filter: blur(10px);
                padding: 20px 0;
                box-shadow: var(--shadow);
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            .header-content {
                max-width: 1400px;
                margin: 0 auto;
                padding: 0 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .header-title {
                font-size: 28px;
                color: #333;
                font-weight: 600;
                margin: 0;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .vllm-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .page-title-section {
                text-align: center;
                margin: 30px 0 40px;
                color: white;
            }
            
            .page-title-section h2 {
                font-size: 36px;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }

            .page-title-section p {
                font-size: 18px;
                opacity: 0.9;
            }
            
            .vllm-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .vllm-panel {
                background: var(--light-bg);
                border-radius: var(--border-radius);
                padding: 20px;
                box-shadow: var(--shadow);
                transition: transform 0.2s ease;
            }

            .vllm-panel:hover {
                transform: translateY(-2px);
            }
            
            .panel-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 2px solid #f0f0f0;
            }
            
            .panel-title {
                font-size: 18px;
                font-weight: 600;
                color: #333;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .content-area {
                min-height: 200px;
                background: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                overflow-y: auto;
                max-height: 400px;
                border: 1px solid #e9ecef;
            }
            
            .loading {
                text-align: center;
                padding: 60px 40px;
                color: #666;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-direction: column;
                gap: 20px;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 16px;
                border: none;
                animation: fadeIn 0.4s ease-out;
                position: relative;
                overflow: hidden;
                min-height: 200px;
            }

            .loading::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
                animation: shimmer 2s infinite;
            }

            @keyframes fadeIn {
                from {
                    opacity: 0;
                    transform: translateY(15px) scale(0.95);
                }
                to {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }

            @keyframes shimmer {
                0% { left: -100%; }
                100% { left: 100%; }
            }
            
            .loading-spinner {
                width: 36px;
                height: 36px;
                border: 4px solid rgba(102, 126, 234, 0.1);
                border-left: 4px solid var(--primary-color);
                border-radius: 50%;
                animation: elegant-spin 1.5s linear infinite;
                position: relative;
            }

            .loading-spinner::before {
                content: '';
                position: absolute;
                top: -4px;
                left: -4px;
                right: -4px;
                bottom: -4px;
                border: 4px solid transparent;
                border-top: 4px solid rgba(102, 126, 234, 0.3);
                border-radius: 50%;
                animation: elegant-spin 2s linear infinite reverse;
            }

            @keyframes elegant-spin {
                0% { 
                    transform: rotate(0deg);
                }
                100% { 
                    transform: rotate(360deg);
                }
            }

            .loading-text {
                font-size: 16px;
                font-weight: 500;
                color: #495057;
                letter-spacing: 0.5px;
                position: relative;
                z-index: 1;
            }



            .placeholder-content {
                text-align: center;
                padding: 40px 20px;
                color: #666;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-direction: column;
                gap: 10px;
                background: #f8f9fa;
                border-radius: 8px;
                border: 2px dashed #dee2e6;
            }

            .placeholder-content .main-text {
                font-size: 16px;
                font-weight: 500;
                color: #495057;
            }

            .placeholder-content .help-text {
                font-size: 13px;
                color: #6c757d;
                line-height: 1.4;
            }

            .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                transition: all 0.2s ease;
                white-space: nowrap;
            }

            .btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }

            .btn-primary { background: var(--info-color); color: white; }
            .btn-success { background: var(--success-color); color: white; }
            .btn-warning { background: var(--warning-color); color: #333; }
            .btn-danger { background: var(--danger-color); color: white; }
            .btn-secondary { background: #6c757d; color: white; }
            .btn-info { background: #17a2b8; color: white; }

            .btn-sm {
                padding: 6px 12px;
                font-size: 13px;
            }

            .form-control {
                width: 100%;
                padding: 10px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 14px;
                transition: border-color 0.2s ease;
            }

            .form-control:focus {
                outline: none;
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }

            .server-selection {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.95) 100%);
                padding: 30px;
                border-radius: 20px;
                margin-bottom: 30px;
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12), 0 4px 16px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.8);
                backdrop-filter: blur(20px);
                position: relative;
                overflow: hidden;
                transition: all 0.3s ease;
            }

            .server-selection::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 50%, #4facfe 100%);
                border-radius: 20px 20px 0 0;
            }

            .server-selection:hover {
                transform: translateY(-2px);
                box-shadow: 0 16px 50px rgba(0, 0, 0, 0.15), 0 6px 20px rgba(0, 0, 0, 0.1);
            }

            .server-selection h3 {
                margin-bottom: 25px;
                color: #2d3748;
                font-size: 24px;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 12px;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                position: relative;
            }

            .server-selection h3::after {
                content: '';
                position: absolute;
                bottom: -8px;
                left: 0;
                width: 60px;
                height: 3px;
                background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
                border-radius: 2px;
            }

            .server-controls {
                display: grid;
                grid-template-columns: 2fr auto auto;
                gap: 20px;
                align-items: center;
                margin-bottom: 15px;
            }

            .server-controls select {
                padding: 14px 18px;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 500;
                background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
                color: #2d3748;
                transition: all 0.3s ease;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
                cursor: pointer;
                min-height: 52px;
            }

            .server-controls select:hover {
                border-color: var(--primary-color);
                box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15);
                transform: translateY(-1px);
            }

            .server-controls select:focus {
                outline: none;
                border-color: var(--primary-color);
                box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1), 0 4px 16px rgba(102, 126, 234, 0.15);
            }

            .server-controls .btn {
                padding: 14px 20px;
                font-size: 15px;
                font-weight: 600;
                border-radius: 12px;
                min-height: 52px;
                display: flex;
                align-items: center;
                justify-content: center;
                white-space: nowrap;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
            }

            .server-controls .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
            }

            .server-controls .btn-info {
                background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
                border: none;
            }

            .server-controls .btn-primary {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                border: none;
            }

            .status-indicator {
                display: inline-flex;
                align-items: center;
                gap: 12px;
                padding: 18px 32px;
                border-radius: 35px;
                font-size: 16px;
                font-weight: 700;
                letter-spacing: 0.8px;
                position: relative;
                overflow: hidden;
                transition: all 0.3s ease;
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
                backdrop-filter: blur(15px);
                border: 3px solid rgba(255, 255, 255, 0.3);
                text-transform: uppercase;
                min-width: 240px;
                justify-content: center;
                height: 60px;
            }

            .status-indicator::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                transition: left 0.6s ease;
            }

            .status-indicator:hover::before {
                left: 100%;
            }

            .status-indicator:hover {
                transform: translateY(-2px) scale(1.02);
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
            }

            .status-running { 
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white;
                box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
            }
            
            .status-running:hover {
                box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4);
            }
            
            .status-stopped { 
                background: linear-gradient(135deg, #dc3545 0%, #e74c3c 100%);
                color: white;
                box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
            }
            
            .status-stopped:hover {
                box-shadow: 0 8px 25px rgba(220, 53, 69, 0.4);
            }
            
            .status-unknown { 
                background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
                color: #333;
                box-shadow: 0 4px 15px rgba(255, 193, 7, 0.3);
            }
            
            .status-unknown:hover {
                box-shadow: 0 8px 25px rgba(255, 193, 7, 0.4);
            }

            /* 状态指示器动画效果 */
            .status-running::after {
                content: '';
                position: absolute;
                right: 20px;
                top: 50%;
                transform: translateY(-50%);
                width: 10px;
                height: 10px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 50%;
                animation: pulse-green 2s infinite;
                box-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
            }

            .status-unknown::after {
                content: '';
                position: absolute;
                right: 20px;
                top: 50%;
                transform: translateY(-50%);
                width: 10px;
                height: 10px;
                background: rgba(51, 51, 51, 0.9);
                border-radius: 50%;
                animation: pulse-orange 2s infinite;
                box-shadow: 0 0 8px rgba(51, 51, 51, 0.4);
            }

            @keyframes pulse-green {
                0%, 100% {
                    opacity: 1;
                    transform: translateY(-50%) scale(1);
                }
                50% {
                    opacity: 0.6;
                    transform: translateY(-50%) scale(1.2);
                }
            }

            @keyframes pulse-orange {
                0%, 100% {
                    opacity: 1;
                    transform: translateY(-50%) scale(1);
                }
                50% {
                    opacity: 0.6;
                    transform: translateY(-50%) scale(1.2);
                }
            }

            /* 服务器状态显示区域样式 */
            .server-status-display {
                margin-top: 20px;
                padding: 20px;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 16px;
                border: 2px solid rgba(255, 255, 255, 0.8);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                position: relative;
                overflow: hidden;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            }

            .server-status-display::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 50%, #4facfe 100%);
                border-radius: 16px 16px 0 0;
            }

            .server-status-display:hover {
                transform: translateY(-3px);
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
            }

            .server-status-display:empty {
                display: none;
            }

            .alert {
                padding: 12px 16px;
                border-radius: 6px;
                margin-bottom: 15px;
                border-left: 4px solid;
            }

            .alert-success { background: #d4edda; border-color: var(--success-color); color: #155724; }
            .alert-warning { background: #fff3cd; border-color: var(--warning-color); color: #856404; }
            .alert-danger { background: #f8d7da; border-color: var(--danger-color); color: #721c24; }
            .alert-info { background: #d1ecf1; border-color: var(--info-color); color: #0c5460; }

            .grid-form {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }

            .form-group {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .form-label {
                font-weight: 600;
                color: #333;
                font-size: 14px;
            }

            .form-help {
                font-size: 12px;
                color: #666;
                margin-top: 4px;
            }

            .modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.7);
                z-index: 10000;
                align-items: center;
                justify-content: center;
            }

            .modal-content {
                background: white;
                border-radius: var(--border-radius);
                max-width: 600px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            }

            .modal-header {
                padding: 20px;
                border-bottom: 1px solid #eee;
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                color: white;
                border-radius: var(--border-radius) var(--border-radius) 0 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .modal-header h3 {
                margin: 0;
                font-size: 20px;
            }

            .modal-close {
                background: none;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                padding: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: background 0.2s ease;
            }

            .modal-close:hover {
                background: rgba(255,255,255,0.2);
            }

            .modal-body {
                padding: 20px;
            }

            .preset-card {
                padding: 15px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s ease;
                margin-bottom: 15px;
            }

            .preset-card:hover {
                border-color: var(--primary-color);
                background: #f8f9fa;
                transform: translateY(-1px);
            }

            .preset-card h4 {
                margin: 0 0 8px 0;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .preset-card p {
                margin: 0 0 8px 0;
                color: #666;
                font-size: 14px;
            }

            .preset-meta {
                font-size: 12px;
                color: #999;
                background: #f8f9fa;
                padding: 8px;
                border-radius: 4px;
                margin-top: 8px;
            }

            .advanced-panel {
                background: #f8f9fa;
                border-radius: 8px;
                margin-top: 20px;
                overflow: hidden;
                border: 1px solid #e9ecef;
            }

            .advanced-panel h4 {
                margin: 0;
                padding: 15px 20px;
                background: #e9ecef;
                color: #495057;
                border-bottom: 1px solid #dee2e6;
                font-size: 16px;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .advanced-panel-content {
                padding: 20px;
            }

            .error-message {
                color: var(--danger-color);
                background: #f8d7da;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
                border-left: 4px solid var(--danger-color);
            }

            .success-message {
                color: var(--success-color);
                background: #d4edda;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
                border-left: 4px solid var(--success-color);
            }

            @media (max-width: 768px) {
                .vllm-grid {
                    grid-template-columns: 1fr;
                }
                
                .server-selection {
                    padding: 20px;
                    margin-bottom: 20px;
                }
                
                .server-selection h3 {
                    font-size: 20px;
                    margin-bottom: 20px;
                }
                
                .server-controls {
                    grid-template-columns: 1fr;
                    gap: 15px;
                }
                
                .server-controls .btn {
                    padding: 12px 16px;
                    font-size: 14px;
                    min-height: 48px;
                }
                
                .server-controls select {
                    padding: 12px 16px;
                    font-size: 15px;
                    min-height: 48px;
                }
                
                .grid-form {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="vllm-header">
            <div class="header-content">
                <h1 class="header-title">
                    🚀 VLLM模型服务管理
                </h1>
                <div style="display: flex; gap: 10px;">
                    <a href="/dashboard" class="btn btn-secondary">← 返回控制台</a>
                    <button id="global-refresh" class="btn btn-primary">🔄 全局刷新</button>
                </div>
            </div>
        </div>
        
        <div class="vllm-container">
            <div class="page-title-section">
                <h2>VLLM模型服务管理中心</h2>
                <p>远程启动停止 | 实时监控 | 智能诊断 | 日志查看</p>
            </div>

            <!-- 服务器选择区域 -->
            <div class="server-selection">
                <h3>🖥️ 服务器选择</h3>
                <div class="server-controls">
                    <select id="server-select" class="form-control">
                        <option value="">选择GPU服务器...</option>
                    </select>
                    <button id="test-connection" class="btn btn-info">🔧 测试连接</button>
                    <button id="refresh-servers" class="btn btn-primary">🔄 刷新列表</button>
                </div>
                <div id="server-status" class="server-status-display"></div>
            </div>

            <!-- Conda环境管理 -->
            <div class="vllm-panel" style="margin-bottom: 20px;">
                <div class="panel-header">
                    <div class="panel-title">🐍 Conda环境管理</div>
                    <div style="display: flex; gap: 10px;">
                        <button id="refresh-conda-list" class="btn btn-info btn-sm">🔄 刷新环境</button>
                        <button id="activate-conda-env" class="btn btn-success btn-sm">✅ 激活环境</button>
                        <button id="check-conda-status" class="btn btn-primary btn-sm">📊 检查状态</button>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 15px;">
                    <div class="form-group">
                        <label class="form-label">可用Conda环境</label>
                        <select id="conda-env-selector" class="form-control">
                            <option value="">选择Conda环境...</option>
                        </select>
                        <div class="form-help">选择要激活的Conda虚拟环境</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">当前激活环境</label>
                        <div id="current-conda-env" class="form-control" style="background: #f8f9fa; color: #666; display: flex; align-items: center; min-height: 42px;">
                            未检测到激活环境
                        </div>
                        <div class="form-help">当前会话中激活的环境</div>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr auto; gap: 20px; margin-bottom: 15px;">
                    <div class="form-group">
                        <label class="form-label">Root密码 (可选)</label>
                        <input type="password" id="root-password" class="form-control" placeholder="输入root密码以使用sudo权限">
                        <div class="form-help">如果需要root权限激活环境，请输入密码</div>
                    </div>
                    
                    <div class="form-group" style="display: flex; align-items: end;">
                        <label class="form-label" style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                            <input type="checkbox" id="use-sudo" style="margin: 0;">
                            使用sudo权限
                        </label>
                        <div class="form-help">勾选此项将使用sudo权限激活环境</div>
                    </div>
                </div>
                
                <div class="content-area" id="conda-env-content" style="min-height: 120px;">
                    <div class="placeholder-content">
                        <div class="main-text">🐍 请选择服务器并刷新Conda环境列表</div>
                        <div class="help-text">这里将显示环境详情、Python版本、已安装包等信息</div>
                    </div>
                </div>
                
                <div id="conda-env-status" style="margin-top: 15px; padding: 12px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #17a2b8; display: none;">
                    <strong>💡 提示：</strong> 建议先激活合适的Conda环境，再启动VLLM模型服务，这样可以确保使用正确的Python环境和依赖包。
                </div>
            </div>

            <!-- 主功能面板 -->
            <div class="vllm-grid">
                <!-- 环境诊断 -->
                <div class="vllm-panel">
                    <div class="panel-header">
                        <div class="panel-title">🔍 环境诊断</div>
                        <button id="run-diagnosis" class="btn btn-primary btn-sm">开始诊断</button>
                    </div>
                    <div class="content-area" id="diagnosis-content">
                        <div class="placeholder-content" style="min-height: 150px;">
                            <div class="main-text">🖥️ 请选择服务器并开始诊断</div>
                            <div class="help-text">检查Python环境、VLLM安装、GPU状态等</div>
                        </div>
                    </div>
                </div>

                <!-- 模型发现 -->
                <div class="vllm-panel">
                    <div class="panel-header">
                        <div class="panel-title">🔎 模型发现</div>
                        <button id="discover-models" class="btn btn-primary btn-sm">扫描模型</button>
                    </div>
                    <div class="content-area" id="models-content">
                        <div class="placeholder-content" style="min-height: 150px;">
                            <div class="main-text">📁 请选择服务器并扫描模型</div>
                            <div class="help-text">自动发现服务器上的可用模型文件</div>
                        </div>
                    </div>
                </div>

                <!-- 运行状态 -->
                <div class="vllm-panel">
                    <div class="panel-header">
                        <div class="panel-title">📊 运行状态</div>
                        <button id="check-status" class="btn btn-primary btn-sm">检查状态</button>
                    </div>
                    <div class="content-area" id="status-content">
                        <div class="placeholder-content" style="min-height: 150px;">
                            <div class="main-text">⚡ 请选择服务器并检查状态</div>
                            <div class="help-text">查看正在运行的VLLM服务进程</div>
                        </div>
                    </div>
                </div>

                <!-- 服务日志 -->
                <div class="vllm-panel">
                    <div class="panel-header">
                        <div class="panel-title">📝 服务日志</div>
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <input type="number" id="log-port" placeholder="端口" class="form-control" style="width: 80px; font-size: 12px;">
                            <button id="view-logs" class="btn btn-primary btn-sm">查看日志</button>
                        </div>
                    </div>
                    <div class="content-area" id="logs-content">
                        <div class="placeholder-content" style="min-height: 150px;">
                            <div class="main-text">📋 请输入端口号并查看日志</div>
                            <div class="help-text">查看指定端口服务的运行日志</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 快速启动服务 -->
            <div class="vllm-panel">
                <div class="panel-header">
                    <div class="panel-title">⚡ 快速启动服务</div>
                    <div style="display: flex; gap: 10px;">
                        <button id="show-presets" class="btn btn-info btn-sm">📋 预设配置</button>
                        <button id="toggle-advanced" class="btn btn-secondary btn-sm">🔧 高级设置</button>
                        <button id="start-service" class="btn btn-success">🚀 启动服务</button>
                    </div>
                </div>
                
                <div class="grid-form">
                    <div class="form-group">
                        <label class="form-label">模型路径 *</label>
                        <input type="text" id="model-path" class="form-control" placeholder="/path/to/model">
                        <div class="form-help">模型文件的完整路径</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">服务端口 *</label>
                        <input type="number" id="service-port" class="form-control" placeholder="8000" min="1000" max="65535">
                        <div class="form-help">HTTP服务监听端口 (1000-65535)</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">GPU索引</label>
                        <input type="text" id="gpu-indices" class="form-control" placeholder="0,1 (留空使用全部)">
                        <div class="form-help">指定使用的GPU，如: 0,1,2</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">张量并行大小</label>
                        <input type="number" id="tensor-parallel" class="form-control" value="1" min="1" max="8">
                        <div class="form-help">跨GPU的张量并行数量</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">最大模型长度</label>
                        <input type="number" id="max-model-len" class="form-control" value="4096" min="512" step="512">
                        <div class="form-help">支持的最大序列长度</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">GPU内存利用率</label>
                        <input type="number" id="gpu-memory-util" class="form-control" value="0.9" min="0.1" max="1.0" step="0.05">
                        <div class="form-help">GPU显存使用比例 (0.1-1.0)</div>
                    </div>
                </div>

                <!-- 高级设置面板 -->
                <div id="advanced-settings" class="advanced-panel" style="display: none;">
                    <h4>🔧 高级启动参数</h4>
                    <div class="advanced-panel-content">
                        <div class="grid-form">
                            <div class="form-group">
                                <label class="form-label">数据类型</label>
                                <select id="dtype" class="form-control">
                                    <option value="auto">自动</option>
                                    <option value="half">FP16</option>
                                    <option value="float16">Float16</option>
                                    <option value="bfloat16">BFloat16</option>
                                    <option value="float32">Float32</option>
                                </select>
                                <div class="form-help">模型推理精度</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">量化方式</label>
                                <select id="quantization" class="form-control">
                                    <option value="">无量化</option>
                                    <option value="awq">AWQ</option>
                                    <option value="gptq">GPTQ</option>
                                    <option value="squeezellm">SqueezeLLM</option>
                                    <option value="fp8">FP8</option>
                                </select>
                                <div class="form-help">模型量化加速推理</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">信任远程代码</label>
                                <select id="trust-remote-code" class="form-control">
                                    <option value="false">否</option>
                                    <option value="true">是</option>
                                </select>
                                <div class="form-help">允许执行远程模型代码</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Ray工作进程</label>
                                <input type="number" id="worker-use-ray" class="form-control" value="0" min="0" max="16">
                                <div class="form-help">0=禁用Ray，>0启用分布式</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 性能监控 -->
            <div class="vllm-panel">
                <div class="panel-header">
                    <div class="panel-title">📊 性能监控</div>
                    <div style="display: flex; gap: 10px;">
                        <button id="refresh-performance" class="btn btn-primary btn-sm">🔄 刷新</button>
                        <button id="toggle-auto-refresh" class="btn btn-secondary btn-sm">⏱️ 自动刷新</button>
                    </div>
                </div>
                <div class="content-area" id="performance-content">
                    <div class="placeholder-content" style="min-height: 150px;">
                        <div class="main-text">📈 请选择服务器并刷新性能数据</div>
                        <div class="help-text">GPU使用率、内存占用、系统负载等信息</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 预设配置模态框 -->
        <div id="presets-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>📋 启动参数预设</h3>
                    <button id="close-presets" class="modal-close">×</button>
                </div>
                <div class="modal-body">
                    <div class="preset-card" data-preset="small">
                        <h4 style="color: #28a745;">🐣 小模型 (7B以下)</h4>
                        <p>适用于7B参数以下的模型，单GPU，低资源消耗</p>
                        <div class="preset-meta">
                            张量并行: 1 | 最大长度: 4096 | GPU利用率: 85% | 数据类型: FP16
                        </div>
                    </div>
                    
                    <div class="preset-card" data-preset="medium">
                        <h4 style="color: #007bff;">🚀 中等模型 (7B-13B)</h4>
                        <p>适用于7B-13B参数的模型，双GPU并行</p>
                        <div class="preset-meta">
                            张量并行: 2 | 最大长度: 4096 | GPU利用率: 90% | 数据类型: FP16
                        </div>
                    </div>
                    
                    <div class="preset-card" data-preset="large">
                        <h4 style="color: #fd7e14;">🔥 大模型 (30B+)</h4>
                        <p>适用于30B+参数的大模型，多GPU并行，高性能</p>
                        <div class="preset-meta">
                            张量并行: 4 | 最大长度: 2048 | GPU利用率: 95% | 数据类型: FP16
                        </div>
                    </div>
                    
                    <div class="preset-card" data-preset="chat">
                        <h4 style="color: #6f42c1;">💬 对话模型优化</h4>
                        <p>专为聊天对话优化，支持长上下文</p>
                        <div class="preset-meta">
                            张量并行: 2 | 最大长度: 8192 | GPU利用率: 88% | 数据类型: BFloat16
                        </div>
                    </div>
                    
                    <div class="preset-card" data-preset="custom">
                        <h4 style="color: #6c757d;">⚙️ 自定义配置</h4>
                        <p>保持当前参数设置不变</p>
                    </div>
                </div>
            </div>
        </div>

        <script>
        // VLLM管理器类
        class VLLMManager {
            constructor() {
                this.currentServer = '';
                this.autoRefreshInterval = null;
                this.isInitialized = false;
                this.isActivating = false;
                this.isCheckingStatus = false;
            }

            // 初始化管理器
            async init() {
                try {
                    console.log('🚀 VLLMManager 初始化开始...');
                    
                    // 绑定事件处理器
                    this.bindEvents();
                    
                    // 加载服务器列表
                    await this.loadServers();
                    
                    this.isInitialized = true;
                    console.log('✅ VLLMManager 初始化完成');
                    
                    this.showMessage('系统初始化完成', 'success');
                } catch (error) {
                    console.error('❌ VLLMManager 初始化失败:', error);
                    this.showMessage(`初始化失败: ${error.message}`, 'error');
                }
            }

            // 显示消息
            showMessage(message, type = 'info', duration = 3000) {
                const alertClass = type === 'error' ? 'alert-danger' : 
                                  type === 'success' ? 'alert-success' : 
                                  type === 'warning' ? 'alert-warning' : 'alert-info';
                
                const alertDiv = document.createElement('div');
                alertDiv.className = `alert ${alertClass}`;
                alertDiv.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 10001; min-width: 300px;';
                alertDiv.textContent = message;
                
                document.body.appendChild(alertDiv);
                
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.parentNode.removeChild(alertDiv);
                    }
                }, duration);
            }

            // 错误处理
            handleError(operation, error) {
                console.error(`❌ ${operation} 失败:`, error);
                this.showMessage(`${operation} 失败: ${error.message}`, 'error');
            }

            // 绑定事件处理器
            bindEvents() {
                // 服务器选择变化
                document.getElementById('server-select').addEventListener('change', (e) => {
                    this.currentServer = e.target.value;
                    this.updateServerStatus();
                });

                // 按钮事件
                const buttons = {
                    'test-connection': () => this.testConnection(),
                    'refresh-servers': () => this.loadServers(),
                    'run-diagnosis': () => this.runDiagnosis(),
                    'discover-models': () => this.discoverModels(),
                    'check-status': () => this.checkRunningServices(),
                    'view-logs': () => this.viewLogs(),
                    'start-service': () => this.startService(),
                    'toggle-advanced': () => this.toggleAdvancedSettings(),
                    'show-presets': () => this.showPresetsModal(),
                    'close-presets': () => this.hidePresetsModal(),
                    'refresh-performance': () => this.refreshPerformance(),
                    'toggle-auto-refresh': () => this.toggleAutoRefresh(),
                    'global-refresh': () => this.globalRefresh(),
                    // Conda环境管理按钮
                    'refresh-conda-list': () => this.refreshCondaEnvList(),
                    'activate-conda-env': () => this.activateCondaEnv(),
                    'check-conda-status': () => this.checkCondaStatus()
                };

                Object.entries(buttons).forEach(([id, handler]) => {
                    const element = document.getElementById(id);
                    if (element) {
                        element.addEventListener('click', handler);
                    }
                });

                // 预设配置点击事件
                document.querySelectorAll('.preset-card').forEach(card => {
                    card.addEventListener('click', () => {
                        this.applyPreset(card.dataset.preset);
                    });
                });

                // 模态框点击外部关闭
                document.getElementById('presets-modal').addEventListener('click', (e) => {
                    if (e.target === e.currentTarget) {
                        this.hidePresetsModal();
                    }
                });
            }

            // 更新服务器状态显示
            updateServerStatus() {
                const statusDiv = document.getElementById('server-status');
                if (this.currentServer) {
                    statusDiv.innerHTML = `<div class="status-indicator status-running">✅ 已选择: ${this.currentServer}</div>`;
                } else {
                    statusDiv.innerHTML = `<div class="status-indicator status-unknown">⚠️ 请选择服务器</div>`;
                }
            }

            // 加载服务器列表
            async loadServers() {
                const select = document.getElementById('server-select');
                
                try {
                    this.showMessage('正在加载服务器列表...', 'info', 1000);
                    
                    const response = await fetch('/api/vllm/servers');
                    const data = await response.json();
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    if (!data.success) {
                        throw new Error(data.message || '获取服务器列表失败');
                    }
                    
                    // 清空并重新填充选项
                    select.innerHTML = '<option value="">选择GPU服务器...</option>';
                    
                    if (data.data && Array.isArray(data.data)) {
                        data.data.forEach(server => {
                            const option = document.createElement('option');
                            option.value = server.name;
                            option.textContent = `${server.name} (${server.host})`;
                            select.appendChild(option);
                        });
                        
                        this.showMessage(`加载了 ${data.data.length} 个服务器`, 'success');
                    } else {
                        this.showMessage('没有可用的服务器', 'warning');
                    }
                } catch (error) {
                    this.handleError('加载服务器列表', error);
                    select.innerHTML = '<option value="">❌ 加载失败，请重试</option>';
                }
            }

            // 测试连接
            async testConnection() {
                if (!this.currentServer) {
                    this.showMessage('请先选择服务器', 'warning');
                    return;
                }

                try {
                    this.showMessage('正在测试连接...', 'info');
                    
                    const response = await fetch('/api/vllm/diagnose/' + this.currentServer);
                    const data = await response.json();
                    
                    if (data.success && data.data.ssh_connection) {
                        this.showMessage(`✅ ${this.currentServer} 连接正常`, 'success');
                    } else {
                        this.showMessage(`❌ ${this.currentServer} 连接失败`, 'error');
                    }
                } catch (error) {
                    this.handleError('测试连接', error);
                }
            }

            // 验证服务器选择
            validateServerSelection() {
                if (!this.currentServer) {
                    this.showMessage('请先选择服务器', 'warning');
                    return false;
                }
                return true;
            }

            // 运行诊断
            async runDiagnosis() {
                if (!this.validateServerSelection()) return;

                const content = document.getElementById('diagnosis-content');
                content.innerHTML = this.getLoadingHTML('检查中...');

                try {
                    const response = await fetch(`/api/vllm/diagnose/${this.currentServer}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        this.renderDiagnosis(data.data);
                    } else {
                        content.innerHTML = this.getErrorHTML(`诊断失败: ${data.message}`);
                    }
                } catch (error) {
                    this.handleError('环境诊断', error);
                    content.innerHTML = this.getErrorHTML(`诊断出错: ${error.message}`);
                }
            }

            // 发现模型
            async discoverModels() {
                if (!this.validateServerSelection()) return;

                const content = document.getElementById('models-content');
                content.innerHTML = this.getLoadingHTML('扫描中...');

                try {
                    const response = await fetch(`/api/vllm/models/${this.currentServer}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        this.renderDiscoveredModels(data.data.discovered_models || []);
                    } else {
                        content.innerHTML = this.getErrorHTML(`扫描失败: ${data.message}`);
                    }
                } catch (error) {
                    this.handleError('模型扫描', error);
                    content.innerHTML = this.getErrorHTML(`扫描出错: ${error.message}`);
                }
            }

            // 检查运行状态
            async checkRunningServices() {
                if (!this.validateServerSelection()) return;

                const content = document.getElementById('status-content');
                content.innerHTML = this.getLoadingHTML('刷新中...');

                try {
                    const response = await fetch(`/api/vllm/running/${this.currentServer}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        this.renderRunningServices(data.data.services || []);
                    } else {
                        content.innerHTML = this.getErrorHTML(`检查失败: ${data.message}`);
                    }
                } catch (error) {
                    this.handleError('状态检查', error);
                    content.innerHTML = this.getErrorHTML(`检查出错: ${error.message}`);
                }
            }

            // 查看日志
            async viewLogs() {
                const port = document.getElementById('log-port').value;
                if (!port || !this.validateServerSelection()) {
                    this.showMessage('请选择服务器并输入端口号', 'warning');
                    return;
                }

                const content = document.getElementById('logs-content');
                content.innerHTML = this.getLoadingHTML('加载中...');

                try {
                    const response = await fetch(`/api/vllm/logs/${this.currentServer}/${port}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        const logs = data.data.logs || '暂无日志';
                        content.innerHTML = `
                            <div style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 6px; font-family: 'Consolas', 'Monaco', monospace; white-space: pre-wrap; font-size: 12px; line-height: 1.4; max-height: 350px; overflow-y: auto;">
                                ${this.escapeHtml(logs)}
                            </div>
                        `;
                    } else {
                        content.innerHTML = this.getErrorHTML(`获取日志失败: ${data.message}`);
                    }
                } catch (error) {
                    this.handleError('获取日志', error);
                    content.innerHTML = this.getErrorHTML(`获取日志出错: ${error.message}`);
                }
            }

            // 启动服务
            async startService() {
                if (!this.validateServerSelection()) return;

                const params = this.getServiceParams();
                if (!params) return;

                try {
                    this.showMessage('正在启动服务...', 'info');
                    
                    const response = await fetch('/api/vllm/start', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            server_name: this.currentServer,
                            ...params
                        })
                    });

                    const data = await response.json();
                    
                    if (data.success) {
                        this.showMessage(`🎉 服务启动成功！\n端口: ${params.port}`, 'success', 5000);
                        // 自动刷新状态
                        setTimeout(() => this.checkRunningServices(), 2000);
                    } else {
                        this.showMessage(`启动失败: ${data.message}`, 'error');
                    }
                } catch (error) {
                    this.handleError('启动服务', error);
                }
            }

            // 获取服务参数
            getServiceParams() {
                const modelPath = document.getElementById('model-path').value.trim();
                const port = parseInt(document.getElementById('service-port').value);
                
                if (!modelPath || !port) {
                    this.showMessage('请填写必填项: 模型路径和端口', 'warning');
                    return null;
                }

                if (port < 1000 || port > 65535) {
                    this.showMessage('端口号应在1000-65535之间', 'warning');
                    return null;
                }

                // 获取选择的conda环境，如果没有选择则使用'base'
                const selectedCondaEnv = document.getElementById('conda-env-selector').value || 'base';
                
                return {
                    conda_env: selectedCondaEnv,
                    model_path: modelPath,
                    port: port,
                    gpu_indices: document.getElementById('gpu-indices').value.trim(),
                    tensor_parallel_size: parseInt(document.getElementById('tensor-parallel').value) || 1,
                    max_model_len: parseInt(document.getElementById('max-model-len').value) || 4096,
                    gpu_memory_utilization: parseFloat(document.getElementById('gpu-memory-util').value) || 0.9,
                    dtype: document.getElementById('dtype').value || "auto",
                    quantization: document.getElementById('quantization').value || null,
                    trust_remote_code: document.getElementById('trust-remote-code').value === 'true',
                    worker_use_ray: parseInt(document.getElementById('worker-use-ray').value) || 0
                };
            }

            // 停止服务
            async stopService(pid, port) {
                if (!confirm('确定要停止此服务吗？')) return;

                try {
                    const response = await fetch('/api/vllm/stop', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            server_name: this.currentServer,
                            pid: pid,
                            port: port
                        })
                    });

                    const data = await response.json();
                    
                    if (data.success) {
                        this.showMessage('服务停止成功!', 'success');
                        this.checkRunningServices(); // 刷新状态
                    } else {
                        this.showMessage(`停止失败: ${data.message}`, 'error');
                    }
                } catch (error) {
                    this.handleError('停止服务', error);
                }
            }

            // 刷新性能数据
            async refreshPerformance() {
                if (!this.validateServerSelection()) return;

                const content = document.getElementById('performance-content');
                content.innerHTML = this.getLoadingHTML('刷新中...');

                try {
                    const response = await fetch(`/api/vllm/performance/${this.currentServer}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        this.renderPerformanceData(data.data);
                    } else {
                        content.innerHTML = this.getErrorHTML(`获取性能数据失败: ${data.message}`);
                    }
                } catch (error) {
                    this.handleError('获取性能数据', error);
                    content.innerHTML = this.getErrorHTML(`获取性能数据出错: ${error.message}`);
                }
            }

            // 切换自动刷新
            toggleAutoRefresh() {
                const button = document.getElementById('toggle-auto-refresh');
                
                if (this.autoRefreshInterval) {
                    clearInterval(this.autoRefreshInterval);
                    this.autoRefreshInterval = null;
                    button.innerHTML = '⏱️ 自动刷新';
                    button.classList.remove('btn-warning');
                    button.classList.add('btn-secondary');
                    this.showMessage('已停止自动刷新', 'info');
                } else {
                    this.autoRefreshInterval = setInterval(() => {
                        this.refreshPerformance();
                    }, 5000);
                    
                    button.innerHTML = '⏸️ 停止刷新';
                    button.classList.remove('btn-secondary');
                    button.classList.add('btn-warning');
                    this.showMessage('已开启自动刷新 (5秒)', 'info');
                    
                    this.refreshPerformance();
                }
            }

            // 切换高级设置
            toggleAdvancedSettings() {
                const panel = document.getElementById('advanced-settings');
                const button = document.getElementById('toggle-advanced');
                
                if (panel.style.display === 'none') {
                    panel.style.display = 'block';
                    button.innerHTML = '🔼 收起高级';
                    button.classList.remove('btn-secondary');
                    button.classList.add('btn-warning');
                } else {
                    panel.style.display = 'none';
                    button.innerHTML = '🔧 高级设置';
                    button.classList.remove('btn-warning');
                    button.classList.add('btn-secondary');
                }
            }

            // 显示预设模态框
            showPresetsModal() {
                document.getElementById('presets-modal').style.display = 'flex';
            }

            // 隐藏预设模态框
            hidePresetsModal() {
                document.getElementById('presets-modal').style.display = 'none';
            }

            // 应用预设配置
            applyPreset(presetType) {
                const presets = {
                    small: {
                        tensorParallel: 1,
                        maxModelLen: 4096,
                        gpuMemoryUtil: 0.85,
                        dtype: 'half'
                    },
                    medium: {
                        tensorParallel: 2,
                        maxModelLen: 4096,
                        gpuMemoryUtil: 0.90,
                        dtype: 'half'
                    },
                    large: {
                        tensorParallel: 4,
                        maxModelLen: 2048,
                        gpuMemoryUtil: 0.95,
                        dtype: 'half'
                    },
                    chat: {
                        tensorParallel: 2,
                        maxModelLen: 8192,
                        gpuMemoryUtil: 0.88,
                        dtype: 'bfloat16'
                    }
                };

                if (presetType === 'custom') {
                    this.hidePresetsModal();
                    return;
                }

                const preset = presets[presetType];
                if (preset) {
                    document.getElementById('tensor-parallel').value = preset.tensorParallel;
                    document.getElementById('max-model-len').value = preset.maxModelLen;
                    document.getElementById('gpu-memory-util').value = preset.gpuMemoryUtil;
                    document.getElementById('dtype').value = preset.dtype;
                    
                    this.showMessage(`✅ 已应用 "${presetType.toUpperCase()}" 预设配置！`, 'success');
                }
                
                this.hidePresetsModal();
            }

            // 全局刷新
            async globalRefresh() {
                this.showMessage('正在执行全局刷新...', 'info');
                
                try {
                    await this.loadServers();
                    
                    if (this.currentServer) {
                        await Promise.all([
                            this.checkRunningServices(),
                            this.refreshPerformance(),
                            this.refreshCondaEnvList()
                        ]);
                    }
                    
                    this.showMessage('全局刷新完成', 'success');
                } catch (error) {
                    this.handleError('全局刷新', error);
                }
            }

            // 设置激活相关按钮的状态
            setActivationButtonsState(enabled) {
                const buttons = [
                    'activate-conda-env',
                    'check-conda-status',
                    'refresh-conda-list'
                ];
                
                buttons.forEach(buttonId => {
                    const button = document.getElementById(buttonId);
                    if (button) {
                        button.disabled = !enabled;
                    }
                });
                
                // 同时禁用/启用快速激活按钮
                const quickActivateButtons = document.querySelectorAll('[id^="quick-activate-"]');
                quickActivateButtons.forEach(button => {
                    button.disabled = !enabled;
                    if (!enabled) {
                        button.style.opacity = '0.6';
                        button.style.cursor = 'not-allowed';
                    } else {
                        button.style.opacity = '1';
                        button.style.cursor = 'pointer';
                    }
                });
            }

            // 快速激活Conda环境
            async quickActivateEnv(envName, buttonId) {
                // 防重复点击检查
                if (this.isActivating) {
                    this.showMessage('正在激活环境，请稍候...', 'warning');
                    return;
                }
                
                const button = document.getElementById(buttonId);
                if (!button || button.disabled) {
                    return;
                }
                
                // 设置环境名称并调用激活方法
                const envSelector = document.getElementById('conda-env-selector');
                if (envSelector) {
                    envSelector.value = envName;
                }
                
                // 禁用当前按钮并显示加载状态
                const originalText = button.innerHTML;
                button.innerHTML = '⏳ 激活中...';
                button.disabled = true;
                
                try {
                    await this.activateCondaEnv();
                } catch (error) {
                    console.error('快速激活失败:', error);
                } finally {
                    // 恢复按钮状态
                    if (button) {
                        button.innerHTML = originalText;
                        button.disabled = false;
                    }
                }
            }

            // 执行状态同步（激活后的增强同步逻辑）
            async performStatusSync(expectedEnv) {
                console.log(`🔄 开始状态同步，期望环境: ${expectedEnv}`);
                
                // 等待一小段时间确保后端状态更新
                await new Promise(resolve => setTimeout(resolve, 800));
                
                // 进行多次验证，确保状态同步
                for (let attempt = 1; attempt <= 3; attempt++) {
                    try {
                        console.log(`🔄 第${attempt}次状态验证...`);
                        
                        // 添加时间戳避免缓存
                        const timestamp = new Date().getTime();
                        const response = await fetch(`/api/vllm/conda-status/${this.currentServer}?t=${timestamp}&force=true`);
                        const data = await response.json();
                        
                        if (data.success) {
                            this.renderCondaStatus(data.data);
                            
                            // 检查是否检测到了期望的环境
                            if (data.data.current_env === expectedEnv) {
                                console.log(`✅ 状态同步成功，当前环境: ${data.data.current_env}`);
                                return;
                            } else {
                                console.log(`⚠️ 第${attempt}次验证: 期望 ${expectedEnv}，实际 ${data.data.current_env || '未激活'}`);
                            }
                        }
                        
                        // 如果不是最后一次尝试，等待后再试
                        if (attempt < 3) {
                            await new Promise(resolve => setTimeout(resolve, 1000));
                        }
                    } catch (error) {
                        console.error(`第${attempt}次状态同步失败:`, error);
                    }
                }
                
                console.log('⚠️ 状态同步完成，但可能存在延迟');
            }
            
            // 同步Conda状态（用于激活后的状态同步）
            async syncCondaStatus() {
                if (!this.validateServerSelection()) return;
                
                // 如果正在检查状态，跳过同步
                if (this.isCheckingStatus) {
                    return;
                }
                
                try {
                    const response = await fetch(`/api/vllm/conda-status/${this.currentServer}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        this.renderCondaStatus(data.data);
                        console.log('✅ Conda状态同步完成');
                    }
                } catch (error) {
                    console.error('Conda状态同步失败:', error);
                }
            }

            // 刷新Conda环境列表（新的conda管理面板）
            async refreshCondaEnvList() {
                if (!this.validateServerSelection()) return;

                const select = document.getElementById('conda-env-selector');
                const content = document.getElementById('conda-env-content');
                const button = document.getElementById('refresh-conda-list');
                
                try {
                    button.disabled = true;
                    button.innerHTML = '🔄 刷新中...';
                    content.innerHTML = this.getLoadingHTML('正在获取Conda环境列表...');
                    
                    const response = await fetch(`/api/vllm/conda-envs/${this.currentServer}`);
                    const data = await response.json();
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    if (!data.success) {
                        throw new Error(data.message || '获取Conda环境列表失败');
                    }
                    
                    // 更新选择器
                    const currentValue = select.value;
                    select.innerHTML = '<option value="">选择Conda环境...</option>';
                    
                    if (data.data && Array.isArray(data.data)) {
                        data.data.forEach(env => {
                            const option = document.createElement('option');
                            option.value = env.name;
                            const displayText = env.description || env.name;
                            option.textContent = `${displayText}${env.is_default ? ' (默认)' : ''}`;
                            select.appendChild(option);
                        });
                        
                        if (currentValue) {
                            select.value = currentValue;
                        }
                        
                        // 渲染环境列表
                        this.renderCondaEnvList(data.data);
                        this.showMessage(`获取到 ${data.data.length} 个Conda环境`, 'success');
                    } else {
                        content.innerHTML = '<div class="placeholder-content"><div class="main-text">❌ 没有找到Conda环境</div><div class="help-text">请检查服务器上是否安装了Conda</div></div>';
                        this.showMessage('没有找到Conda环境', 'warning');
                    }
                } catch (error) {
                    this.handleError('获取Conda环境列表', error);
                    select.innerHTML = '<option value="">❌ 获取失败，请重试</option>';
                    content.innerHTML = this.getErrorHTML(`获取Conda环境列表失败: ${error.message}`);
                } finally {
                    button.disabled = false;
                    button.innerHTML = '🔄 刷新环境';
                }
            }

            // 激活Conda环境
            async activateCondaEnv() {
                if (!this.validateServerSelection()) return;

                const select = document.getElementById('conda-env-selector');
                const envName = select.value;
                
                if (!envName) {
                    this.showMessage('请先选择要激活的Conda环境', 'warning');
                    return;
                }

                const button = document.getElementById('activate-conda-env');
                const currentEnvDiv = document.getElementById('current-conda-env');
                
                // 防重复点击检查
                if (this.isActivating) {
                    this.showMessage('环境激活正在进行中，请稍候...', 'warning');
                    return;
                }
                
                // 获取密码和sudo选项
                const passwordInput = document.getElementById('root-password');
                const useSudoCheckbox = document.getElementById('use-sudo');
                const password = passwordInput ? passwordInput.value : '';
                const useSudo = useSudoCheckbox ? useSudoCheckbox.checked : false;
                
                // 如果选择使用sudo但没有输入密码，提示用户
                if (useSudo && !password) {
                    this.showMessage('使用sudo权限时请输入root密码', 'warning');
                    return;
                }
                
                try {
                    // 设置激活状态，防止重复操作
                    this.isActivating = true;
                    this.setActivationButtonsState(false);
                    button.innerHTML = '⏳ 激活中...';
                    this.showMessage(`正在激活Conda环境: ${envName}...`, 'info');
                    
                    const requestBody = {
                        server_name: this.currentServer,
                        env_name: envName
                    };
                    
                    // 如果使用sudo，添加密码
                    if (useSudo && password) {
                        requestBody.use_sudo = true;
                        requestBody.sudo_password = password;
                    }
                    
                    const response = await fetch('/api/vllm/activate-conda-env', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(requestBody)
                    });

                    const data = await response.json();
                    
                    if (data.success) {
                        currentEnvDiv.innerHTML = `<span style="color: #28a745; font-weight: 600;">✅ ${envName}</span>`;
                        currentEnvDiv.style.background = '#d4edda';
                        currentEnvDiv.style.borderColor = '#28a745';
                        
                        // 显示提示信息
                        const statusDiv = document.getElementById('conda-env-status');
                        statusDiv.style.display = 'block';
                        
                        // 根据是否使用缓存显示不同消息
                        const cacheMsg = data.data?.cached ? ' (缓存状态)' : '';
                        this.showMessage(`✅ Conda环境 "${envName}" 激活成功！${cacheMsg}`, 'success');
                        
                        // 激活成功后立即进行多次状态同步，确保前后端状态一致
                        await this.performStatusSync(envName);
                        
                        // 清除密码输入框
                        if (passwordInput) {
                            passwordInput.value = '';
                        }
                    } else {
                        this.showMessage(`激活失败: ${data.message}`, 'error');
                    }
                } catch (error) {
                    this.handleError('激活Conda环境', error);
                } finally {
                    // 重置激活状态并重新启用所有激活相关按钮
                    this.isActivating = false;
                    this.setActivationButtonsState(true);
                    button.innerHTML = '✅ 激活环境';
                }
            }

            // 检查Conda状态
            async checkCondaStatus() {
                if (!this.validateServerSelection()) return;

                // 防重复操作
                if (this.isCheckingStatus) {
                    this.showMessage('正在检查状态，请稍候...', 'warning');
                    return;
                }

                const button = document.getElementById('check-conda-status');
                const content = document.getElementById('conda-env-content');
                
                try {
                    this.isCheckingStatus = true;
                    this.setActivationButtonsState(false);
                    button.innerHTML = '🔍 检查中...';
                    content.innerHTML = this.getLoadingHTML('正在检查Conda状态...');
                    
                    const response = await fetch(`/api/vllm/conda-status/${this.currentServer}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        this.renderCondaStatus(data.data);
                        this.showMessage('Conda状态检查完成', 'success');
                    } else {
                        content.innerHTML = this.getErrorHTML(`检查Conda状态失败: ${data.message}`);
                    }
                } catch (error) {
                    this.handleError('检查Conda状态', error);
                    content.innerHTML = this.getErrorHTML(`检查Conda状态出错: ${error.message}`);
                } finally {
                    this.isCheckingStatus = false;
                    this.setActivationButtonsState(true);
                    button.innerHTML = '📊 检查状态';
                }
            }

            // 渲染Conda环境列表
            renderCondaEnvList(envs) {
                const content = document.getElementById('conda-env-content');
                
                if (!envs || envs.length === 0) {
                    content.innerHTML = '<div class="placeholder-content"><div class="main-text">❌ 没有找到Conda环境</div><div class="help-text">请检查服务器上是否安装了Conda</div></div>';
                    return;
                }

                let html = '<div style="display: grid; gap: 12px;">';
                envs.forEach((env, index) => {
                    const isDefault = env.is_default;
                    const borderColor = isDefault ? '#28a745' : '#e9ecef';
                    const bgColor = isDefault ? '#f8fff9' : 'white';
                    const buttonId = `quick-activate-${index}`;
                    
                    html += `
                        <div style="padding: 12px; background: ${bgColor}; border-radius: 8px; border: 2px solid ${borderColor}; transition: all 0.2s ease;" 
                             onmouseover="this.style.borderColor='#667eea'" 
                             onmouseout="this.style.borderColor='${borderColor}'">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <div style="font-weight: 600; font-size: 14px; color: #333;">
                                    🐍 ${env.name || env.description}
                                    ${isDefault ? '<span style="color: #28a745; font-size: 12px; margin-left: 8px;">✅ 默认</span>' : ''}
                                </div>
                                <button id="${buttonId}" class="btn btn-primary btn-sm" 
                                        onclick="vllmManager.quickActivateEnv('${env.name}', '${buttonId}')">
                                    ⚡ 快速激活
                                </button>
                            </div>
                            <div style="font-size: 12px; color: #666; line-height: 1.4;">
                                ${env.description ? `<div>📝 ${env.description}</div>` : ''}
                                ${env.python_version ? `<div>🐍 Python: ${env.python_version}</div>` : ''}
                                ${env.path ? `<div style="word-break: break-all;">📁 路径: ${env.path}</div>` : ''}
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                
                content.innerHTML = html;
            }

            // 渲染Conda状态
            renderCondaStatus(status) {
                const content = document.getElementById('conda-env-content');
                const currentEnvDiv = document.getElementById('current-conda-env');
                
                // 更新当前环境显示
                if (status.current_env) {
                    currentEnvDiv.innerHTML = `<span style="color: #28a745; font-weight: 600;">✅ ${status.current_env}</span>`;
                    currentEnvDiv.style.background = '#d4edda';
                    currentEnvDiv.style.borderColor = '#28a745';
                } else {
                    currentEnvDiv.innerHTML = '❌ 未激活任何环境';
                    currentEnvDiv.style.background = '#f8d7da';
                    currentEnvDiv.style.borderColor = '#dc3545';
                }
                
                // 获取会话状态信息
                const sessionStatusInfo = this.getSessionStatusInfo(status.session_status);
                
                // 渲染详细状态
                let html = `
                    <div style="padding: 15px; background: ${status.conda_available ? '#d4edda' : '#f8d7da'}; border-radius: 8px; border-left: 4px solid ${status.conda_available ? '#28a745' : '#dc3545'}; margin-bottom: 15px;">
                        <h4 style="margin: 0 0 8px 0; color: ${status.conda_available ? '#28a745' : '#dc3545'};">
                            ${status.conda_available ? '✅' : '❌'} Conda ${status.conda_available ? '可用' : '不可用'}
                        </h4>
                        <div style="font-size: 14px;">
                            <!-- ${status.conda_version ? `版本: ${status.conda_version}` : '未检测到版本信息'} -->
                            状态检查完成
                        </div>
                    </div>
                    
                    <!-- 会话状态信息 -->
                    <div style="padding: 12px; background: ${sessionStatusInfo.bgColor}; border-radius: 8px; border-left: 4px solid ${sessionStatusInfo.borderColor}; margin-bottom: 15px;">
                        <div style="font-weight: 600; margin-bottom: 4px; color: ${sessionStatusInfo.textColor};">
                            ${sessionStatusInfo.icon} ${sessionStatusInfo.title}
                        </div>
                        <div style="font-size: 13px; color: #666;">
                            ${sessionStatusInfo.description}
                        </div>
                    </div>
                    
                    <div style="display: grid; gap: 12px;">
                        <!-- Python路径小卡片已注释掉
                        <div style="padding: 12px; background: white; border-radius: 8px; border: 1px solid #e9ecef;">
                            <div style="font-weight: 600; margin-bottom: 8px;">🐍 当前Python环境</div>
                            <div style="font-size: 13px; color: #666;">
                                <div style="word-break: break-all;">路径: ${status.python_path || 'N/A'}</div>
                            </div>
                        </div>
                        -->
                        
                        <div style="display: grid; gap: 8px;">
                            <div style="padding: 10px; background: #d4edda; border-radius: 6px; border-left: 4px solid #28a745;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span>✅</span>
                                    <div>
                                        <div style="font-weight: 600; font-size: 14px;">📊 总环境数: ${status.total_envs || 0}</div>
                                        <div style="font-size: 12px; color: #155724;">Conda环境总数统计</div>
                                    </div>
                                </div>
                            </div>
                            <div style="padding: 10px; background: ${status.current_env && status.current_env !== '无' ? '#d4edda' : '#f8d7da'}; border-radius: 6px; border-left: 4px solid ${status.current_env && status.current_env !== '无' ? '#28a745' : '#dc3545'};">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span>${status.current_env && status.current_env !== '无' ? '✅' : '❌'}</span>
                                    <div>
                                        <div style="font-weight: 600; font-size: 14px;">🐍 当前激活: ${status.current_env || '无'}</div>
                                        <div style="font-size: 12px; color: ${status.current_env && status.current_env !== '无' ? '#155724' : '#721c24'};">当前激活的Conda环境</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                content.innerHTML = html;
            }
            
            // 获取会话状态信息
            getSessionStatusInfo(sessionStatus) {
                const statusMap = {
                    'persistent_session': {
                        icon: '🔗',
                        title: '持久化会话连接',
                        description: '正在使用持久化会话获取状态，数据与激活环境保持同步',
                        bgColor: '#d1ecf1',
                        borderColor: '#17a2b8',
                        textColor: '#0c5460'
                    },
                    'verified_active': {
                        icon: '✅',
                        title: '会话状态已验证',
                        description: '持久化会话中的环境状态已通过验证，数据准确可靠',
                        bgColor: '#d4edda',
                        borderColor: '#28a745',
                        textColor: '#155724'
                    },
                    'verification_failed': {
                        icon: '⚠️',
                        title: '会话状态验证失败',
                        description: '会话状态与实际环境不符，已清除缓存并重新检测',
                        bgColor: '#fff3cd',
                        borderColor: '#ffc107',
                        textColor: '#856404'
                    },
                    'env_var_detected': {
                        icon: '🔍',
                        title: '通过环境变量检测',
                        description: '在持久化会话中通过CONDA_DEFAULT_ENV环境变量检测到激活环境',
                        bgColor: '#d1ecf1',
                        borderColor: '#17a2b8',
                        textColor: '#0c5460'
                    },
                    'conda_info_detected': {
                        icon: '📊',
                        title: '通过conda info检测',
                        description: '在持久化会话中通过conda info命令检测到激活环境',
                        bgColor: '#d1ecf1',
                        borderColor: '#17a2b8',
                        textColor: '#0c5460'
                    },
                    'python_path_detected': {
                        icon: '🐍',
                        title: '通过Python路径检测',
                        description: '在持久化会话中通过Python可执行文件路径检测到激活环境',
                        bgColor: '#d1ecf1',
                        borderColor: '#17a2b8',
                        textColor: '#0c5460'
                    },
                    'no_env_detected': {
                        icon: '❌',
                        title: '未检测到激活环境',
                        description: '持久化会话中未检测到任何激活的conda环境',
                        bgColor: '#f8d7da',
                        borderColor: '#dc3545',
                        textColor: '#721c24'
                    },
                    'conda_unavailable': {
                        icon: '❌',
                        title: 'Conda不可用',
                        description: '持久化会话中无法访问conda命令',
                        bgColor: '#f8d7da',
                        borderColor: '#dc3545',
                        textColor: '#721c24'
                    },
                    'fallback_ssh': {
                        icon: '🔄',
                        title: '使用临时SSH连接',
                        description: '没有可用的持久化会话，使用临时SSH连接检查状态（可能与激活环境不同步）',
                        bgColor: '#fff3cd',
                        borderColor: '#ffc107',
                        textColor: '#856404'
                    },
                    'no_session': {
                        icon: '⚪',
                        title: '无会话信息',
                        description: '未获取到会话状态信息',
                        bgColor: '#e2e3e5',
                        borderColor: '#6c757d',
                        textColor: '#495057'
                    }
                };
                
                return statusMap[sessionStatus] || statusMap['no_session'];
            }

            // 刷新Conda环境列表
            // 渲染诊断结果
            renderDiagnosis(diagnosis) {
                const content = document.getElementById('diagnosis-content');
                
                const successIcon = diagnosis.success ? '✅' : '❌';
                const successColor = diagnosis.success ? '#28a745' : '#dc3545';
                const bgColor = diagnosis.success ? '#d4edda' : '#f8d7da';
                
                let html = `
                    <div style="padding: 15px; background: ${bgColor}; border-radius: 8px; border-left: 4px solid ${successColor}; margin-bottom: 15px;">
                        <h4 style="margin: 0 0 8px 0; color: ${successColor};">
                            ${successIcon} ${diagnosis.success ? '环境检查通过' : '环境检查发现问题'}
                        </h4>
                        <p style="margin: 0; font-size: 14px;">
                            ${diagnosis.success ? '所有环境检查项目都通过，可以正常运行VLLM服务。' : '发现问题需要解决。'}
                        </p>
                    </div>

                    <div style="display: grid; gap: 10px;">
                `;

                // 检查项目
                const checks = [
                    { key: 'ssh_connection', name: '🔗 SSH连接', desc: diagnosis.ssh_connection ? 'SSH连接正常' : 'SSH连接失败' },
                    { key: 'python_version', name: '🐍 Python环境', desc: diagnosis.python_version ? `Python版本: ${diagnosis.python_version}` : 'Python未安装' },
                    { key: 'vllm_installed', name: '📦 VLLM安装', desc: diagnosis.vllm_installed ? `VLLM版本: ${diagnosis.vllm_version}` : 'VLLM未安装' },
                    { key: 'gpu_available', name: '🎮 GPU可用性', desc: diagnosis.gpu_available ? 'GPU可用' : 'GPU不可用' },
                    { key: 'nvidia_smi', name: '🖥️ NVIDIA驱动', desc: diagnosis.nvidia_smi ? 'nvidia-smi可用' : 'nvidia-smi不可用' }
                ];

                checks.forEach(check => {
                    const status = diagnosis[check.key];
                    const icon = status ? '✅' : '❌';
                    const color = status ? '#28a745' : '#dc3545';
                    const bg = status ? '#d4edda' : '#f8d7da';
                    
                    html += `
                        <div style="padding: 10px; background: ${bg}; border-radius: 6px; border-left: 4px solid ${color};">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span>${icon}</span>
                                <div>
                                    <div style="font-weight: 600; font-size: 14px;">${check.name}</div>
                                    <div style="font-size: 12px; color: #666;">${check.desc}</div>
                                </div>
                            </div>
                        </div>
                    `;
                });

                html += '</div>';
                content.innerHTML = html;
            }

            // 渲染发现的模型
            renderDiscoveredModels(models) {
                const content = document.getElementById('models-content');
                
                if (!models || models.length === 0) {
                    content.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">未发现任何模型</div>';
                    return;
                }

                let html = '<div style="display: grid; gap: 15px;">';
                models.forEach((model, index) => {
                    html += `
                        <div style="padding: 15px; background: white; border-radius: 8px; border: 1px solid #e9ecef;">
                            <div style="font-weight: 600; font-size: 14px; margin-bottom: 8px;">${model.name}</div>
                            <div style="font-size: 12px; color: #666; margin-bottom: 10px; word-break: break-all;">${model.path}</div>
                            <button class="btn btn-success btn-sm" onclick="vllmManager.quickStart('${model.path}', ${8000 + index})">
                                🚀 快速启动
                            </button>
                        </div>
                    `;
                });
                html += '</div>';
                
                content.innerHTML = html;
            }

            // 渲染运行中的服务
            renderRunningServices(services) {
                const content = document.getElementById('status-content');
                
                if (!services || services.length === 0) {
                    content.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">当前没有运行的VLLM服务</div>';
                    return;
                }

                let html = '<div style="display: grid; gap: 15px;">';
                services.forEach(service => {
                    html += `
                        <div style="padding: 15px; background: white; border-radius: 8px; border: 1px solid #e9ecef;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <div>
                                    <div style="font-weight: 600; font-size: 14px;">端口: ${service.port}</div>
                                    <div style="font-size: 12px; color: #666;">PID: ${service.pid} | CPU: ${service.cpu || 'N/A'}% | 内存: ${service.memory || 'N/A'}%</div>
                                </div>
                                <div class="status-indicator status-running">● 运行中</div>
                            </div>
                            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                                <button class="btn btn-primary btn-sm" onclick="vllmManager.viewServiceLogs(${service.port})">
                                    📄 查看日志
                                </button>
                                <button class="btn btn-danger btn-sm" onclick="vllmManager.stopService(${service.pid}, ${service.port})">
                                    ⏹️ 停止服务
                                </button>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                
                content.innerHTML = html;
            }

            // 渲染性能数据
            renderPerformanceData(perfData) {
                const content = document.getElementById('performance-content');
                const timestamp = new Date(perfData.timestamp).toLocaleString();
                
                let html = `
                    <div style="text-align: right; font-size: 12px; color: #666; margin-bottom: 15px;">
                        更新时间: ${timestamp}
                    </div>
                `;

                // GPU信息
                if (perfData.gpu_metrics && perfData.gpu_metrics.length > 0) {
                    html += '<h4 style="margin: 0 0 10px 0; color: #333;">🎮 GPU使用情况</h4>';
                    html += '<div style="display: grid; gap: 10px; margin-bottom: 20px;">';
                    
                    perfData.gpu_metrics.forEach(gpu => {
                        const memPercent = ((gpu.memory_used / gpu.memory_total) * 100).toFixed(1);
                        html += `
                            <div style="padding: 12px; border: 1px solid #ddd; border-radius: 6px; background: white;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                    <strong>GPU ${gpu.gpu_id}</strong>
                                    <span>${gpu.temperature}°C</span>
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 13px;">
                                    <div>
                                        <div>利用率: ${gpu.utilization}%</div>
                                        <div style="width: 100%; height: 4px; background: #e9ecef; border-radius: 2px; overflow: hidden;">
                                            <div style="width: ${gpu.utilization}%; height: 100%; background: ${gpu.utilization > 80 ? '#dc3545' : gpu.utilization > 50 ? '#ffc107' : '#28a745'};"></div>
                                        </div>
                                    </div>
                                    <div>
                                        <div>显存: ${gpu.memory_used}MB/${gpu.memory_total}MB (${memPercent}%)</div>
                                        <div style="width: 100%; height: 4px; background: #e9ecef; border-radius: 2px; overflow: hidden;">
                                            <div style="width: ${memPercent}%; height: 100%; background: ${memPercent > 80 ? '#dc3545' : memPercent > 60 ? '#ffc107' : '#28a745'};"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    html += '</div>';
                }

                // 系统信息
                html += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">';
                
                // 系统负载
                html += `
                    <div style="padding: 12px; border: 1px solid #ddd; border-radius: 6px; background: white;">
                        <h5 style="margin: 0 0 8px 0;">💻 系统负载</h5>
                        <div style="font-size: 13px;">
                            <div>1分钟: ${perfData.load_average[0]}</div>
                            <div>5分钟: ${perfData.load_average[1]}</div>
                            <div>15分钟: ${perfData.load_average[2]}</div>
                        </div>
                    </div>
                `;

                // 内存使用
                const memUsedPercent = ((perfData.memory.used / perfData.memory.total) * 100).toFixed(1);
                html += `
                    <div style="padding: 12px; border: 1px solid #ddd; border-radius: 6px; background: white;">
                        <h5 style="margin: 0 0 8px 0;">🧠 系统内存</h5>
                        <div style="font-size: 13px;">
                            <div>已用: ${perfData.memory.used}MB</div>
                            <div>总计: ${perfData.memory.total}MB</div>
                            <div>可用: ${perfData.memory.available}MB</div>
                            <div style="margin-top: 5px;">使用率: ${memUsedPercent}%</div>
                            <div style="width: 100%; height: 4px; background: #e9ecef; border-radius: 2px; margin-top: 2px; overflow: hidden;">
                                <div style="width: ${memUsedPercent}%; height: 100%; background: ${memUsedPercent > 80 ? '#dc3545' : memUsedPercent > 60 ? '#ffc107' : '#28a745'};"></div>
                            </div>
                        </div>
                    </div>
                `;

                html += '</div>';
                content.innerHTML = html;
            }

            // 快速启动
            quickStart(modelPath, port) {
                document.getElementById('model-path').value = modelPath;
                document.getElementById('service-port').value = port;
                
                if (confirm(`🚀 即将快速启动模型服务:\n📁 模型: ${modelPath}\n🌐 端口: ${port}\n\n是否使用默认参数启动？`)) {
                    this.startService();
                }
            }

            // 查看服务日志（快捷方式）
            viewServiceLogs(port) {
                document.getElementById('log-port').value = port;
                this.viewLogs();
            }

            // 工具方法
            getLoadingHTML(message, subtitle = '') {
                return `
                    <div class="loading">
                        <div class="loading-spinner"></div>
                        <div class="loading-text">${message}</div>
                        ${subtitle ? `<div class="loading-subtitle">${subtitle}</div>` : ''}
                    </div>
                `;
            }

            getErrorHTML(message) {
                return `<div class="error-message">${message}</div>`;
            }

            escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
        }

        // 初始化管理器
        const vllmManager = new VLLMManager();
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', () => {
            console.log('📄 DOM加载完成，开始初始化VLLM管理器...');
            vllmManager.init();
        });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)