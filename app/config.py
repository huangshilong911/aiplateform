"""AI平台配置管理模块"""

import yaml
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class GpuServerConfig:
    """GPU服务器配置"""
    name: str
    host: str
    username: str
    password: str
    gpu_count: int
    model_path: str
    port: int = 22
    enabled: bool = True

@dataclass
class PortRange:
    """端口范围配置"""
    start: int
    end: int

@dataclass
class VllmConfig:
    """VLLM配置"""
    default_port_range: PortRange
    default_gpu_memory_utilization: float = 0.9
    default_max_model_len: int = 4096

@dataclass
class ModelStorageConfig:
    """模型存储配置"""
    base_path: str
    max_storage_gb: int

@dataclass
class ModelScopeConfig:
    """ModelScope配置"""
    api_url: str
    download_timeout: int = 3600

@dataclass
class MonitoringConfig:
    """监控配置"""
    gpu_interval: int = 5
    gpu_history_retention: int = 24
    system_interval: int = 5
    system_history_retention: int = 24
    token_interval: int = 10
    token_history_retention: int = 168
    gpu_push_interval: int = 5
    system_push_interval: int = 5
    token_push_interval: int = 10
    max_error_count: int = 100

class AiPlatformConfig:
    """AI平台配置管理器"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self._config = None
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            raise ValueError(f"配置文件未找到: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {e}")
    
    @property
    def server_host(self) -> str:
        return self._config.get('server', {}).get('host', '0.0.0.0')
    
    @property
    def server_port(self) -> int:
        return self._config.get('server', {}).get('port', 8088)
    
    @property
    def server_workers(self) -> int:
        return self._config.get('server', {}).get('workers', 4)
    
    @property
    def database_url(self) -> str:
        return self._config.get('database', {}).get('url', 'sqlite:///./aiplatform.db')
    
    @property
    def database_echo(self) -> bool:
        return self._config.get('database', {}).get('echo', False)
    
    @property
    def gpu_servers(self) -> List[GpuServerConfig]:
        """获取GPU服务器配置列表"""
        servers = []
        for server_data in self._config.get('gpu_servers', []):
            servers.append(GpuServerConfig(
                name=server_data['name'],
                host=server_data['host'],
                username=server_data['username'],
                password=server_data['password'],
                gpu_count=server_data['gpu_count'],
                model_path=server_data['model_path'],
                port=server_data.get('port', 22),
                enabled=server_data.get('enabled', True)
            ))
        return servers
    
    @property
    def model_storage(self) -> ModelStorageConfig:
        """获取模型存储配置"""
        storage_config = self._config.get('model_storage', {})
        return ModelStorageConfig(
            base_path=storage_config.get('base_path', './models'),
            max_storage_gb=storage_config.get('max_storage_gb', 1000)
        )
    
    @property
    def modelscope(self) -> ModelScopeConfig:
        """获取ModelScope配置"""
        ms_config = self._config.get('modelscope', {})
        return ModelScopeConfig(
            api_url=ms_config.get('api_url', 'https://www.modelscope.cn'),
            download_timeout=ms_config.get('download_timeout', 3600)
        )
    
    @property
    def vllm(self) -> VllmConfig:
        """获取VLLM配置"""
        vllm_config = self._config.get('vllm', {})
        port_range = vllm_config.get('default_port_range', {})
        return VllmConfig(
            default_port_range=PortRange(
                start=port_range.get('start', 8000),
                end=port_range.get('end', 8100)
            ),
            default_gpu_memory_utilization=vllm_config.get('default_gpu_memory_utilization', 0.9),
            default_max_model_len=vllm_config.get('default_max_model_len', 4096)
        )
    
    @property
    def monitoring(self) -> MonitoringConfig:
        """获取监控配置"""
        mon_config = self._config.get('monitoring', {})
        gpu_config = mon_config.get('gpu', {})
        system_config = mon_config.get('system', {})
        token_config = mon_config.get('token', {})
        websocket_config = mon_config.get('websocket', {})
        
        return MonitoringConfig(
            gpu_interval=gpu_config.get('interval', 5),
            gpu_history_retention=gpu_config.get('history_retention', 24),
            system_interval=system_config.get('interval', 5),
            system_history_retention=system_config.get('history_retention', 24),
            token_interval=token_config.get('interval', 10),
            token_history_retention=token_config.get('history_retention', 168),
            gpu_push_interval=websocket_config.get('gpu_push_interval', 5),
            system_push_interval=websocket_config.get('system_push_interval', 5),
            token_push_interval=websocket_config.get('token_push_interval', 10),
            max_error_count=mon_config.get('max_error_count', 100)
        )
    
    def update_gpu_server(self, server_name: str, updates: Dict[str, Any]) -> bool:
        """更新GPU服务器配置"""
        servers = self._config.get('gpu_servers', [])
        for server in servers:
            if server['name'] == server_name:
                server.update(updates)
                self._save_config()
                return True
        return False
    
    def add_gpu_server(self, server_config: GpuServerConfig) -> bool:
        """添加新的GPU服务器配置"""
        if 'gpu_servers' not in self._config:
            self._config['gpu_servers'] = []
        
        # 检查是否已存在同名服务器
        for server in self._config['gpu_servers']:
            if server['name'] == server_config.name:
                return False
        
        self._config['gpu_servers'].append({
            'name': server_config.name,
            'host': server_config.host,
            'port': server_config.port,
            'username': server_config.username,
            'password': server_config.password,
            'gpu_count': server_config.gpu_count,
            'enabled': server_config.enabled,
            'model_path': server_config.model_path
        })
        self._save_config()
        return True
    
    def remove_gpu_server(self, server_name: str) -> bool:
        """移除GPU服务器配置"""
        servers = self._config.get('gpu_servers', [])
        for i, server in enumerate(servers):
            if server['name'] == server_name:
                del servers[i]
                self._save_config()
                return True
        return False
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            raise ValueError(f"保存配置文件失败: {e}") 