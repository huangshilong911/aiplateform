# AI平台管理系统 (Python版)

基于FastAPI构建的企业级GPU服务器监控和大模型服务管理平台，提供实时监控、模型管理、SSH远程控制、WebSocket终端、VLLM服务管理等全方位功能。

## 🚀 功能特性

### 需求1: GPU服务器监控
- ✅ 实时监控GPU使用率、内存、温度、功耗等指标
- ✅ 支持多服务器同时监控
- ✅ 历史数据存储和查询
- ✅ GPU状态分析和统计
- ✅ WebSocket实时推送GPU数据

### 需求2: 模型列表管理
- ✅ 自动发现服务器上的大模型文件
- ✅ 模型信息展示（路径、大小、类型等）
- ✅ 模型分类和组织管理
- ✅ 批量模型操作
- ✅ ModelScope模型下载支持

### 需求3: 模型服务控制
- ✅ 在线启动/停止大模型服务
- ✅ 支持VLLM框架
- ✅ 服务状态监控
- ✅ 端口管理和资源分配
- ✅ 服务日志查看
- ✅ 动态端口范围配置

### 需求3.1: VLLM专业管理（新功能）
- ✅ 独立VLLM管理页面
- ✅ 完整的VLLM参数配置（基础+高级）
- ✅ 智能参数预设（小/中/大模型）
- ✅ 配置模板保存和加载
- ✅ 实时性能监控
- ✅ 健康检查和连接测试
- ✅ 批量服务操作
- ✅ 增强的环境诊断

### 需求4: SSH远程登录
- ✅ 安全的SSH连接管理
- ✅ 远程命令执行
- ✅ 连接状态监控
- ✅ 多服务器会话管理
- ✅ **WebSocket实时终端**（新功能）
- ✅ 交互式SSH会话

### 需求5: 配置管理
- ✅ 动态添加/修改/删除GPU服务器
- ✅ 连接配置测试
- ✅ 系统参数配置
- ✅ 配置文件管理
- ✅ 实时配置更新

### 需求6: 开发者工具（新功能）
- ✅ API文档自动生成（Swagger/ReDoc）
- ✅ 原始数据API访问
- ✅ 系统状态诊断工具
- ✅ 故障排查工具
- ✅ 实时日志查看
- ✅ 增强的GPU环境诊断
- ✅ Python环境检测
- ✅ CUDA运行时验证

### 需求7: 页面模块化（新功能）
- ✅ 系统监控页面
- ✅ 控制台仪表板
- ✅ 开发者工具页面
- ✅ WebSocket终端页面
- ✅ VLLM专业管理页面
- ✅ 响应式Web界面
- ✅ 模块化架构设计

## 📋 系统要求

- **Python**: 3.8+
- **操作系统**: Linux/Windows/macOS
- **内存**: 至少2GB RAM
- **磁盘**: 至少1GB可用空间
- **网络**: 支持SSH连接

## 🛠️ 安装部署

### 1. 环境准备

```bash
# 克隆项目（或解压到aiplatform_py目录）
cd aiplatform_py

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置系统

编辑 `config/config.yaml` 文件，配置GPU服务器信息：

```yaml
# 服务器配置
server:
  host: "0.0.0.0"
  port: 8088
  workers: 4

# 数据库配置
database:
  url: "sqlite:///./aiplatform.db"
  echo: false

# GPU服务器配置
gpu_servers:
  - name: "GPU-Server-1"
    host: "192.168.1.30"  # 修改为实际IP
    port: 22
    username: "your_username"  # 修改为实际用户名
    password: "your_password"  # 修改为实际密码
    gpu_count: 4
    enabled: true
    model_path: "/path/to/models"  # 修改为实际模型路径

# 监控配置
monitoring:
  gpu:
    interval: 3  # GPU监控间隔（秒）
    history_retention: 24  # 历史数据保留（小时）
  system:
    interval: 3  # 系统监控间隔（秒）
    history_retention: 24  # 历史数据保留（小时）

