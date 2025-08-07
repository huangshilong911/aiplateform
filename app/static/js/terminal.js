class WebSSHTerminal {
    constructor() {
        this.terminal = null;
        this.websocket = null;
        this.fitAddon = null;
        this.connected = false;
        this.currentServer = null;
        
        this.init();
    }
    
    init() {
        this.loadServerList();
        this.setupEventListeners();
        this.initTerminal();
    }
    
    async loadServerList() {
        try {
            const response = await fetch('/api/config/servers');
            const data = await response.json();
            
            if (data.success) {
                const serverSelect = document.getElementById('server-select');
                serverSelect.innerHTML = '<option value="">选择服务器...</option>';
                
                data.data.forEach(server => {
                    if (server.enabled) {
                        const option = document.createElement('option');
                        option.value = server.name;
                        option.textContent = `${server.name} (${server.host}:${server.port})`;
                        serverSelect.appendChild(option);
                    }
                });
            }
        } catch (error) {
            console.error('加载服务器列表失败:', error);
            this.updateStatus('加载服务器列表失败', 'error');
        }
    }
    
    setupEventListeners() {
        document.getElementById('connect-btn').addEventListener('click', () => this.connect());
        document.getElementById('disconnect-btn').addEventListener('click', () => this.disconnect());
        document.getElementById('clear-btn').addEventListener('click', () => this.clearTerminal());
        
        window.addEventListener('resize', () => {
            if (this.fitAddon) {
                this.fitAddon.fit();
                this.sendResize();
            }
        });
        
        window.addEventListener('beforeunload', () => {
            if (this.websocket) {
                this.websocket.close();
            }
        });
    }
    
    initTerminal() {
        this.terminal = new Terminal({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: 'Consolas, Monaco, "Courier New", monospace',
            theme: {
                background: '#000000',
                foreground: '#ffffff',
                cursor: '#ffffff',
                selection: '#4d4d4d'
            },
            allowTransparency: false,
            rows: 24,
            cols: 80
        });
        
        this.fitAddon = new FitAddon.FitAddon();
        this.terminal.loadAddon(this.fitAddon);
        
        const terminalElement = document.getElementById('terminal');
        terminalElement.innerHTML = '';
        this.terminal.open(terminalElement);
        this.fitAddon.fit();
        
        // 处理终端输入
        this.terminal.onData(data => {
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send(JSON.stringify({
                    type: 'input',
                    data: data
                }));
            }
        });
        
        this.terminal.writeln('欢迎使用SSH远程终端');
        this.terminal.writeln('请选择服务器并点击连接...');
    }
    
    connect() {
        const serverSelect = document.getElementById('server-select');
        const serverName = serverSelect.value;
        
        if (!serverName) {
            alert('请先选择服务器');
            return;
        }
        
        if (this.connected) {
            this.disconnect();
        }
        
        this.currentServer = serverName;
        this.updateStatus('正在连接...', 'connecting');
        
        // WebSocket连接
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/terminal/${encodeURIComponent(serverName)}`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            this.connected = true;
            this.updateStatus(`已连接到 ${serverName}`, 'connected');
            this.updateButtons();
            this.terminal.clear();
            this.sendResize();
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'output') {
                    this.terminal.write(data.data);
                } else if (data.type === 'connected') {
                    this.terminal.write(data.message);
                } else if (data.type === 'error') {
                    this.terminal.write(`\\r\\n\\x1b[31m${data.message}\\x1b[0m\\r\\n`);
                }
            } catch (error) {
                console.error('处理WebSocket消息错误:', error);
            }
        };
        
        this.websocket.onclose = (event) => {
            this.connected = false;
            this.updateButtons();
            
            if (event.code === 4000) {
                this.updateStatus('服务器不存在', 'error');
            } else if (event.code === 4001) {
                this.updateStatus('服务器未启用', 'error');
            } else if (event.code === 4002) {
                this.updateStatus(`连接错误: ${event.reason}`, 'error');
            } else {
                this.updateStatus('连接已断开', 'error');
            }
            
            this.terminal.write('\\r\\n\\x1b[31m连接已断开\\x1b[0m\\r\\n');
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket错误:', error);
            this.updateStatus('连接错误', 'error');
        };
    }
    
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        this.connected = false;
        this.updateStatus('未连接', '');
        this.updateButtons();
    }
    
    clearTerminal() {
        if (this.terminal) {
            this.terminal.clear();
        }
    }
    
    sendResize() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN && this.terminal) {
            this.websocket.send(JSON.stringify({
                type: 'resize',
                cols: this.terminal.cols,
                rows: this.terminal.rows
            }));
        }
    }
    
    updateStatus(message, type = '') {
        const statusElement = document.getElementById('status');
        statusElement.textContent = message;
        statusElement.className = `status ${type}`;
    }
    
    updateButtons() {
        const connectBtn = document.getElementById('connect-btn');
        const disconnectBtn = document.getElementById('disconnect-btn');
        
        connectBtn.disabled = this.connected;
        disconnectBtn.disabled = !this.connected;
    }
}

// 初始化终端
const terminal = new WebSSHTerminal(); 