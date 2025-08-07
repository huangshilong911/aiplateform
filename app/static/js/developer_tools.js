class DeveloperTools {
    constructor() {
        this.init();
    }
    
    init() {
        this.checkAllStatus();
        // 每3秒自动刷新状态
        setInterval(() => this.checkAllStatus(), 3000);
    }
    
    async checkAllStatus() {
        await Promise.all([
            this.checkHealthStatus(),
            this.checkApiResponse(),
            this.checkServerConnections(),
            this.checkGpuMonitoring(),
            this.checkModelServices(),
            this.checkApiEndpoints()
        ]);
    }
    
    async checkHealthStatus() {
        try {
            const response = await fetch('/health');
            const data = await response.json();
            const indicator = document.getElementById('health-indicator');
            const details = document.getElementById('health-details');
            
            if (response.ok && data.status === 'healthy') {
                indicator.textContent = '✅ 正常';
                indicator.className = 'status-value healthy';
                details.textContent = `数据库: ${data.database}, 配置: ${data.config}`;
            } else {
                indicator.textContent = '❌ 异常';
                indicator.className = 'status-value error';
                details.textContent = '系统健康检查失败，请查看详细日志';
            }
        } catch (error) {
            const indicator = document.getElementById('health-indicator');
            const details = document.getElementById('health-details');
            indicator.textContent = '❌ 无法连接';
            indicator.className = 'status-value error';
            details.textContent = '无法连接到健康检查端点';
        }
    }
    
    async checkApiResponse() {
        try {
            const start = Date.now();
            const response = await fetch('/api/system/current');
            const responseTime = Date.now() - start;
            const indicator = document.getElementById('api-indicator');
            const details = document.getElementById('api-details');
            
            if (response.ok) {
                if (responseTime < 500) {
                    indicator.textContent = `✅ ${responseTime}ms`;
                    indicator.className = 'status-value healthy';
                    details.textContent = 'API响应速度很快';
                } else if (responseTime < 2000) {
                    indicator.textContent = `⚠️ ${responseTime}ms`;
                    indicator.className = 'status-value warning';
                    details.textContent = 'API响应稍慢，但在可接受范围内';
                } else {
                    indicator.textContent = `⚠️ ${responseTime}ms`;
                    indicator.className = 'status-value warning';
                    details.textContent = 'API响应较慢，可能影响用户体验';
                }
            } else {
                indicator.textContent = '❌ 错误';
                indicator.className = 'status-value error';
                details.textContent = `HTTP ${response.status} - API请求失败`;
            }
        } catch (error) {
            const indicator = document.getElementById('api-indicator');
            const details = document.getElementById('api-details');
            indicator.textContent = '❌ 超时';
            indicator.className = 'status-value error';
            details.textContent = 'API请求超时或网络错误';
        }
    }
    
    async checkServerConnections() {
        try {
            const response = await fetch('/api/system/current');
            const data = await response.json();
            const indicator = document.getElementById('server-indicator');
            const details = document.getElementById('server-details');
            
            if (response.ok && data.success) {
                const servers = data.data || [];
                
                if (servers.length === 0) {
                    indicator.textContent = '⚠️ 无数据';
                    indicator.className = 'status-value warning';
                    details.textContent = '系统监控服务未收集到数据，请检查监控服务状态';
                } else {
                    const onlineCount = servers.filter(s => s.server_status === 'online').length;
                    const totalCount = servers.length;
                    
                    if (onlineCount === totalCount) {
                        indicator.textContent = `✅ ${onlineCount}/${totalCount}`;
                        indicator.className = 'status-value healthy';
                        details.textContent = '所有GPU服务器连接正常';
                    } else if (onlineCount > 0) {
                        indicator.textContent = `⚠️ ${onlineCount}/${totalCount}`;
                        indicator.className = 'status-value warning';
                        details.textContent = `部分GPU服务器离线，${totalCount - onlineCount}台无法连接`;
                    } else {
                        indicator.textContent = `❌ 0/${totalCount}`;
                        indicator.className = 'status-value error';
                        details.textContent = '所有GPU服务器均无法连接，请检查SSH连接和监控服务';
                    }
                }
            } else {
                indicator.textContent = '❌ 未知';
                indicator.className = 'status-value error';
                details.textContent = '无法获取服务器连接状态，API响应异常';
            }
        } catch (error) {
            const indicator = document.getElementById('server-indicator');
            const details = document.getElementById('server-details');
            indicator.textContent = '❌ 检查失败';
            indicator.className = 'status-value error';
            details.textContent = '服务器连接检查失败，请检查网络连接和API服务';
        }
    }
    
    async checkGpuMonitoring() {
        try {
            const response = await fetch('/api/gpu/current');
            const indicator = document.getElementById('gpu-indicator');
            const details = document.getElementById('gpu-details');
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    const gpuCount = data.data ? data.data.length : 0;
                    indicator.textContent = `✅ ${gpuCount} GPU`;
                    indicator.className = 'status-value healthy';
                    details.textContent = `GPU监控服务正常，监控到 ${gpuCount} 个GPU设备`;
                } else {
                    indicator.textContent = '⚠️ 异常';
                    indicator.className = 'status-value warning';
                    details.textContent = 'GPU监控服务响应异常';
                }
            } else {
                indicator.textContent = '❌ 错误';
                indicator.className = 'status-value error';
                details.textContent = 'GPU监控API请求失败';
            }
        } catch (error) {
            const indicator = document.getElementById('gpu-indicator');
            const details = document.getElementById('gpu-details');
            indicator.textContent = '❌ 服务异常';
            indicator.className = 'status-value error';
            details.textContent = 'GPU监控服务不可用';
        }
    }
    
    async checkModelServices() {
        try {
            const response = await fetch('/api/models/');
            const indicator = document.getElementById('model-indicator');
            const details = document.getElementById('model-details');
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    const models = data.data || [];
                    const runningCount = models.filter(m => m.status === 'RUNNING').length;
                    indicator.textContent = `✅ ${runningCount}/${models.length}`;
                    indicator.className = 'status-value healthy';
                    details.textContent = `模型管理服务正常，${runningCount} 个模型正在运行`;
                } else {
                    indicator.textContent = '⚠️ 异常';
                    indicator.className = 'status-value warning';
                    details.textContent = '模型管理服务响应异常';
                }
            } else {
                indicator.textContent = '❌ 错误';
                indicator.className = 'status-value error';
                details.textContent = '模型管理API请求失败';
            }
        } catch (error) {
            const indicator = document.getElementById('model-indicator');
            const details = document.getElementById('model-details');
            indicator.textContent = '❌ 服务异常';
            indicator.className = 'status-value error';
            details.textContent = '模型管理服务不可用';
        }
    }
    
    async checkApiEndpoints() {
        // 检查各个API端点状态并更新工具状态
        const endpoints = [
            { id: 'gpu-status', url: '/api/gpu/current' },
            { id: 'system-status', url: '/api/system/current' },
            { id: 'models-status', url: '/api/models/' },
            { id: 'dashboard-status', url: '/api/dashboard' },
            { id: 'health-status', url: '/health' },
            { id: 'config-status', url: '/api/config/servers' }
        ];
        
        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint.url);
                const element = document.getElementById(endpoint.id);
                if (element) {
                    if (response.ok) {
                        element.textContent = '正常';
                        element.className = 'tool-status status-online';
                    } else {
                        element.textContent = '异常';
                        element.className = 'tool-status status-error';
                    }
                }
            } catch (error) {
                const element = document.getElementById(endpoint.id);
                if (element) {
                    element.textContent = '错误';
                    element.className = 'tool-status status-error';
                }
            }
        }
        
        // 检查数据库状态（通过健康检查）
        try {
            const response = await fetch('/health');
            const data = await response.json();
            const dbIndicator = document.getElementById('db-indicator');
            const dbDetails = document.getElementById('db-details');
            
            if (response.ok && data.database === 'ok') {
                dbIndicator.textContent = '✅ 正常';
                dbIndicator.className = 'status-value healthy';
                dbDetails.textContent = '数据库连接正常，读写操作正常';
            } else {
                dbIndicator.textContent = '❌ 异常';
                dbIndicator.className = 'status-value error';
                dbDetails.textContent = `数据库状态异常: ${data.database}`;
            }
        } catch (error) {
            const dbIndicator = document.getElementById('db-indicator');
            const dbDetails = document.getElementById('db-details');
            dbIndicator.textContent = '❌ 无法检查';
            dbIndicator.className = 'status-value error';
            dbDetails.textContent = '无法检查数据库状态';
        }
    }
}

// 页面切换功能
function showPage(pageNum) {
    if (pageNum === 0) {
        // 跳转到系统监控页面
        window.location.href = '/';
    } else if (pageNum === 1) {
        // 跳转到控制台页面
        window.location.href = '/dashboard';
    } else if (pageNum === 2) {
        // 当前就是开发者工具页面，不需要切换
        return;
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

// 手动刷新状态
function refreshStatus() {
    if (window.developerTools) {
        window.developerTools.checkAllStatus();
    }
}

// 初始化开发者工具
window.developerTools = new DeveloperTools(); 