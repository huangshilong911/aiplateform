# AI平台管理系统 (Python版)

基于FastAPI构建的GPU服务器监控和大模型服务管理平台，提供实时监控、模型管理、SSH远程控制等功能。

## 🚀 功能特性

### 需求1: GPU服务器监控
- ✅ 实时监控GPU使用率、内存、温度、功耗等指标
- ✅ 支持多服务器同时监控
- ✅ 历史数据存储和查询
- ✅ GPU状态分析和统计

### 需求2: 模型列表管理
- ✅ 自动发现服务器上的大模型文件
- ✅ 模型信息展示（路径、大小、类型等）
- ✅ 模型分类和组织管理
- ✅ 批量模型操作

### 需求3: 模型服务控制
- ✅ 在线启动/停止大模型服务
- ✅ 支持VLLM框架
- ✅ 服务状态监控
- ✅ 端口管理和资源分配
- ✅ 服务日志查看

### 需求4: SSH远程登录
- ✅ 安全的SSH连接管理
- ✅ 远程命令执行
- ✅ 连接状态监控
- ✅ 多服务器会话管理

### 需求5: 配置管理
- ✅ 动态添加/修改/删除GPU服务器
- ✅ 连接配置测试
- ✅ 系统参数配置
- ✅ 配置文件管理

## 📋 系统要求

- **Python**: 3.8+
- **操作系统**: Linux/Windows/macOS
- **内存**: 至少2GB RAM
- **磁盘**: 至少1GB可用空间

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
│   │   └── config.py      # 配置管理API
│   ├── models/            # 数据模型
│   │   ├── base.py        # 基础模型
│   │   ├── gpu_resource.py    # GPU资源模型
│   │   ├── model_service.py   # 模型服务模型
│   │   └── system_resource.py # 系统资源模型
│   ├── services/          # 业务服务
│   │   ├── ssh_manager.py     # SSH连接管理
│   │   ├── gpu_monitor.py     # GPU监控服务
│   │   ├── system_monitor.py  # 系统监控服务
│   │   └── model_service.py   # 模型服务管理
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库管理
│   └── main.py           # 应用入口
├── config/               # 配置文件
│   └── config.yaml       # 主配置文件
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
```

### 系统监控

```bash
# 获取系统资源状态
GET /api/system/current

# 获取指定服务器系统资源
GET /api/system/servers/{server_name}

# 获取系统历史数据
GET /api/system/history/{server_name}?hours=1
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

### 3. 执行远程命令

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

4. **数据库错误**
   - 检查数据库文件权限
   - 确认SQLite支持
   - 清理旧的数据库文件

### 日志查看

```bash
# 查看应用日志
tail -f aiplatform.log

# 查看详细错误信息
python run.py --log-level debug
```

## 🔒 安全注意事项

1. **密码安全**: 配置文件中的密码以明文存储，请确保文件权限设置正确
2. **网络安全**: 生产环境建议使用HTTPS和防火墙
3. **SSH密钥**: 推荐使用SSH密钥而非密码认证
4. **访问控制**: 考虑添加身份验证和授权机制

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

## 📄 许可证

本项目基于MIT许可证开源。

## 📞 技术支持

如有问题或建议，请通过以下方式联系：

- 创建GitHub Issue
- 发送邮件到项目维护者

---

**感谢使用AI平台管理系统！** 🎉 