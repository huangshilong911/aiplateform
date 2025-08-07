"""Web SSH终端页面"""

from fastapi.responses import HTMLResponse

def terminal_page():
    """Web SSH终端页面"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SSH远程终端 - AI平台管理系统</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css" />
        <link rel="stylesheet" href="/static/css/terminal.css">
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 SSH远程终端</h1>
                <div class="controls">
                    <select id="server-select" class="server-select">
                        <option value="">选择服务器...</option>
                    </select>
                    <button id="connect-btn" class="btn btn-success">连接</button>
                    <button id="disconnect-btn" class="btn btn-danger" disabled>断开</button>
                    <button id="clear-btn" class="btn btn-primary">清屏</button>
                    <a href="/dashboard" class="btn btn-primary">返回控制台</a>
                </div>
            </div>
            
            <div class="terminal-container">
                <div id="status" class="status">未连接</div>
                <div id="terminal">
                    <div class="loading">请选择服务器并点击连接...</div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"></script>
        <script src="/static/js/terminal.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content) 