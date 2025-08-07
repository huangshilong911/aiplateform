#!/usr/bin/env python3
"""增强的GPU环境诊断脚本"""

import sys
import json
sys.path.append('.')

from app.config import AiPlatformConfig
from app.services.ssh_manager import SSHManager

class GPUDiagnosticTool:
    """GPU诊断工具"""
    
    def __init__(self):
        self.config = AiPlatformConfig()
        self.ssh_manager = SSHManager()
    
    def print_header(self):
        """打印标题"""
        print("=" * 80)
        print("🔍 GPU环境增强诊断工具")
        print("=" * 80)
    
    def diagnose_server(self, server_name: str):
        """诊断指定服务器的GPU环境"""
        print(f"\n🖥️  诊断服务器: {server_name}")
        print("-" * 60)
        
        # 查找服务器配置
        server_config = None
        for server in self.config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
        
        if not server_config:
            print(f"❌ 错误: 未找到服务器配置 '{server_name}'")
            return False
        
        if not server_config.enabled:
            print(f"⚠️  警告: 服务器 '{server_name}' 已禁用")
            return False
        
        print(f"📡 服务器地址: {server_config.host}:{server_config.port}")
        print(f"👤 用户名: {server_config.username}")
        
        # 基础连接测试
        if not self._test_ssh_connection(server_config):
            return False
        
        # GPU硬件检测
        self._check_gpu_hardware(server_config)
        
        # CUDA环境检测
        self._check_cuda_environment(server_config)
        
        # Python环境检测
        self._check_python_environments(server_config)
        
        # PyTorch环境检测
        self._check_pytorch_environments(server_config)
        
        # VLLM环境检测
        self._check_vllm_environment(server_config)
        
        return True
    
    def _test_ssh_connection(self, server_config):
        """测试SSH连接"""
        print("\n🔗 测试SSH连接...")
        
        exit_code, stdout, stderr = self.ssh_manager.execute_command(
            server_config, "echo 'SSH连接正常'", timeout=10
        )
        
        if exit_code == 0:
            print("✅ SSH连接成功")
            return True
        else:
            print(f"❌ SSH连接失败")
            print(f"   退出码: {exit_code}")
            print(f"   错误信息: {stderr}")
            return False
    
    def _check_gpu_hardware(self, server_config):
        """检查GPU硬件"""
        print("\n🎮 检查GPU硬件...")
        
        # 检查nvidia-smi
        exit_code, stdout, stderr = self.ssh_manager.execute_command(
            server_config, "nvidia-smi", timeout=15
        )
        
        if exit_code == 0:
            print("✅ nvidia-smi 可用")
            
            # 获取GPU详细信息
            gpu_cmd = "nvidia-smi --query-gpu=index,name,driver_version,memory.total --format=csv,noheader"
            exit_code, gpu_info, _ = self.ssh_manager.execute_command(
                server_config, gpu_cmd, timeout=10
            )
            
            if exit_code == 0 and gpu_info.strip():
                print("🔍 GPU设备信息:")
                for line in gpu_info.strip().split('\n'):
                    if line.strip():
                        print(f"   • {line.strip()}")
        else:
            print("❌ nvidia-smi 不可用")
            print(f"   错误: {stderr}")
    
    def _check_cuda_environment(self, server_config):
        """检查CUDA环境"""
        print("\n🔧 检查CUDA环境...")
        
        # 检查CUDA版本
        commands = [
            ("nvcc --version", "NVCC编译器"),
            ("cat /usr/local/cuda/version.txt 2>/dev/null || echo '文件不存在'", "CUDA版本文件"),
            ("ls -la /usr/local/cuda*/lib64/libcudart.so* 2>/dev/null || echo '未找到'", "CUDA运行时库"),
            ("echo $CUDA_HOME", "CUDA_HOME环境变量"),
            ("echo $LD_LIBRARY_PATH", "LD_LIBRARY_PATH环境变量")
        ]
        
        for cmd, desc in commands:
            exit_code, stdout, stderr = self.ssh_manager.execute_command(
                server_config, cmd, timeout=10
            )
            
            print(f"  📋 {desc}:")
            if exit_code == 0:
                result = stdout.strip() if stdout.strip() else "(空输出)"
                print(f"     {result}")
            else:
                print(f"     ❌ 执行失败: {stderr}")
    
    def _check_python_environments(self, server_config):
        """检查Python环境"""
        print("\n🐍 检查Python环境...")
        
        python_commands = [
            ("which python", "python路径"),
            ("which python3", "python3路径"),
            ("python --version", "python版本"),
            ("python3 --version", "python3版本")
        ]
        
        for cmd, desc in python_commands:
            exit_code, stdout, stderr = self.ssh_manager.execute_command(
                server_config, cmd, timeout=10
            )
            
            print(f"  📋 {desc}:")
            if exit_code == 0:
                print(f"     ✅ {stdout.strip()}")
            else:
                print(f"     ❌ 失败: {stderr}")
    
    def _check_pytorch_environments(self, server_config):
        """检查PyTorch环境"""
        print("\n🔥 检查PyTorch环境...")
        
        # 检查不同Python环境中的PyTorch
        python_executables = ["python", "python3"]
        
        for python_exe in python_executables:
            print(f"\n  🔍 检查 {python_exe} 环境:")
            
            # 检查PyTorch是否安装
            cmd = f"{python_exe} -c 'import torch; print(f\"PyTorch版本: {{torch.__version__}}\")' 2>/dev/null"
            exit_code, stdout, stderr = self.ssh_manager.execute_command(
                server_config, cmd, timeout=15
            )
            
            if exit_code != 0:
                print(f"     ❌ PyTorch未安装或导入失败")
                continue
            
            print(f"     ✅ {stdout.strip()}")
            
            # 检查CUDA支持
            cuda_cmd = f"{python_exe} -c 'import torch; print(f\"CUDA可用: {{torch.cuda.is_available()}}\"); print(f\"CUDA版本: {{torch.version.cuda}}\"); print(f\"GPU数量: {{torch.cuda.device_count()}}\")' 2>/dev/null"
            exit_code, cuda_info, _ = self.ssh_manager.execute_command(
                server_config, cuda_cmd, timeout=15
            )
            
            if exit_code == 0:
                for line in cuda_info.strip().split('\n'):
                    if line.strip():
                        if "CUDA可用: True" in line:
                            print(f"     ✅ {line.strip()}")
                        elif "CUDA可用: False" in line:
                            print(f"     ❌ {line.strip()}")
                        else:
                            print(f"     📋 {line.strip()}")
            else:
                print(f"     ❌ CUDA检查失败")
            
            # 检查PyTorch安装细节
            detail_cmd = f"{python_exe} -c 'import torch; print(f\"编译标志: {{torch.version.cuda}}\"); print(f\"构建信息: {{torch.__config__.show()}}\")' 2>/dev/null"
            exit_code, detail_info, _ = self.ssh_manager.execute_command(
                server_config, detail_cmd, timeout=15
            )
            
            if exit_code == 0 and detail_info.strip():
                print(f"     📝 详细信息:")
                for line in detail_info.strip().split('\n')[:5]:  # 只显示前5行
                    if line.strip():
                        print(f"        {line.strip()}")
    
    def _check_vllm_environment(self, server_config):
        """检查VLLM环境"""
        print("\n🚀 检查VLLM环境...")
        
        python_executables = ["python", "python3"]
        
        for python_exe in python_executables:
            print(f"\n  🔍 检查 {python_exe} 中的VLLM:")
            
            # 检查VLLM是否安装
            cmd = f"{python_exe} -c 'import vllm; print(f\"VLLM版本: {{vllm.__version__}}\")' 2>/dev/null"
            exit_code, stdout, stderr = self.ssh_manager.execute_command(
                server_config, cmd, timeout=20
            )
            
            if exit_code == 0:
                print(f"     ✅ {stdout.strip()}")
                
                # 检查VLLM GPU支持
                gpu_cmd = f"{python_exe} -c 'from vllm import LLM; print(\"VLLM GPU支持正常\")' 2>/dev/null"
                exit_code, gpu_result, _ = self.ssh_manager.execute_command(
                    server_config, gpu_cmd, timeout=30
                )
                
                if exit_code == 0:
                    print(f"     ✅ VLLM GPU支持正常")
                else:
                    print(f"     ❌ VLLM GPU支持异常")
            else:
                print(f"     ❌ VLLM未安装或导入失败")
    
    def diagnose_all_servers(self):
        """诊断所有启用的服务器"""
        self.print_header()
        
        enabled_servers = [s for s in self.config.gpu_servers if s.enabled]
        
        if not enabled_servers:
            print("❌ 没有启用的GPU服务器")
            return
        
        print(f"📊 发现 {len(enabled_servers)} 个启用的服务器")
        
        for server in enabled_servers:
            success = self.diagnose_server(server.name)
            if not success:
                print(f"\n❌ 服务器 {server.name} 诊断失败")
        
        print("\n" + "=" * 80)
        print("🏁 诊断完成")
        print("=" * 80)

def main():
    """主函数"""
    diagnostic_tool = GPUDiagnosticTool()
    
    if len(sys.argv) == 2:
        server_name = sys.argv[1]
        diagnostic_tool.print_header()
        diagnostic_tool.diagnose_server(server_name)
    else:
        diagnostic_tool.diagnose_all_servers()

if __name__ == "__main__":
    main() 