# VLLM配置
vllm:
  default_port_range:
    start: 8000
    end: 8100
  default_gpu_memory_utilization: 0.9
  default_max_model_len: 4096
```

### 3. 启动系统

```bash
# 使用启动脚本（推荐）
python run.py

# 或直接使用uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8088
```

### 4. 访问系统

- **主页**: http://localhost:8088
- **系统监控**: http://localhost:8088/
- **控制台**: http://localhost:8088/dashboard
- **开发者工具**: http://localhost:8088/developer
- **WebSocket终端**: http://localhost:8088/terminal
- **VLLM管理**: http://localhost:8088/vllm
- **API文档**: http://localhost:8088/docs
- **健康检查**: http://localhost:8088/health

## 📁 项目结构

```
aiplatform_py/
├── app/                    # 应用核心代码
│   ├── api/               # API路由
│   │   ├── gpu.py         # GPU监控API
│   │   ├── models.py      # 模型管理API
│   │   ├── system.py      # 系统监控API
│   │   ├── ssh.py         # SSH管理API
│   │   ├── config.py      # 配置管理API
│   │   └── vllm_management.py # VLLM管理API（新）
│   ├── models/            # 数据模型
│   │   ├── base.py        # 基础模型
│   │   ├── gpu_resource.py    # GPU资源模型
│   │   ├── model_service.py   # 模型服务模型
│   │   └── system_resource.py # 系统资源模型
│   ├── pages/             # 页面模块
│   │   ├── dashboard.py       # 控制台页面
│   │   ├── system_monitor.py  # 系统监控页面
│   │   ├── developer_tools.py # 开发者工具页面
│   │   ├── terminal.py        # 终端页面
│   │   └── vllm_management_page.py # VLLM管理页面（新）
│   ├── services/          # 业务服务
│   │   ├── ssh_manager.py     # SSH连接管理
│   │   ├── gpu_monitor.py     # GPU监控服务
│   │   ├── system_monitor.py  # 系统监控服务
│   │   ├── model_service.py   # 模型服务管理
│   │   ├── websocket_terminal.py # WebSocket终端服务
│   │   └── enhanced_diagnosis.py # 增强诊断服务（新）
│   ├── static/            # 静态资源
│   │   ├── css/           # 样式文件
│   │   ├── js/            # JavaScript文件
│   │   └── templates/     # 模板文件
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库管理
│   └── main.py           # 应用入口
├── config/               # 配置文件
│   └── config.yaml       # 主配置文件
├── debug_test/           # 调试测试
│   ├── check_server_status.py  # 服务器状态检查
│   ├── cleanup_invalid_records.py # 清理无效记录
│   ├── test_api.py       # API测试脚本
│   ├── check_db.py       # 数据库检查
│   ├── debug_gpu.py      # GPU调试脚本
│   ├── gpu_diagnosis_enhanced.py # 增强GPU诊断
│   ├── test_vllm_management.py # VLLM管理测试
│   └── quick_diagnosis.py # 快速诊断工具
├── docs/                 # 文档目录
│   ├── VLLM_COMPLETE_FEATURES.md # VLLM功能清单
│   ├── VLLM_SEPARATION_SUMMARY.md # VLLM分离总结
│   ├── DIAGNOSIS_FUNCTION_FIX.md # 诊断功能修复
│   └── LOADING_STATE_FIX.md # 加载状态修复
├── logs/                 # 日志目录
├── data/                 # 数据目录
├── models/               # 模型存储目录
├── requirements.txt      # 依赖包列表
├── run.py               # 启动脚本
└── README.md            # 项目文档
```

## 🔧 API接口

### GPU监控

```bash
# 获取当前GPU状态
GET /api/gpu/current

# 获取指定服务器GPU状态
GET /api/gpu/servers/{server_name}

# 获取GPU历史数据
GET /api/gpu/history/{server_name}/{gpu_index}?hours=1

