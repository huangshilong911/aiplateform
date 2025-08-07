#!/usr/bin/env python3
"""VLLM模型服务管理功能测试脚本"""

import sys
import os
import asyncio
import json
import requests
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import AiPlatformConfig
from app.services.vllm_service import get_vllm_manager
from app.services.ssh_manager import get_ssh_manager

class VllmTester:
    """VLLM功能测试器"""
    
    def __init__(self):
        self.config = AiPlatformConfig()
        self.vllm_manager = get_vllm_manager(self.config)
        self.ssh_manager = get_ssh_manager()
        self.base_url = f"http://{self.config.server_host}:{self.config.server_port}"
        
    def test_server_diagnosis(self, server_name: str):
        """测试服务器环境诊断"""
        print(f"\n=== 测试服务器环境诊断: {server_name} ===")
        
        try:
            # 获取服务器配置
            server_config = None
            for server in self.config.gpu_servers:
                if server.name == server_name:
                    server_config = server
                    break
            
            if not server_config:
                print(f"❌ 服务器 '{server_name}' 不存在")
                return False
            
            # 执行诊断
            diagnosis = self.vllm_manager.diagnose_server_environment(server_config)
            
            print("📋 诊断结果:")
            print(f"  SSH连接: {'✅' if diagnosis['ssh_connection'] else '❌'}")
            print(f"  Python版本: {diagnosis.get('python_version', '未检测到')}")
            print(f"  VLLM安装: {'✅' if diagnosis['vllm_installed'] else '❌'}")
            print(f"  GPU可用: {'✅' if diagnosis['gpu_available'] else '❌'}")
            print(f"  NVIDIA-SMI: {'✅' if diagnosis['nvidia_smi'] else '❌'}")
            print(f"  模型路径: {'✅' if diagnosis['model_path_exists'] else '❌'}")
            
            if diagnosis['errors']:
                print("⚠️  发现的问题:")
                for error in diagnosis['errors']:
                    print(f"    • {error}")
            
            if diagnosis['suggestions']:
                print("💡 修复建议:")
                for suggestion in diagnosis['suggestions']:
                    print(f"    • {suggestion}")
                    
            return len(diagnosis['errors']) == 0
            
        except Exception as e:
            print(f"❌ 诊断过程出错: {e}")
            return False
    
    def test_api_diagnosis(self, server_name: str):
        """测试API诊断接口"""
        print(f"\n=== 测试API诊断接口: {server_name} ===")
        
        try:
            url = f"{self.base_url}/api/vllm/diagnosis/{server_name}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    print("✅ API诊断接口正常")
                    diagnosis = data['data']
                    print(f"  SSH连接: {'✅' if diagnosis['ssh_connection'] else '❌'}")
                    print(f"  VLLM安装: {'✅' if diagnosis['vllm_installed'] else '❌'}")
                    return True
                else:
                    print(f"❌ API返回失败: {data.get('message', '未知错误')}")
                    return False
            else:
                print(f"❌ API请求失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API测试出错: {e}")
            return False
    
    def test_model_discovery(self, server_name: str):
        """测试模型发现功能"""
        print(f"\n=== 测试模型发现功能: {server_name} ===")
        
        try:
            url = f"{self.base_url}/api/vllm/models/{server_name}"
            response = requests.get(url, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    models = data['data']['discovered_models']
                    print(f"✅ 发现 {len(models)} 个模型:")
                    for model in models[:5]:  # 只显示前5个
                        print(f"  📁 {model['name']} ({model['size']})")
                        print(f"     路径: {model['path']}")
                    
                    if len(models) > 5:
                        print(f"  ... 还有 {len(models) - 5} 个模型")
                        
                    return len(models) > 0
                else:
                    print(f"❌ 模型发现失败: {data.get('message', '未知错误')}")
                    return False
            else:
                print(f"❌ 模型发现请求失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 模型发现测试出错: {e}")
            return False
    
    def test_port_check(self, server_name: str):
        """测试端口检查功能"""
        print(f"\n=== 测试端口检查功能: {server_name} ===")
        
        try:
            url = f"{self.base_url}/api/vllm/ports/{server_name}?start_port=8000&count=5"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    available_ports = data['data']['available_ports']
                    print(f"✅ 检查端口8000-8004，{len(available_ports)}个可用")
                    print(f"  可用端口: {available_ports}")
                    return True
                else:
                    print(f"❌ 端口检查失败: {data.get('message', '未知错误')}")
                    return False
            else:
                print(f"❌ 端口检查请求失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 端口检查测试出错: {e}")
            return False
    
    def test_service_listing(self, server_name: str):
        """测试服务列表功能"""
        print(f"\n=== 测试服务列表功能: {server_name} ===")
        
        try:
            url = f"{self.base_url}/api/vllm/list/{server_name}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    services = data['data']['services']
                    print(f"✅ 当前运行 {len(services)} 个VLLM服务")
                    
                    for service in services:
                        print(f"  🟢 PID: {service['pid']}, 端口: {service.get('port', '未知')}")
                        print(f"     CPU: {service['cpu_usage']}%, 内存: {service['memory_usage']}%")
                    
                    return True
                else:
                    print(f"❌ 服务列表获取失败: {data.get('message', '未知错误')}")
                    return False
            else:
                print(f"❌ 服务列表请求失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 服务列表测试出错: {e}")
            return False
    
    def test_vllm_start_stop(self, server_name: str, model_path: str = None):
        """测试VLLM服务启动和停止"""
        print(f"\n=== 测试VLLM服务启动停止: {server_name} ===")
        
        if not model_path:
            print("⚠️  未提供模型路径，跳过启动停止测试")
            return True
        
        test_port = 8001
        
        try:
            # 1. 启动服务
            print("🚀 启动VLLM服务...")
            start_data = {
                "server_name": server_name,
                "model_path": model_path,
                "port": test_port,
                "gpu_indices": "0",
                "max_model_len": 2048,
                "gpu_memory_utilization": 0.8,
                "tensor_parallel_size": 1
            }
            
            response = requests.post(
                f"{self.base_url}/api/vllm/start",
                json=start_data,
                timeout=90
            )
            
            if response.status_code != 200:
                print(f"❌ 启动请求失败: HTTP {response.status_code}")
                return False
            
            start_result = response.json()
            if not start_result['success']:
                print(f"❌ 启动失败: {start_result.get('message', '未知错误')}")
                return False
            
            pid = start_result['data']['pid']
            print(f"✅ 服务启动成功, PID: {pid}, 端口: {test_port}")
            
            # 2. 等待一段时间
            print("⏱️  等待服务稳定...")
            time.sleep(10)
            
            # 3. 检查服务状态
            print("🔍 检查服务状态...")
            status_response = requests.get(
                f"{self.base_url}/api/vllm/status/{server_name}?pid={pid}&port={test_port}",
                timeout=30
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data['success']:
                    status = status_data['data']['status']
                    print(f"  运行状态: {'✅' if status['running'] else '❌'}")
                    print(f"  进程存在: {'✅' if status['pid_exists'] else '❌'}")
                    print(f"  端口占用: {'✅' if status['port_in_use'] else '❌'}")
            
            # 4. 停止服务
            print("🛑 停止VLLM服务...")
            stop_data = {
                "server_name": server_name,
                "pid": pid
            }
            
            stop_response = requests.post(
                f"{self.base_url}/api/vllm/stop",
                json=stop_data,
                timeout=30
            )
            
            if stop_response.status_code == 200:
                stop_result = stop_response.json()
                if stop_result['success']:
                    print("✅ 服务停止成功")
                    return True
                else:
                    print(f"❌ 停止失败: {stop_result.get('message', '未知错误')}")
                    return False
            else:
                print(f"❌ 停止请求失败: HTTP {stop_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 启动停止测试出错: {e}")
            return False
    
    def run_all_tests(self, server_name: str, model_path: str = None):
        """运行所有测试"""
        print(f"🧪 开始VLLM管理功能测试 - 服务器: {server_name}")
        print("=" * 50)
        
        tests = [
            ("服务器环境诊断", lambda: self.test_server_diagnosis(server_name)),
            ("API诊断接口", lambda: self.test_api_diagnosis(server_name)),
            ("模型发现功能", lambda: self.test_model_discovery(server_name)),
            ("端口检查功能", lambda: self.test_port_check(server_name)),
            ("服务列表功能", lambda: self.test_service_listing(server_name)),
        ]
        
        # 如果提供了模型路径，添加启动停止测试
        if model_path:
            tests.append(("VLLM启动停止", lambda: self.test_vllm_start_stop(server_name, model_path)))
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} - 通过")
                else:
                    print(f"❌ {test_name} - 失败")
            except Exception as e:
                print(f"❌ {test_name} - 异常: {e}")
        
        print("\n" + "=" * 50)
        print(f"🏆 测试完成: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！VLLM管理功能正常工作")
        else:
            print("⚠️  部分测试失败，请检查相关配置和环境")
        
        return passed == total

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python test_vllm_management.py <服务器名称> [模型路径]")
        print("示例: python test_vllm_management.py GPU-Server-1 /path/to/model")
        return
    
    server_name = sys.argv[1]
    model_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    tester = VllmTester()
    tester.run_all_tests(server_name, model_path)

if __name__ == "__main__":
    main() 