// AI平台管理系统 - 仪表板JavaScript

class AIPlatformDashboard {
    constructor() {
        this.apiBase = '';
        this.updateInterval = 3000; // 3秒更新间隔
        this.updateTimers = {};
        this.sshTerminalHistory = [];
        this.isEditMode = false; // 跟踪是否为编辑模式
        this.editingServerName = null; // 当前编辑的服务器名称
        
        // WebSocket终端相关
        this.webTerminal = null;
        this.webTerminalWS = null;
        this.webTerminalFitAddon = null;
        this.webTerminalConnected = false;
        this.currentServerName = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // 刷新按钮
        document.getElementById('refresh-gpu')?.addEventListener('click', () => this.loadGPUData());
        document.getElementById('refresh-models')?.addEventListener('click', () => this.loadModelsData());
        document.getElementById('refresh-system')?.addEventListener('click', () => {
            this.loadSystemData();
            this.loadTokenStats();
        });
        document.getElementById('refresh-config')?.addEventListener('click', () => this.loadConfigData());

        // WebSocket SSH终端相关
        document.getElementById('ssh-connect-btn')?.addEventListener('click', () => this.connectWebTerminal());
        document.getElementById('ssh-disconnect-btn')?.addEventListener('click', () => this.disconnectWebTerminal());
        document.getElementById('ssh-clear-btn')?.addEventListener('click', () => this.clearWebTerminal());
        
        // 窗口大小调整
        window.addEventListener('resize', () => {
            if (this.webTerminalFitAddon) {
                setTimeout(() => {
                    this.webTerminalFitAddon.fit();
                    this.sendTerminalResize();
                }, 100);
            }
        });

        // 模型管理（简化版）
        // 移除复杂的模型操作，只保留状态显示

        // 配置管理
        document.getElementById('add-server')?.addEventListener('click', () => this.showAddServerForm());
        document.getElementById('save-server-config')?.addEventListener('click', () => this.saveServerConfig());
        document.getElementById('cancel-server-config')?.addEventListener('click', () => this.cancelServerConfig());
        document.getElementById('test-server-connection')?.addEventListener('click', () => this.testServerConnection());
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadGPUData(),
                this.loadModelsData(), 
                this.loadSystemData(),
                this.loadTokenStats(),
                this.loadConfigData()
            ]);
        } catch (error) {
            console.error('初始化数据加载失败:', error);
            this.showAlert('error', '初始化数据加载失败: ' + error.message);
        }
    }

    startAutoRefresh() {
        this.updateTimers.gpu = setInterval(() => this.loadGPUData(), this.updateInterval);
        this.updateTimers.system = setInterval(() => this.loadSystemData(), this.updateInterval);
        this.updateTimers.models = setInterval(() => this.loadModelsData(), this.updateInterval * 2); // 模型状态更新慢一些
        this.updateTimers.tokens = setInterval(() => this.loadTokenStats(), this.updateInterval);
    }

    stopAutoRefresh() {
        Object.values(this.updateTimers).forEach(timer => clearInterval(timer));
        this.updateTimers = {};
    }

    // GPU监控相关
    async loadGPUData() {
        try {
            const response = await fetch(`${this.apiBase}/api/gpu/current`);
            const data = await response.json();
            
            if (data.success) {
                this.renderGPUData(data.data);
            } else {
                throw new Error(data.message || 'GPU数据获取失败');
            }
        } catch (error) {
            console.error('GPU数据加载失败:', error);
            this.renderGPUError(error.message);
        }
    }

    renderGPUData(gpuData) {
        const container = document.getElementById('gpu-grid');
        if (!container) return;

        if (!gpuData || gpuData.length === 0) {
            container.innerHTML = '<div class="alert alert-info">暂无GPU数据</div>';
            return;
        }

        const groupedData = this.groupGPUByServer(gpuData);
        
        container.innerHTML = Object.entries(groupedData).map(([serverName, gpus]) => 
            `<div class="gpu-server">
                <h4 class="server-title">${serverName}</h4>
                ${gpus.map(gpu => this.renderGPUCard(gpu)).join('')}
            </div>`
        ).join('');
    }

    groupGPUByServer(gpuData) {
        return gpuData.reduce((groups, gpu) => {
            const server = gpu.server_name || '未知服务器';
            if (!groups[server]) groups[server] = [];
            groups[server].push(gpu);
            return groups;
        }, {});
    }

    renderGPUCard(gpu) {
        const utilizationGpu = gpu.utilization_gpu || 0;
        const utilizationMemory = gpu.utilization_memory || 0;
        const temperature = gpu.temperature || 0;
        // 基于更新时间判断GPU是否在线（最近5分钟内有数据更新）
        const lastUpdate = new Date(gpu.updated_at || gpu.created_at);
        const now = new Date();
        const timeDiff = (now - lastUpdate) / 1000 / 60; // 分钟
        const isOnline = timeDiff < 5; // 5分钟内有数据更新就认为在线

        return `
            <div class="gpu-card">
                <div class="gpu-header">
                    <div class="gpu-name">GPU ${gpu.gpu_index || 0}</div>
                    <div class="gpu-status ${isOnline ? 'online' : 'offline'}">
                        ${isOnline ? '在线' : '离线'}
                    </div>
                </div>
                <div class="gpu-metrics">
                    <div class="gpu-metric">
                        <span class="gpu-metric-value">${utilizationGpu}%</span>
                        <span class="gpu-metric-label">GPU使用率</span>
                        <div class="progress">
                            <div class="progress-bar gpu" style="width: ${utilizationGpu}%"></div>
                        </div>
                    </div>
                    <div class="gpu-metric">
                        <span class="gpu-metric-value">${utilizationMemory}%</span>
                        <span class="gpu-metric-label">显存使用率</span>
                        <div class="progress">
                            <div class="progress-bar memory" style="width: ${utilizationMemory}%"></div>
                        </div>
                    </div>
                    <div class="gpu-metric">
                        <span class="gpu-metric-value">${temperature}°C</span>
                        <span class="gpu-metric-label">温度</span>
                    </div>
                    <div class="gpu-metric">
                        <span class="gpu-metric-value">${gpu.power_draw || 0}W</span>
                        <span class="gpu-metric-label">功耗</span>
                    </div>
                </div>
            </div>
        `;
    }

    renderGPUError(error) {
        const container = document.getElementById('gpu-grid');
        if (container) {
            container.innerHTML = `<div class="alert alert-error">GPU数据加载失败: ${error}</div>`;
        }
    }

    // 模型管理相关
    async loadModelsData() {
        try {
            const response = await fetch(`${this.apiBase}/api/models/`);
            const data = await response.json();
            
            if (data.success) {
                this.renderModelsData(data.data);
            } else {
                throw new Error(data.message || '模型数据获取失败');
            }
        } catch (error) {
            console.error('模型数据加载失败:', error);
            this.renderModelsError(error.message);
        }
    }

    renderModelsData(modelsData) {
        const container = document.getElementById('models-list');
        if (!container) return;

        // 更新模型状态概览
        this.updateModelsSummary(modelsData);

        if (!modelsData || modelsData.length === 0) {
            container.innerHTML = '<div class="alert alert-info">暂无模型数据</div>';
            return;
        }

        container.innerHTML = modelsData.map(model => this.renderModelItem(model)).join('');
    }

    updateModelsSummary(modelsData) {
        const summaryElement = document.getElementById('models-summary');
        if (!summaryElement || !modelsData) return;

        const total = modelsData.length;
        const running = modelsData.filter(model => model.status === 'RUNNING').length;
        const stopped = total - running;

        summaryElement.innerHTML = `
            <span style="color: #28a745;">运行中: ${running}</span> | 
            <span style="color: #dc3545;">已停止: ${stopped}</span> | 
            <span style="color: #6c757d;">总计: ${total}</span>
        `;
    }

    renderModelItem(model) {
        const isRunning = model.status === 'RUNNING';
        const statusClass = isRunning ? 'running' : 'stopped';
        const statusText = isRunning ? '运行中' : '已停止';

        return `
            <div class="model-item">
                <div class="model-header">
                    <div class="model-name">${model.name || '未知模型'}</div>
                    <div class="model-status ${statusClass}">${statusText}</div>
                </div>
                <div class="model-info">
                    <div>服务器: ${model.server_name || '未知'}</div>
                    <div>端口: ${model.port || '未分配'}</div>
                    ${model.gpu_indices ? `<div>GPU: ${model.gpu_indices}</div>` : ''}
                    ${isRunning && model.port ? `<div>访问地址: http://${model.server_name}:${model.port}</div>` : ''}
                </div>
                <div class="model-simple-actions" style="margin-top: 10px;">
                    <small style="color: #666;">
                        详细管理请访问 
                        <a href="/vllm" style="color: #007bff; text-decoration: none;">VLLM管理页面</a>
                    </small>
                </div>
            </div>
        `;
    }

    async startModel(modelId) {
        try {
            const response = await fetch(`${this.apiBase}/api/models/${modelId}/start`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', '模型启动成功');
                this.loadModelsData();
            } else {
                throw new Error(data.message || '模型启动失败');
            }
        } catch (error) {
            console.error('模型启动失败:', error);
            this.showAlert('error', '模型启动失败: ' + error.message);
        }
    }

    async stopModel(modelId) {
        try {
            const response = await fetch(`${this.apiBase}/api/models/${modelId}/stop`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', '模型停止成功');
                this.loadModelsData();
            } else {
                throw new Error(data.message || '模型停止失败');
            }
        } catch (error) {
            console.error('模型停止失败:', error);
            this.showAlert('error', '模型停止失败: ' + error.message);
        }
    }

    // VLLM相关功能已移至独立的VLLM管理页面 (/vllm)
    


    renderModelsError(error) {
        const container = document.getElementById('models-list');
        if (container) {
            container.innerHTML = `<div class="alert alert-error">模型数据加载失败: ${error}</div>`;
        }
    }

    // 系统监控相关
    async loadSystemData() {
        try {
            const response = await fetch(`${this.apiBase}/api/system/current`);
            const data = await response.json();
            
            if (data.success) {
                this.renderSystemData(data.data);
            } else {
                throw new Error(data.message || '系统数据获取失败');
            }
        } catch (error) {
            console.error('系统数据加载失败:', error);
            this.renderSystemError(error.message);
        }
    }

    renderSystemData(systemData) {
        this.renderSystemMetrics(systemData);
        this.renderSystemServers(systemData);
    }

    // Token统计相关
    async loadTokenStats() {
        try {
            const response = await fetch(`${this.apiBase}/api/models/stats/tokens`);
            const data = await response.json();
            
            if (data.success) {
                this.renderTokenStats(data.data);
            } else {
                throw new Error(data.message || 'Token统计获取失败');
            }
        } catch (error) {
            console.error('Token统计加载失败:', error);
            this.renderTokenStatsError(error.message);
        }
    }

    renderTokenStats(tokenData) {
        const container = document.getElementById('token-stats');
        if (!container) return;

        const overview = tokenData.overview || {};
        const byServer = tokenData.by_server || {};
        const topModels = tokenData.top_models || [];

        // 构建Token统计HTML
        container.innerHTML = `
            <div class="token-stats-grid">
                <div class="token-metric-group">
                    <h4>📊 总体统计</h4>
                    <div class="token-metrics">
                        <div class="token-metric">
                            <span class="metric-label">运行中模型</span>
                            <span class="metric-value">${overview.total_running_models || 0}</span>
                        </div>
                        <div class="token-metric">
                            <span class="metric-label">总Token数</span>
                            <span class="metric-value">${this.formatNumber(overview.total_tokens || 0)}</span>
                        </div>
                        <div class="token-metric">
                            <span class="metric-label">总请求数</span>
                            <span class="metric-value">${this.formatNumber(overview.total_requests || 0)}</span>
                        </div>
                        <div class="token-metric">
                            <span class="metric-label">平均Token/请求</span>
                            <span class="metric-value">${overview.avg_tokens_per_request || 0}</span>
                        </div>
                    </div>
                </div>
                
                <div class="token-metric-group">
                    <h4>🖥️ 按服务器统计</h4>
                    <div class="server-token-stats">
                        ${Object.entries(byServer).map(([serverName, stats]) => `
                            <div class="server-token-stat">
                                <div class="server-name">${serverName}</div>
                                <div class="server-stats">
                                    <span>模型: ${stats.running_models}</span>
                                    <span>Token: ${this.formatNumber(stats.total_tokens)}</span>
                                    <span>请求: ${this.formatNumber(stats.total_requests)}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="token-metric-group">
                    <h4>🏆 最活跃模型Top 5</h4>
                    <div class="top-models-list">
                        ${topModels.slice(0, 5).map((model, index) => `
                            <div class="top-model-item">
                                <div class="model-rank">#${index + 1}</div>
                                <div class="model-info">
                                    <div class="model-name">${model.name}</div>
                                    <div class="model-details">
                                        <span class="model-server">${model.server_name}</span>
                                        <span class="model-type">${model.model_type}</span>
                                    </div>
                                </div>
                                <div class="model-stats">
                                    <div class="stat">
                                        <span>Token: ${this.formatNumber(model.total_tokens)}</span>
                                    </div>
                                    <div class="stat">
                                        <span>请求: ${this.formatNumber(model.total_requests)}</span>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    renderTokenStatsError(message) {
        const container = document.getElementById('token-stats');
        if (container) {
            container.innerHTML = `<div class="alert alert-error">Token统计加载失败: ${message}</div>`;
        }
    }

    renderSystemMetrics(systemData) {
        const container = document.getElementById('system-metrics');
        if (!container) return;

        // 计算总体指标
        const totalServers = systemData?.length || 0;
        const onlineServers = systemData?.filter(s => s.server_status === 'online').length || 0;
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
        // 改进的在线状态判断：基于server_status和有效数据
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

    formatLoadAverage(loadAverage) {
        // 处理负载平均值格式转换
        if (!loadAverage) {
            return '0.00';
        }
        
        // 如果是字符串，解析第一个值（1分钟负载）
        if (typeof loadAverage === 'string') {
            const parts = loadAverage.split(',');
            if (parts.length > 0) {
                const firstLoad = parseFloat(parts[0].trim());
                return isNaN(firstLoad) ? '0.00' : firstLoad.toFixed(2);
            }
        }
        
        // 如果是数组，取第一个值
        if (Array.isArray(loadAverage) && loadAverage.length > 0) {
            const firstLoad = parseFloat(loadAverage[0]);
            return isNaN(firstLoad) ? '0.00' : firstLoad.toFixed(2);
        }
        
        // 如果是数字，直接使用
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

    formatNumber(num) {
        if (!num || num === 0) return '0';
        
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
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

    renderSystemError(error) {
        const container = document.getElementById('system-metrics');
        if (container) {
            container.innerHTML = `<div class="alert alert-error">系统数据加载失败: ${error}</div>`;
        }
    }

    // SSH相关
    async connectSSH() {
        const serverSelect = document.getElementById('ssh-server-select');
        const serverName = serverSelect?.value;
        
        if (!serverName) {
            this.showAlert('error', '请先选择服务器');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/api/ssh/servers/${serverName}/status`);
            const data = await response.json();
            
            if (data.success) {
                this.addTerminalOutput(`连接到 ${serverName} - ${data.data.status}`);
                this.loadServerList(); // 更新服务器列表
            } else {
                throw new Error(data.message || 'SSH连接失败');
            }
        } catch (error) {
            console.error('SSH连接失败:', error);
            this.addTerminalOutput(`连接失败: ${error.message}`);
        }
    }

    async executeSSHCommand() {
        const serverSelect = document.getElementById('ssh-server-select');
        const commandInput = document.getElementById('ssh-command-input');
        const serverName = serverSelect?.value;
        const command = commandInput?.value.trim();
        
        if (!serverName) {
            this.showAlert('error', '请先选择服务器');
            return;
        }
        
        if (!command) {
            this.showAlert('error', '请输入命令');
            return;
        }

        this.addTerminalOutput(`$ ${command}`);
        commandInput.value = '';

        try {
            const response = await fetch(`${this.apiBase}/api/ssh/servers/${serverName}/execute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    command: command,
                    timeout: 30
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const result = data.data;
                if (result.stdout) {
                    this.addTerminalOutput(result.stdout);
                }
                if (result.stderr) {
                    this.addTerminalOutput(`错误: ${result.stderr}`);
                }
            } else {
                throw new Error(data.message || '命令执行失败');
            }
        } catch (error) {
            console.error('SSH命令执行失败:', error);
            this.addTerminalOutput(`命令执行失败: ${error.message}`);
        }
    }

    addTerminalOutput(text) {
        const terminal = document.getElementById('ssh-terminal');
        if (!terminal) return;

        const timestamp = new Date().toLocaleTimeString();
        terminal.innerHTML += `<div>[${timestamp}] ${text}</div>`;
        terminal.scrollTop = terminal.scrollHeight;
        
        // 保持历史记录不要太长
        const lines = terminal.getElementsByTagName('div');
        if (lines.length > 1000) {
            for (let i = 0; i < 100; i++) {
                if (lines[0]) lines[0].remove();
            }
        }
    }

    // 配置管理相关
    async loadConfigData() {
        try {
            const response = await fetch(`${this.apiBase}/api/config/servers`);
            const data = await response.json();
            
            if (data.success) {
                this.renderConfigData(data.data);
                this.loadServerList(data.data);
            } else {
                throw new Error(data.message || '配置数据获取失败');
            }
        } catch (error) {
            console.error('配置数据加载失败:', error);
            this.renderConfigError(error.message);
        }
    }

    renderConfigData(configData) {
        const container = document.getElementById('server-config-list');
        if (!container) return;

        if (!configData || configData.length === 0) {
            container.innerHTML = '<div class="alert alert-info">暂无服务器配置</div>';
            return;
        }

        container.innerHTML = configData.map(server => this.renderServerConfigItem(server)).join('');
    }

    renderServerConfigItem(server) {
        return `
            <div class="server-config-item">
                <div class="server-config-info">
                    <div class="server-config-name">${server.name}</div>
                    <div class="server-config-details">
                        ${server.host}:${server.port} | GPU: ${server.gpu_count} | 
                        状态: ${server.enabled ? '启用' : '禁用'}
                    </div>
                </div>
                <div class="server-config-actions">
                    <button class="btn btn-primary btn-sm" onclick="dashboard.editServer('${server.name}')">编辑</button>
                    <button class="btn btn-sm ${server.enabled ? 'btn-danger' : 'btn-success'}" 
                            onclick="dashboard.toggleServer('${server.name}', ${!server.enabled})">
                        ${server.enabled ? '禁用' : '启用'}
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="dashboard.deleteServer('${server.name}')">删除</button>
                </div>
            </div>
        `;
    }

    loadServerList(servers) {
        const serverSelect = document.getElementById('ssh-server-select');
        if (!serverSelect) return;

        const currentValue = serverSelect.value;
        
        if (servers) {
            serverSelect.innerHTML = '<option value="">选择服务器...</option>' +
                servers.filter(s => s.enabled)
                       .map(s => `<option value="${s.name}">${s.name} (${s.host})</option>`)
                       .join('');
        } else {
            // 如果没有传入servers，从现有选项中保留
            return;
        }
        
        // 恢复之前的选择
        if (currentValue) {
            serverSelect.value = currentValue;
        }
    }

    renderConfigError(error) {
        const container = document.getElementById('server-config-list');
        if (container) {
            container.innerHTML = `<div class="alert alert-error">配置数据加载失败: ${error}</div>`;
        }
    }

    // 工具方法
    showAlert(type, message, duration = 5000) {
        // 创建警告元素
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        alert.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            min-width: 300px;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        
        document.body.appendChild(alert);
        
        // 显示动画
        setTimeout(() => {
            alert.style.opacity = '1';
            alert.style.transform = 'translateX(0)';
        }, 100);
        
        // 自动隐藏
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 300);
        }, duration);
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleString('zh-CN');
    }

    // 配置管理新增功能
    showAddServerForm() {
        // 强制重置编辑状态
        this.isEditMode = false;
        this.editingServerName = null;
        
        // 清空表单
        const form = document.getElementById('server-config-form');
        if (form) {
            form.reset();
        }
        
        // 确保服务器名称字段可编辑
        const serverNameField = document.getElementById('server-name');
        if (serverNameField) {
            serverNameField.disabled = false;
            serverNameField.focus();
            serverNameField.value = ''; // 明确清空
        }
        
        // 更新按钮文本
        const saveButton = document.getElementById('save-server-config');
        if (saveButton) {
            saveButton.textContent = '保存配置';
        }
        
        // 显示提示信息
        this.showAlert('info', '请填写新服务器信息');
        
        console.log('进入添加服务器模式，isEditMode:', this.isEditMode);
    }

    async saveServerConfig() {
        const form = document.getElementById('server-config-form');
        
        // 调试信息
        console.log('保存服务器配置，当前状态:', {
            isEditMode: this.isEditMode,
            editingServerName: this.editingServerName
        });
        
        const serverConfig = {
            name: document.getElementById('server-name').value.trim(),
            host: document.getElementById('server-host').value.trim(),
            port: parseInt(document.getElementById('server-port').value) || 22,
            username: document.getElementById('server-username').value.trim(),
            password: document.getElementById('server-password').value,
            gpu_count: parseInt(document.getElementById('server-gpu-count').value) || 1,
            model_path: document.getElementById('server-model-path').value.trim(),
            enabled: true
        };

        // 验证必填字段
        const requiredFields = ['name', 'host', 'username'];
        // 编辑模式下，密码可以为空（表示不更改）
        if (!this.isEditMode) {
            requiredFields.push('password');
        }
        
        for (const field of requiredFields) {
            if (!serverConfig[field]) {
                this.showAlert('error', `请填写${field === 'name' ? '服务器名称' : field === 'host' ? '主机地址' : field === 'username' ? '用户名' : '密码'}`);
                return;
            }
        }

        try {
            let url, method;
            let requestBody = { ...serverConfig };
            
            // 严格验证编辑模式状态
            if (this.isEditMode && this.editingServerName) {
                // 编辑模式：使用PUT方法
                url = `${this.apiBase}/api/config/servers/${this.editingServerName}`;
                method = 'PUT';
                
                console.log('编辑模式，目标服务器:', this.editingServerName);
                
                // 如果密码为空，从请求中移除，表示不更改密码
                if (!serverConfig.password) {
                    delete requestBody.password;
                }
                
                // 编辑模式下移除name字段，因为不能更改
                delete requestBody.name;
            } else {
                // 新增模式：使用POST方法
                url = `${this.apiBase}/api/config/servers`;
                method = 'POST';
                
                console.log('新增模式，服务器名称:', serverConfig.name);
                
                // 确保不是编辑模式
                this.isEditMode = false;
                this.editingServerName = null;
            }
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                const actionText = this.isEditMode ? '更新' : '保存';
                this.showAlert('success', `服务器配置${actionText}成功`);
                
                // 重置表单和状态
                this.resetServerConfigForm();
                
                this.loadConfigData();
            } else {
                // 显示服务器返回的具体错误信息
                const errorMsg = data.detail || data.message || `HTTP ${response.status}: 请求失败`;
                throw new Error(errorMsg);
            }
        } catch (error) {
            console.error('保存服务器配置失败:', error);
            this.showAlert('error', error.message);
        }
    }

    async testServerConnection() {
        const serverName = document.getElementById('server-name').value.trim();
        
        if (!serverName) {
            this.showAlert('error', '请先填写服务器名称');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/api/config/servers/${serverName}/test`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showAlert('success', '服务器连接测试成功');
            } else {
                const errorMsg = data.detail || data.message || `HTTP ${response.status}: 连接测试失败`;
                throw new Error(errorMsg);
            }
        } catch (error) {
            console.error('服务器连接测试失败:', error);
            this.showAlert('error', error.message);
        }

    }

    async editServer(serverName) {
        try {
            // 先重置状态
            this.resetServerConfigForm();
            
            const response = await fetch(`${this.apiBase}/api/config/servers/${serverName}`);
            const data = await response.json();
            
            if (data.success) {
                // 设置编辑模式
                this.isEditMode = true;
                this.editingServerName = serverName;
                
                console.log('进入编辑模式，目标服务器:', serverName);
                
                const server = data.data;
                // 安全地填充表单
                const fields = {
                    'server-name': server.name || '',
                    'server-host': server.host || '',
                    'server-port': server.port || 22,
                    'server-username': server.username || '',
                    'server-password': '', // 出于安全考虑不显示密码
                    'server-gpu-count': server.gpu_count || 1,
                    'server-model-path': server.model_path || ''
                };
                
                Object.entries(fields).forEach(([id, value]) => {
                    const element = document.getElementById(id);
                    if (element) {
                        element.value = value;
                    }
                });
                
                // 编辑模式下禁用服务器名称修改
                const serverNameField = document.getElementById('server-name');
                if (serverNameField) {
                    serverNameField.disabled = true;
                }
                
                // 更新按钮文本
                const saveButton = document.getElementById('save-server-config');
                if (saveButton) {
                    saveButton.textContent = '更新配置';
                }
                
                this.showAlert('info', `正在编辑服务器: ${serverName}`);
            } else {
                throw new Error(data.message || '获取服务器配置失败');
            }
        } catch (error) {
            console.error('编辑服务器失败:', error);
            this.showAlert('error', '获取服务器配置失败: ' + error.message);
            // 编辑失败时重置状态
            this.resetServerConfigForm();
        }
    }

    async toggleServer(serverName, enabled) {
        try {
            const response = await fetch(`${this.apiBase}/api/config/servers/${serverName}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ enabled: enabled })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', `服务器已${enabled ? '启用' : '禁用'}`);
                this.loadConfigData();
            } else {
                throw new Error(data.message || '服务器状态更新失败');
            }
        } catch (error) {
            console.error('切换服务器状态失败:', error);
            this.showAlert('error', '服务器状态更新失败: ' + error.message);
        }

    }

    async deleteServer(serverName) {
        if (!confirm(`确定要删除服务器 "${serverName}" 吗？此操作不可撤销。`)) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/api/config/servers/${serverName}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', '服务器删除成功');
                this.loadConfigData();
            } else {
                throw new Error(data.message || '删除服务器失败');
            }
        } catch (error) {
            console.error('删除服务器失败:', error);
            this.showAlert('error', '删除服务器失败: ' + error.message);
        }
    }

    cancelServerConfig() {
        this.resetServerConfigForm();
        this.showAlert('info', '已取消操作');
    }
    
    resetServerConfigForm() {
        // 重置表单
        const form = document.getElementById('server-config-form');
        if (form) {
            form.reset();
        }
        
        // 重置编辑状态
        this.isEditMode = false;
        this.editingServerName = null;
        
        // 启用服务器名称字段
        const serverNameField = document.getElementById('server-name');
        if (serverNameField) {
            serverNameField.disabled = false;
            serverNameField.value = '';
        }
        
        // 恢复按钮文本
        const saveButton = document.getElementById('save-server-config');
        if (saveButton) {
            saveButton.textContent = '保存配置';
        }
        
        console.log('表单状态已重置');
    }

    // 模型管理新增功能
    showAddModelForm() {
        // 这里可以打开一个模态框或表单来添加新模型
        const modelName = prompt('请输入模型名称:');
        const modelPath = prompt('请输入模型路径:');
        const serverName = prompt('请输入服务器名称:');
        
        if (modelName && modelPath && serverName) {
            this.addModel({
                name: modelName,
                model_path: modelPath,
                server_name: serverName,
                model_type: 'LLM',
                gpu_indices: '0',
                max_model_len: 4096
            });
        }
    }

    async addModel(modelConfig) {
        try {
            const response = await fetch(`${this.apiBase}/api/models/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(modelConfig)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', '模型添加成功');
                this.loadModelsData();
            } else {
                throw new Error(data.message || '添加模型失败');
            }
        } catch (error) {
            console.error('添加模型失败:', error);
            this.showAlert('error', '添加模型失败: ' + error.message);
        }
    }

    async editModel(modelId) {
        // 这里可以实现编辑模型的功能
        this.showAlert('info', '编辑模型功能即将推出');
    }

        async deleteModel(modelId) {
        if (!confirm('确定要删除这个模型吗？')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/api/models/${modelId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', '模型删除成功');
                this.loadModelsData();
            } else {
                throw new Error(data.message || '删除模型失败');
            }
        } catch (error) {
            console.error('删除模型失败:', error);
            this.showAlert('error', '删除模型失败: ' + error.message);
        }
    }
    
    // 环境诊断功能已移至VLLM管理页面
    
    // 运行服务管理功能已移至VLLM管理页面

    // WebSocket SSH终端方法
    initWebTerminal() {
        if (this.webTerminal) {
            return;
        }

        // 初始化xterm.js终端
        this.webTerminal = new Terminal({
            cursorBlink: true,
            fontSize: 13,
            fontFamily: 'Consolas, Monaco, "Courier New", monospace',
            theme: {
                background: '#1e1e1e',
                foreground: '#ffffff',
                cursor: '#ffffff',
                selection: '#4d4d4d'
            },
            allowTransparency: false,
            rows: 24,
            cols: 80
        });

        // 添加fit插件
        this.webTerminalFitAddon = new FitAddon.FitAddon();
        this.webTerminal.loadAddon(this.webTerminalFitAddon);

        // 挂载到DOM
        const terminalContainer = document.getElementById('ssh-web-terminal');
        terminalContainer.innerHTML = '';
        this.webTerminal.open(terminalContainer);
        this.webTerminalFitAddon.fit();

        // 处理终端输入
        this.webTerminal.onData(data => {
            if (this.webTerminalWS && this.webTerminalWS.readyState === WebSocket.OPEN) {
                this.webTerminalWS.send(JSON.stringify({
                    type: 'input',
                    data: data
                }));
            }
        });

        this.webTerminal.writeln('终端已初始化，请选择服务器并连接...');
    }

    async connectWebTerminal() {
        const serverSelect = document.getElementById('ssh-server-select');
        const serverName = serverSelect.value;

        if (!serverName) {
            this.showAlert('error', '请先选择服务器');
            return;
        }

        if (this.webTerminalConnected) {
            this.disconnectWebTerminal();
        }

        this.currentServerName = serverName;
        this.updateSSHStatus('正在连接...', 'connecting');

        // 初始化终端
        this.initWebTerminal();

        // 建立WebSocket连接
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/terminal/${encodeURIComponent(serverName)}`;

        this.webTerminalWS = new WebSocket(wsUrl);

        this.webTerminalWS.onopen = () => {
            this.webTerminalConnected = true;
            this.updateSSHStatus(`已连接到 ${serverName}`, 'connected');
            this.updateSSHButtons();
            this.webTerminal.clear();
            this.sendTerminalResize();
        };

        this.webTerminalWS.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                if (data.type === 'output') {
                    this.webTerminal.write(data.data);
                } else if (data.type === 'connected') {
                    this.webTerminal.write(data.message);
                } else if (data.type === 'error') {
                    this.webTerminal.write(`\r\n\x1b[31m${data.message}\x1b[0m\r\n`);
                }
            } catch (error) {
                console.error('处理WebSocket消息错误:', error);
            }
        };

        this.webTerminalWS.onclose = (event) => {
            this.webTerminalConnected = false;
            this.updateSSHButtons();

            let errorMessage = '连接已断开';
            if (event.code === 4000) {
                errorMessage = '服务器不存在';
            } else if (event.code === 4001) {
                errorMessage = '服务器未启用';
            } else if (event.code === 4002) {
                errorMessage = `连接错误: ${event.reason}`;
            }

            this.updateSSHStatus(errorMessage, 'error');
            
            if (this.webTerminal) {
                this.webTerminal.write('\r\n\x1b[31m连接已断开\x1b[0m\r\n');
            }
        };

        this.webTerminalWS.onerror = (error) => {
            console.error('WebSocket错误:', error);
            this.updateSSHStatus('连接错误', 'error');
        };
    }

    disconnectWebTerminal() {
        if (this.webTerminalWS) {
            this.webTerminalWS.close();
            this.webTerminalWS = null;
        }
        this.webTerminalConnected = false;
        this.updateSSHStatus('未连接', '');
        this.updateSSHButtons();
        
        if (this.webTerminal) {
            this.webTerminal.write('\r\n\x1b[33m已断开连接\x1b[0m\r\n');
        }
    }

    clearWebTerminal() {
        if (this.webTerminal) {
            this.webTerminal.clear();
        }
    }

    sendTerminalResize() {
        if (this.webTerminalWS && this.webTerminalWS.readyState === WebSocket.OPEN && this.webTerminal) {
            this.webTerminalWS.send(JSON.stringify({
                type: 'resize',
                cols: this.webTerminal.cols,
                rows: this.webTerminal.rows
            }));
        }
    }

    updateSSHStatus(message, type = '') {
        const statusElement = document.getElementById('ssh-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `ssh-status ${type}`;
        }
    }

    updateSSHButtons() {
        const connectBtn = document.getElementById('ssh-connect-btn');
        const disconnectBtn = document.getElementById('ssh-disconnect-btn');
        
        if (connectBtn) connectBtn.disabled = this.webTerminalConnected;
        if (disconnectBtn) disconnectBtn.disabled = !this.webTerminalConnected;
    }
}

// 全局实例
let dashboard;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    dashboard = new AIPlatformDashboard();
    
    // 添加页面离开时的清理
    window.addEventListener('beforeunload', function() {
        if (dashboard) {
            dashboard.stopAutoRefresh();
            dashboard.disconnectWebTerminal();
        }
    });
    
    // 添加页面可见性变化处理
    document.addEventListener('visibilitychange', function() {
        if (dashboard) {
            if (document.hidden) {
                dashboard.stopAutoRefresh();
            } else {
                dashboard.startAutoRefresh();
                dashboard.loadInitialData();
            }
        }
    });
});