# 获取GPU统计摘要
GET /api/gpu/summary

# WebSocket GPU数据推送
WS /ws/gpu/{server_name}
```

### 模型管理

```bash
# 获取所有模型
GET /api/models/

# 启动模型服务
POST /api/models/{model_id}/start

# 停止模型服务
POST /api/models/{model_id}/stop

# 发现服务器模型
GET /api/models/discover/{server_name}

# 添加模型
POST /api/models/
Content-Type: application/json
{
    "name": "chatglm3-6b",
    "model_path": "/home/models/chatglm3-6b",
    "server_name": "GPU-Server-1",
    "gpu_indices": "0",
    "max_model_len": 4096
}
```

### 系统监控

```bash
# 获取系统资源状态
GET /api/system/current

# 获取指定服务器系统资源
GET /api/system/servers/{server_name}

# 获取系统历史数据
GET /api/system/history/{server_name}?hours=1

# WebSocket系统数据推送
WS /ws/system/{server_name}
```

### SSH管理

```bash
# 执行SSH命令
POST /api/ssh/servers/{server_name}/execute
Content-Type: application/json
{
    "command": "nvidia-smi",
    "timeout": 30
}

# 检查SSH连接状态
GET /api/ssh/servers/{server_name}/status

# 获取服务器系统信息
GET /api/ssh/servers/{server_name}/system-info

# WebSocket SSH终端
WS /ws/terminal/{server_name}
```

### 配置管理

```bash
# 添加GPU服务器
POST /api/config/servers
Content-Type: application/json
{
    "name": "GPU-Server-3",
    "host": "192.168.1.32",
    "username": "admin",
    "password": "password",
    "gpu_count": 8,
    "model_path": "/home/admin/models"
}

# 测试服务器连接
POST /api/config/servers/{server_name}/test

# 更新服务器配置
PUT /api/config/servers/{server_name}

# 删除服务器配置
DELETE /api/config/servers/{server_name}
```

### VLLM管理（新功能）

```bash
# 获取服务器列表
GET /api/vllm/servers

# 环境诊断
GET /api/vllm/diagnose/{server_name}

# 发现模型
GET /api/vllm/models/{server_name}

# 获取运行中服务
GET /api/vllm/running/{server_name}

# 获取服务日志
GET /api/vllm/logs/{server_name}/{port}?lines=100

# 检查端口使用
GET /api/vllm/ports/{server_name}

# 启动VLLM服务
POST /api/vllm/start
Content-Type: application/json
{
    "server_name": "GPU-Server-1",
    "model_path": "/path/to/model",
    "port": 8000,
    "gpu_indices": "0",
    "tensor_parallel_size": 1,
    "max_model_len": 4096,
    "gpu_memory_utilization": 0.9,
    "dtype": "auto",
    "quantization": null,
    "trust_remote_code": false
}

# 停止VLLM服务
POST /api/vllm/stop
Content-Type: application/json
{
    "server_name": "GPU-Server-1",
    "port": 8000
}

# 重启VLLM服务
POST /api/vllm/restart

# 获取服务状态
GET /api/vllm/status/{server_name}

# 健康检查
GET /api/vllm/health/{server_name}/{port}

# 性能监控
GET /api/vllm/performance/{server_name}

# 批量操作
POST /api/vllm/batch-operation

# 配置管理
GET /api/vllm/saved-models
POST /api/vllm/save-model
DELETE /api/vllm/models/{model_id}
```

## 🔍 使用示例

### 1. 监控GPU状态

```python
import requests

# 获取所有GPU状态
response = requests.get("http://localhost:8088/api/gpu/current")
gpu_data = response.json()

for gpu in gpu_data["data"]:
    print(f"服务器: {gpu['server_name']}")
    print(f"GPU {gpu['gpu_index']}: {gpu['utilization_gpu']}% 使用率")
```

### 2. 启动模型服务

```python
import requests

