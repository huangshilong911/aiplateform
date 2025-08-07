class EnhancedSystemMonitor {
    constructor() {
        this.autoRefreshEnabled = true;
        this.refreshInterval = null;
        this.apiBase = '';
        this.init();
    }
    
    init() {
        this.setupAutoRefresh();
        this.loadData();
    }
    
    setupAutoRefresh() {
        const checkbox = document.getElementById('autoRefresh');
        checkbox.addEventListener('change', (e) => {
            this.autoRefreshEnabled = e.target.checked;
            if (this.autoRefreshEnabled) {
                this.startAutoRefresh();
            } else {
                this.stopAutoRefresh();
            }
        });
        
        if (this.autoRefreshEnabled) {
            this.startAutoRefresh();
        }
    }
    
    startAutoRefresh() {
        this.stopAutoRefresh();
        this.refreshInterval = setInterval(() => {
            this.loadData();
        }, 3000); // 3秒刷新一次
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    async loadData() {
        try {
            // 并行加载系统数据和token统计数据
            const [systemResponse, tokenResponse] = await Promise.all([
                fetch('/api/system/current'),
                fetch('/api/models/stats/tokens')
            ]);
            
            const systemData = await systemResponse.json();
            const tokenData = await tokenResponse.json();
            
            if (systemData.success) {
                this.renderSystemData(systemData.data);
            } else {
                this.renderError('系统数据获取失败: ' + (systemData.message || '未知错误'));
            }
            
            if (tokenData.success) {
                this.renderTokenStats(tokenData.data);
            } else {
                this.renderTokenError('Token数据获取失败: ' + (tokenData.message || '未知错误'));
            }
        } catch (error) {
            console.error('数据加载失败:', error);
            this.renderError('数据加载失败: ' + error.message);
        }
    }
    
    renderSystemData(systemData) {
        this.renderSystemMetrics(systemData);
        this.renderSystemServers(systemData);
    }
    
    renderSystemMetrics(systemData) {
        const container = document.getElementById('system-metrics');
        if (!container) return;
        
        // 计算总体指标
        const totalServers = systemData?.length || 0;
        const onlineServers = systemData?.filter(s => this.isServerOnline(s)).length || 0;
        const avgCpuUsage = totalServers > 0 ? 
            systemData.reduce((sum, s) => sum + (s.cpu_usage || 0), 0) / totalServers : 0;
        const avgMemoryUsage = totalServers > 0 ?
            systemData.reduce((sum, s) => sum + (s.memory_percent || 0), 0) / totalServers : 0;

        // 计算GPU相关指标
        const totalGPUs = systemData.reduce((sum, s) => sum + (s.gpu_summary?.total_gpus || 0), 0);
        const availableGPUs = systemData.reduce((sum, s) => sum + (s.gpu_summary?.available_gpus || 0), 0);
        const busyGPUs = systemData.reduce((sum, s) => sum + (s.gpu_summary?.busy_gpus || 0), 0);
        const avgGpuUsage = totalServers > 0 ?
            systemData.reduce((sum, s) => sum + (s.gpu_summary?.avg_gpu_utilization || 0), 0) / totalServers : 0;
        const avgGpuMemoryUsage = totalServers > 0 ?
            systemData.reduce((sum, s) => sum + (s.gpu_summary?.avg_memory_utilization || 0), 0) / totalServers : 0;
        const totalGpuMemory = systemData.reduce((sum, s) => sum + (s.gpu_summary?.total_gpu_memory || 0), 0);
        const usedGpuMemory = systemData.reduce((sum, s) => sum + (s.gpu_summary?.used_gpu_memory || 0), 0);
        
        // 计算磁盘使用率
        const avgDiskUsage = totalServers > 0 ?
            systemData.reduce((sum, s) => sum + (s.disk_percent || 0), 0) / totalServers : 0;

        container.innerHTML = `
            <div class="system-metrics-grid">
                <div class="metric-group">
                    <h4>服务器状态</h4>
                    <div class="metric-row">
                        <div class="system-metric">
                            <span class="system-metric-value">${totalServers}</span>
                            <span class="system-metric-label">总服务器数</span>
                </div>
                        <div class="system-metric">
                            <span class="system-metric-value">${onlineServers}</span>
                            <span class="system-metric-label">在线服务器</span>
                        </div>
                </div>
            </div>
            
                <div class="metric-group">
                    <h4>系统资源</h4>
                    <div class="metric-row">
                        <div class="system-metric">
                            <span class="system-metric-value">${avgCpuUsage.toFixed(1)}%</span>
                            <span class="system-metric-label">平均CPU使用率</span>
                </div>
                        <div class="system-metric">
                            <span class="system-metric-value">${avgMemoryUsage.toFixed(1)}%</span>
                            <span class="system-metric-label">平均内存使用率</span>
                        </div>
                        <div class="system-metric">
                            <span class="system-metric-value">${avgDiskUsage.toFixed(1)}%</span>
                            <span class="system-metric-label">平均磁盘使用率</span>
                        </div>
                </div>
            </div>
            
                <div class="metric-group">
                    <h4>GPU资源</h4>
                    <div class="metric-row">
                        <div class="system-metric">
                            <span class="system-metric-value">${totalGPUs}</span>
                            <span class="system-metric-label">总GPU数量</span>
                </div>
                        <div class="system-metric">
                            <span class="system-metric-value">${availableGPUs}</span>
                            <span class="system-metric-label">可用GPU</span>
            </div>
                        <div class="system-metric">
                            <span class="system-metric-value">${busyGPUs}</span>
                            <span class="system-metric-label">忙碌GPU</span>
        </div>
        </div>
                            <div class="metric-row">
                                <div class="system-metric">
                                    <span class="system-metric-value">${avgGpuUsage.toFixed(1)}%</span>
                                    <span class="system-metric-label">平均GPU使用率</span>
                                </div>
                                <div class="system-metric">
                                    <span class="system-metric-value">${avgGpuMemoryUsage.toFixed(1)}%</span>
                                    <span class="system-metric-label">平均显存使用率</span>
                                </div>
                                <div class="system-metric">
                                    <span class="system-metric-value">${this.formatMemorySize(usedGpuMemory)}/${this.formatMemorySize(totalGpuMemory)}</span>
                                    <span class="system-metric-label">显存使用情况</span>
                                </div>
                            </div>
                        </div>
    </div>
        `;
    }
    
    renderSystemServers(systemData) {
        const container = document.getElementById('system-servers');
        if (!container) return;
        
        if (!systemData || systemData.length === 0) {
            container.innerHTML = '<div class="alert alert-info">暂无系统数据</div>';
            return;
        }
        
        container.innerHTML = systemData.map(server => this.renderServerItem(server)).join('');
    }
    
    renderServerItem(server) {
        const isOnline = this.isServerOnline(server);
        const cpuPercent = server.cpu_usage || 0;
        const memoryPercent = server.memory_percent || 0;
        const diskPercent = server.disk_percent || 0;
        
        // GPU汇总信息
        const gpuSummary = server.gpu_summary || {};
        const totalGpus = gpuSummary.total_gpus || 0;
        const availableGpus = gpuSummary.available_gpus || 0;
        const avgGpuUtil = gpuSummary.avg_gpu_utilization || 0;
        const avgGpuMemUtil = gpuSummary.avg_memory_utilization || 0;
        const maxTemp = gpuSummary.max_temperature || 0;
        const totalPower = gpuSummary.total_power_draw || 0;

        return `
            <div class="server-item-enhanced">
                <div class="server-header">
                    <div class="server-name">
                        <span class="status-indicator ${isOnline ? 'online' : 'offline'}"></span>
                        <h3>${server.server_name || '未知服务器'}</h3>
                        <span class="server-status-text ${isOnline ? 'online' : 'offline'}">
                            ${isOnline ? '在线' : '离线'}
                        </span>
                    </div>
                    <div class="server-info">
                        <div class="info-item">
                            <span class="info-label">系统负载:</span>
                            <span class="info-value">${this.formatLoadAverage(server.load_average)}</span>
                </div>
                        <div class="info-item">
                            <span class="info-label">运行时间:</span>
                            <span class="info-value">${this.formatUptime(server.uptime)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">进程数:</span>
                            <span class="info-value">${server.process_count || 'N/A'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="server-metrics">
                    <div class="metrics-section">
                        <h4>系统资源</h4>
                        <div class="metrics-grid">
                            <div class="metric-item">
                                <div class="metric-header">
                                    <span class="metric-label">CPU</span>
                                    <span class="metric-value">${cpuPercent.toFixed(1)}%</span>
                    </div>
                                <div class="progress">
                                    <div class="progress-bar cpu" style="width: ${cpuPercent}%"></div>
                    </div>
                    </div>
                            <div class="metric-item">
                                <div class="metric-header">
                                    <span class="metric-label">内存</span>
                                    <span class="metric-value">${memoryPercent.toFixed(1)}%</span>
                    </div>
                                <div class="progress">
                                    <div class="progress-bar memory" style="width: ${memoryPercent}%"></div>
                </div>
                                <div class="metric-detail">
                                    ${this.formatMemorySize(server.memory_used)}/${this.formatMemorySize(server.memory_total)}
                    </div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-header">
                                    <span class="metric-label">磁盘</span>
                                    <span class="metric-value">${diskPercent.toFixed(1)}%</span>
                                </div>
                                <div class="progress">
                                    <div class="progress-bar disk" style="width: ${diskPercent}%"></div>
                                </div>
                                <div class="metric-detail">
                                    ${this.formatMemorySize(server.disk_used * 1024)}/${this.formatMemorySize(server.disk_total * 1024)}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    ${totalGpus > 0 ? `
                    <div class="metrics-section">
                        <h4>GPU资源 (${totalGpus}个GPU)</h4>
                        <div class="metrics-grid">
                            <div class="metric-item">
                                <div class="metric-header">
                                    <span class="metric-label">GPU使用率</span>
                                    <span class="metric-value">${avgGpuUtil.toFixed(1)}%</span>
                                </div>
                                <div class="progress">
                                    <div class="progress-bar gpu" style="width: ${avgGpuUtil}%"></div>
                                </div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-header">
                                    <span class="metric-label">显存使用率</span>
                                    <span class="metric-value">${avgGpuMemUtil.toFixed(1)}%</span>
                                </div>
                                <div class="progress">
                                    <div class="progress-bar gpu-memory" style="width: ${avgGpuMemUtil}%"></div>
                                </div>
                                <div class="metric-detail">
                                    ${this.formatMemorySize(gpuSummary.used_gpu_memory)}/${this.formatMemorySize(gpuSummary.total_gpu_memory)}
                                </div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-header">
                                    <span class="metric-label">状态</span>
                                    <span class="metric-value">${availableGpus}/${totalGpus} 可用</span>
                                </div>
                                <div class="gpu-status-detail">
                                    <span class="status-chip available">可用: ${availableGpus}</span>
                                    <span class="status-chip busy">忙碌: ${gpuSummary.busy_gpus || 0}</span>
                                </div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-header">
                                    <span class="metric-label">温度/功耗</span>
                                    <span class="metric-value">${maxTemp}°C / ${totalPower.toFixed(0)}W</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    ` : '<div class="no-gpu-message">此服务器无GPU资源</div>'}
                </div>
            </div>
        `;
    }
    
    isServerOnline(server) {
        // 检查服务器是否在线：基于server_status或有效的系统数据
        if (server.server_status === 'online' || server.status === 'online') {
            return true;
        }
        
        // 检查是否有有效的系统资源数据
        const hasValidCpu = server.cpu_usage !== null && server.cpu_usage !== undefined;
        const hasValidMemory = server.memory_percent !== null && server.memory_percent !== undefined;
        
        return hasValidCpu || hasValidMemory;
    }
    
    formatLoadAverage(loadAverage) {
        if (!loadAverage) return '0.00';
        
        if (typeof loadAverage === 'string') {
            const parts = loadAverage.split(',');
            if (parts.length > 0) {
                const firstLoad = parseFloat(parts[0].trim());
                return isNaN(firstLoad) ? '0.00' : firstLoad.toFixed(2);
            }
        }
        
        if (Array.isArray(loadAverage) && loadAverage.length > 0) {
            const firstLoad = parseFloat(loadAverage[0]);
            return isNaN(firstLoad) ? '0.00' : firstLoad.toFixed(2);
        }
        
        if (typeof loadAverage === 'number') {
            return loadAverage.toFixed(2);
        }
        
        return '0.00';
    }
    
    formatMemorySize(sizeInMB) {
        if (!sizeInMB || sizeInMB === 0) return '0MB';
        
        if (sizeInMB >= 1024) {
            return (sizeInMB / 1024).toFixed(1) + 'GB';
        }
        return sizeInMB.toFixed(0) + 'MB';
    }
    
    formatUptime(uptimeSeconds) {
        if (!uptimeSeconds) return 'N/A';
        
        const days = Math.floor(uptimeSeconds / (24 * 3600));
        const hours = Math.floor((uptimeSeconds % (24 * 3600)) / 3600);
        const minutes = Math.floor((uptimeSeconds % 3600) / 60);
        
        if (days > 0) {
            return `${days}天${hours}小时`;
        } else if (hours > 0) {
            return `${hours}小时${minutes}分钟`;
        } else {
            return `${minutes}分钟`;
        }
    }
    
    renderTokenStats(tokenData) {
        const container = document.getElementById('token-stats');
        if (!container) return;

        const overview = tokenData.overview || {};
        const byServer = tokenData.by_server || {};
        const byType = tokenData.by_type || {};
        const topModels = tokenData.top_models || [];

        container.innerHTML = `
            <div class="token-stats-grid">
                <div class="token-metric-group">
                    <h4>总体统计</h4>
                    <div class="token-metric-row">
                        <div class="token-metric">
                            <span class="token-metric-value">${overview.total_running_models || 0}</span>
                            <span class="token-metric-label">运行中模型</span>
                        </div>
                        <div class="token-metric">
                            <span class="token-metric-value">${this.formatNumber(overview.total_tokens || 0)}</span>
                            <span class="token-metric-label">总Token数</span>
                        </div>
                        <div class="token-metric">
                            <span class="token-metric-value">${this.formatNumber(overview.total_requests || 0)}</span>
                            <span class="token-metric-label">总请求数</span>
                        </div>
                        <div class="token-metric">
                            <span class="token-metric-value">${overview.avg_tokens_per_request || 0}</span>
                            <span class="token-metric-label">平均Token/请求</span>
                        </div>
                    </div>
                </div>
                
                <div class="token-metric-group">
                    <h4>按服务器统计</h4>
                    <div class="token-metric-row">
                        ${Object.keys(byServer).map(serverName => {
                            const serverData = byServer[serverName];
                            return `
                                <div class="token-metric">
                                    <span class="token-metric-value">${this.formatNumber(serverData.total_tokens || 0)}</span>
                                    <span class="token-metric-label">${serverName}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
                
                <div class="token-metric-group">
                    <h4>最活跃模型 (Top 5)</h4>
                    <div class="top-models-list">
                        ${topModels.length > 0 ? topModels.map(model => `
                            <div class="top-model-item">
                                <div class="model-info">
                                    <div class="model-name">${model.name}</div>
                                    <div class="model-details">
                                        ${model.server_name} | ${model.model_type || 'Unknown'}
                                    </div>
                                </div>
                                <div class="model-stats">
                                    <div class="token-count">${this.formatNumber(model.total_tokens)} tokens</div>
                                    <div>${model.total_requests} 请求</div>
                                </div>
                            </div>
                        `).join('') : '<div class="alert alert-info">暂无运行中的模型</div>'}
                    </div>
                </div>
            </div>
        `;
    }
    
    renderTokenError(message) {
        const container = document.getElementById('token-stats');
        if (container) {
            container.innerHTML = `<div class="alert alert-error">${message}</div>`;
        }
    }
    
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
    
    renderError(message) {
        const metricsContainer = document.getElementById('system-metrics');
        const serversContainer = document.getElementById('system-servers');
        
        if (metricsContainer) {
            metricsContainer.innerHTML = `<div class="alert alert-error">${message}</div>`;
        }
        
        if (serversContainer) {
            serversContainer.innerHTML = `<div class="alert alert-error">${message}</div>`;
        }
    }
}

// 页面切换功能
function showPage(pageNum) {
    if (pageNum === 0) {
        // 当前就是页面0，不需要切换
        return;
    } else if (pageNum === 1) {
        // 跳转到控制台页面
        window.location.href = '/dashboard';
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

// 手动刷新数据
function refreshData() {
    if (window.systemMonitor) {
        window.systemMonitor.loadData();
    }
}

// 初始化系统监控
window.systemMonitor = new EnhancedSystemMonitor(); 