# 添加模型
model_data = {
    "name": "chatglm3-6b",
    "model_path": "/home/models/chatglm3-6b",
    "server_name": "GPU-Server-1",
    "gpu_indices": "0",
    "max_model_len": 4096
}

response = requests.post("http://localhost:8088/api/models/", json=model_data)
model = response.json()["data"]

# 启动模型服务
model_id = model["id"]
response = requests.post(f"http://localhost:8088/api/models/{model_id}/start")
print(response.json()["message"])
```

### 3. 使用WebSocket终端

```javascript
// 连接WebSocket终端
const ws = new WebSocket('ws://localhost:8088/ws/terminal/GPU-Server-1');

ws.onopen = function() {
    console.log('终端连接已建立');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'output') {
        console.log('终端输出:', data.message);
    }
};

// 发送命令
ws.send(JSON.stringify({
    type: 'input',
    data: 'ls -la\n'
}));
```

### 4. 执行远程命令

```python
import requests

# 执行GPU查询命令
command_data = {
    "command": "nvidia-smi --query-gpu=name,temperature.gpu --format=csv",
    "timeout": 10
}

response = requests.post(
    "http://localhost:8088/api/ssh/servers/GPU-Server-1/execute",
    json=command_data
)

result = response.json()["data"]
print(f"命令输出: {result['stdout']}")
```

### 5. VLLM服务管理

```python
import requests

# 环境诊断
response = requests.get("http://localhost:8088/api/vllm/diagnose/GPU-Server-1")
diagnosis = response.json()["data"]
print(f"GPU可用: {diagnosis['gpu_available']}")

# 发现模型
response = requests.get("http://localhost:8088/api/vllm/models/GPU-Server-1")
models = response.json()["data"]["discovered_models"]
print(f"发现 {len(models)} 个模型")

# 启动VLLM服务
vllm_config = {
    "server_name": "GPU-Server-1",
    "model_path": "/path/to/chatglm3-6b",
    "port": 8000,
    "gpu_indices": "0",
    "tensor_parallel_size": 1,
    "max_model_len": 4096,
    "gpu_memory_utilization": 0.9,
    "dtype": "auto"
}

response = requests.post(
    "http://localhost:8088/api/vllm/start",
    json=vllm_config
)
print(response.json()["message"])

# 检查服务状态
response = requests.get("http://localhost:8088/api/vllm/status/GPU-Server-1")
status = response.json()["data"]
print(f"运行中服务: {len(status['running_services'])}")

# 健康检查
response = requests.get("http://localhost:8088/api/vllm/health/GPU-Server-1/8000")
health = response.json()["data"]
print(f"服务健康状态: {health['status']}")
```

### 6. 配置模板管理

```python
import requests

# 保存配置模板
config_template = {
    "name": "ChatGLM3-6B-Template",
    "description": "ChatGLM3-6B优化配置",
    "config": {
        "model_path": "/path/to/chatglm3-6b",
        "tensor_parallel_size": 1,
        "max_model_len": 8192,
        "gpu_memory_utilization": 0.85,
        "dtype": "half"
    }
}

response = requests.post(
    "http://localhost:8088/api/vllm/save-model",
    json=config_template
)
print("配置模板已保存")

# 获取已保存的配置
response = requests.get("http://localhost:8088/api/vllm/saved-models")
templates = response.json()["data"]
print(f"已保存 {len(templates)} 个配置模板")
```

## 🌐 Web界面功能

### 系统监控页面
- 实时GPU使用率图表
- 系统资源监控面板
- 服务器状态概览
- 历史数据趋势图

### 控制台仪表板
- 综合数据展示
- 快速操作面板
- 模型服务管理
- 系统状态摘要

### 开发者工具页面
- API文档链接
- 原始数据访问
- 系统诊断工具
- 故障排查指南
- 增强的GPU环境诊断
- Python环境检测

### WebSocket终端页面
- 实时SSH终端
- 多服务器会话管理
- 交互式命令执行
- 终端历史记录

### VLLM管理页面（新功能）
- 专业的VLLM服务管理界面
- 完整的启动参数配置
- 智能参数预设（小/中/大模型）
- 配置模板保存和加载
- 实时性能监控面板
- 服务健康检查
- 环境诊断工具
- 模型发现和管理
- 服务日志查看
- 批量操作支持

## 🚨 故障排除

### 常见问题

1. **SSH连接失败**
   - 检查服务器IP、端口、用户名密码是否正确
   - 确认服务器SSH服务已启动
   - 检查防火墙设置

2. **GPU监控无数据**
   - 确认服务器已安装nvidia-smi
   - 检查GPU驱动是否正常
   - 验证SSH连接是否正常

3. **模型启动失败**
   - 检查模型路径是否存在
   - 确认vllm环境已安装
   - 查看端口是否被占用

4. **WebSocket连接失败**
   - 检查浏览器WebSocket支持
   - 确认服务器端口配置正确
   - 查看网络连接状态

5. **数据库错误**
   - 检查数据库文件权限
   - 确认SQLite支持
   - 清理旧的数据库文件

6. **VLLM环境问题**
   - 使用环境诊断功能检查GPU可用性
   - 确认PyTorch CUDA支持正常
   - 检查Python环境和依赖包
   - 验证CUDA运行时库安装

7. **VLLM服务启动失败**
   - 检查模型路径和权限
   - 确认端口未被占用
   - 验证GPU内存是否充足
   - 查看服务日志获取详细错误信息

8. **配置参数错误**
   - 使用智能预设避免参数冲突
   - 检查张量并行度设置
   - 验证GPU内存利用率配置
   - 确认数据类型和量化设置兼容性

### 日志查看

```bash
# 查看应用日志
tail -f aiplatform.log

# 查看详细错误信息
python run.py --log-level debug

# 运行API测试
python debug_test/test_api.py

# VLLM管理测试
python debug_test/test_vllm_management.py

# 增强GPU诊断
python debug_test/gpu_diagnosis_enhanced.py

# 快速诊断工具
python debug_test/quick_diagnosis.py

# 检查模型服务状态
python debug_test/check_model_services.py
```

## 🔒 安全注意事项

1. **密码安全**: 配置文件中的密码以明文存储，请确保文件权限设置正确
2. **网络安全**: 生产环境建议使用HTTPS和防火墙
3. **SSH密钥**: 推荐使用SSH密钥而非密码认证
4. **访问控制**: 考虑添加身份验证和授权机制
5. **WebSocket安全**: 生产环境建议添加WebSocket认证

## 🆕 最新更新

### v1.2.0 (当前版本)
- ✨ 新增独立VLLM管理页面
- ✨ 完整的VLLM参数配置支持
- ✨ 智能参数预设和配置模板
- ✨ 增强的GPU环境诊断功能
- ✨ 实时性能监控和健康检查
- ✨ 配置保存和批量操作
- ✨ 模块化架构优化
- ✨ 企业级功能完善

### v1.1.0
- ✨ 新增WebSocket实时终端功能
- ✨ 新增开发者工具页面
- ✨ 页面模块化重构
- ✨ 实时数据推送功能
- ✨ 改进的配置管理系统
- ✨ 增强的错误处理和日志记录

### v1.0.0
- 🎉 初始版本发布
- ✅ GPU服务器监控
- ✅ 模型服务管理
- ✅ SSH远程控制
- ✅ 基础Web界面

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

### 开发环境设置

```bash
# 克隆项目
git clone <repository-url>
cd aiplatform_py

# 安装开发依赖
pip install -r requirements.txt

# 运行API测试
python debug_test/test_api.py

# 启动开发服务器
python run.py
```

## 📄 许可证

本项目基于MIT许可证开源。

## 📞 技术支持

如有问题或建议，请通过以下方式联系：

- 创建GitHub Issue
- 发送邮件到项目维护者
- 查看项目Wiki文档

---

**感谢使用AI平台管理系统！** 🎉