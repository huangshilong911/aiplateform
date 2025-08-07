#!/usr/bin/env python3
"""GPU环境修复脚本"""

import sys
import subprocess
sys.path.append('.')

from app.config import AiPlatformConfig
from app.services.ssh_manager import SSHManager

class GPUEnvironmentFixer:
    """GPU环境修复工具"""
    
    def __init__(self):
        self.config = AiPlatformConfig()
        self.ssh_manager = SSHManager()
    
    def print_header(self):
        """打印标题"""
        print("=" * 80)
        print("🔧 GPU环境自动修复工具")
        print("=" * 80)
    
    def fix_server_environment(self, server_name: str):
        """修复指定服务器的GPU环境"""
        print(f"\n🖥️  修复服务器: {server_name}")
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
            print(f"⚠️  警告: 服务器 '{server_name}' 已禁用，跳过修复")
            return False
        
        # 测试连接
        if not self._test_connection(server_config):
            return False
        
        # 诊断当前问题
        issues = self._diagnose_issues(server_config)
        
        if not issues:
            print("✅ 未检测到GPU环境问题")
            return True
        
        print(f"\n🔍 检测到 {len(issues)} 个问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        # 执行修复
        self._apply_fixes(server_config, issues)
        
        # 验证修复结果
        print("\n🔄 验证修复结果...")
        return self._verify_fixes(server_config)
    
    def _test_connection(self, server_config):
        """测试SSH连接"""
        print("\n🔗 测试SSH连接...")
        
        exit_code, _, stderr = self.ssh_manager.execute_command(
            server_config, "echo 'test'", timeout=10
        )
        
        if exit_code == 0:
            print("✅ SSH连接正常")
            return True
        else:
            print(f"❌ SSH连接失败: {stderr}")
            return False
    
    def _diagnose_issues(self, server_config):
        """诊断当前存在的问题"""
        print("\n🔍 诊断GPU环境问题...")
        issues = []
        
        # 检查nvidia-smi
        exit_code, _, _ = self.ssh_manager.execute_command(
            server_config, "nvidia-smi", timeout=10
        )
        if exit_code != 0:
            issues.append("nvidia-smi不可用")
        
        # 检查Python环境
        python_available = False
        for python_exe in ["python", "python3"]:
            exit_code, _, _ = self.ssh_manager.execute_command(
                server_config, f"{python_exe} --version", timeout=5
            )
            if exit_code == 0:
                python_available = True
                break
        
        if not python_available:
            issues.append("Python环境不可用")
        
        # 检查PyTorch
        pytorch_cuda_available = False
        for python_exe in ["python", "python3"]:
            exit_code, stdout, _ = self.ssh_manager.execute_command(
                server_config, 
                f"{python_exe} -c 'import torch; print(torch.cuda.is_available())' 2>/dev/null",
                timeout=15
            )
            if exit_code == 0 and "True" in stdout:
                pytorch_cuda_available = True
                break
        
        if not pytorch_cuda_available:
            issues.append("PyTorch CUDA支持不可用")
        
        # 检查VLLM
        vllm_available = False
        for python_exe in ["python", "python3"]:
            exit_code, _, _ = self.ssh_manager.execute_command(
                server_config,
                f"{python_exe} -c 'import vllm' 2>/dev/null",
                timeout=20
            )
            if exit_code == 0:
                vllm_available = True
                break
        
        if not vllm_available:
            issues.append("VLLM未正确安装")
        
        return issues
    
    def _apply_fixes(self, server_config, issues):
        """应用修复方案"""
        print("\n🔧 开始应用修复方案...")
        
        for issue in issues:
            if "nvidia-smi不可用" in issue:
                self._fix_nvidia_driver(server_config)
            elif "Python环境不可用" in issue:
                self._fix_python_environment(server_config)
            elif "PyTorch CUDA支持不可用" in issue:
                self._fix_pytorch_cuda(server_config)
            elif "VLLM未正确安装" in issue:
                self._fix_vllm_installation(server_config)
    
    def _fix_nvidia_driver(self, server_config):
        """修复NVIDIA驱动问题"""
        print("\n🎮 检查NVIDIA驱动...")
        
        # 检查驱动状态
        exit_code, stdout, _ = self.ssh_manager.execute_command(
            server_config, "lsmod | grep nvidia", timeout=10
        )
        
        if exit_code != 0:
            print("❌ NVIDIA驱动模块未加载")
            print("💡 建议: 请联系系统管理员检查NVIDIA驱动安装")
        else:
            print("✅ NVIDIA驱动模块已加载")
            
            # 检查设备文件
            exit_code, _, _ = self.ssh_manager.execute_command(
                server_config, "ls /dev/nvidia*", timeout=5
            )
            
            if exit_code != 0:
                print("❌ NVIDIA设备文件不存在")
                print("💡 尝试重新加载驱动模块...")
                
                reload_cmds = [
                    "sudo rmmod nvidia_uvm",
                    "sudo rmmod nvidia_drm", 
                    "sudo rmmod nvidia_modeset",
                    "sudo rmmod nvidia",
                    "sudo modprobe nvidia",
                    "sudo modprobe nvidia_modeset",
                    "sudo modprobe nvidia_drm",
                    "sudo modprobe nvidia_uvm"
                ]
                
                for cmd in reload_cmds:
                    exit_code, _, stderr = self.ssh_manager.execute_command(
                        server_config, cmd, timeout=10
                    )
                    if exit_code != 0:
                        print(f"⚠️  命令执行失败: {cmd}")
                        print(f"   错误: {stderr}")
            else:
                print("✅ NVIDIA设备文件存在")
    
    def _fix_python_environment(self, server_config):
        """修复Python环境"""
        print("\n🐍 检查Python环境...")
        
        # 检查Python安装
        for python_exe in ["python3", "python"]:
            exit_code, stdout, _ = self.ssh_manager.execute_command(
                server_config, f"which {python_exe}", timeout=5
            )
            
            if exit_code == 0:
                print(f"✅ 找到Python: {stdout.strip()}")
                
                # 检查版本
                exit_code, version, _ = self.ssh_manager.execute_command(
                    server_config, f"{python_exe} --version", timeout=5
                )
                
                if exit_code == 0:
                    print(f"   版本: {version.strip()}")
                    return
        
        print("❌ 未找到可用的Python环境")
        print("💡 建议: 安装Python 3.8+")
    
    def _fix_pytorch_cuda(self, server_config):
        """修复PyTorch CUDA支持"""
        print("\n🔥 修复PyTorch CUDA支持...")
        
        # 检查当前PyTorch安装
        for python_exe in ["python3", "python"]:
            exit_code, _, _ = self.ssh_manager.execute_command(
                server_config, f"{python_exe} -c 'import torch'", timeout=10
            )
            
            if exit_code == 0:
                print(f"✅ {python_exe} 中已安装PyTorch")
                
                # 检查CUDA支持
                exit_code, cuda_available, _ = self.ssh_manager.execute_command(
                    server_config,
                    f"{python_exe} -c 'import torch; print(torch.cuda.is_available())'",
                    timeout=10
                )
                
                if exit_code == 0:
                    if "True" in cuda_available:
                        print("✅ PyTorch CUDA支持正常")
                        return
                    else:
                        print("❌ PyTorch不支持CUDA")
                        print("💡 可能安装的是CPU版本的PyTorch")
                        
                        # 获取CUDA版本信息
                        exit_code, cuda_version, _ = self.ssh_manager.execute_command(
                            server_config, "nvidia-smi | grep 'CUDA Version'", timeout=5
                        )
                        
                        if exit_code == 0:
                            print(f"   系统CUDA版本: {cuda_version.strip()}")
                            print("   建议重新安装支持CUDA的PyTorch版本")
                        
                        # 提供安装命令建议
                        print("\n💡 修复命令建议:")
                        print(f"   {python_exe} -m pip uninstall torch torchvision torchaudio -y")
                        print(f"   {python_exe} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
                else:
                    print(f"❌ {python_exe} PyTorch导入失败")
            else:
                print(f"❌ {python_exe} 中未安装PyTorch")
                
                print(f"\n💡 为 {python_exe} 安装PyTorch:")
                install_cmd = f"{python_exe} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
                print(f"   {install_cmd}")
                
                # 可选：自动执行安装（需要用户确认）
                response = input(f"是否自动执行安装命令？(y/N): ")
                if response.lower() == 'y':
                    print("🔄 开始安装PyTorch...")
                    exit_code, stdout, stderr = self.ssh_manager.execute_command(
                        server_config, install_cmd, timeout=300  # 5分钟超时
                    )
                    
                    if exit_code == 0:
                        print("✅ PyTorch安装完成")
                    else:
                        print(f"❌ PyTorch安装失败: {stderr}")
    
    def _fix_vllm_installation(self, server_config):
        """修复VLLM安装"""
        print("\n🚀 修复VLLM安装...")
        
        # 检查VLLM安装
        for python_exe in ["python3", "python"]:
            exit_code, _, _ = self.ssh_manager.execute_command(
                server_config, f"{python_exe} -c 'import vllm'", timeout=15
            )
            
            if exit_code == 0:
                print(f"✅ {python_exe} 中已安装VLLM")
                
                # 检查版本
                exit_code, version, _ = self.ssh_manager.execute_command(
                    server_config,
                    f"{python_exe} -c 'import vllm; print(vllm.__version__)'",
                    timeout=10
                )
                
                if exit_code == 0:
                    print(f"   VLLM版本: {version.strip()}")
                return
            else:
                print(f"❌ {python_exe} 中未安装VLLM")
                
                print(f"\n💡 为 {python_exe} 安装VLLM:")
                install_cmd = f"{python_exe} -m pip install vllm"
                print(f"   {install_cmd}")
                
                # 可选：自动执行安装
                response = input(f"是否自动执行VLLM安装命令？(y/N): ")
                if response.lower() == 'y':
                    print("🔄 开始安装VLLM...")
                    exit_code, stdout, stderr = self.ssh_manager.execute_command(
                        server_config, install_cmd, timeout=600  # 10分钟超时
                    )
                    
                    if exit_code == 0:
                        print("✅ VLLM安装完成")
                    else:
                        print(f"❌ VLLM安装失败: {stderr}")
    
    def _verify_fixes(self, server_config):
        """验证修复结果"""
        print("\n✅ 最终验证...")
        
        # 重新检查GPU可用性
        exit_code, stdout, _ = self.ssh_manager.execute_command(
            server_config,
            "python3 -c 'import torch; print(f\"GPU可用: {torch.cuda.is_available()}\"); print(f\"GPU数量: {torch.cuda.device_count()}\")'",
            timeout=15
        )
        
        if exit_code == 0:
            print("📊 GPU检测结果:")
            for line in stdout.strip().split('\n'):
                if line.strip():
                    if "GPU可用: True" in line:
                        print(f"   ✅ {line.strip()}")
                    elif "GPU可用: False" in line:
                        print(f"   ❌ {line.strip()}")
                    else:
                        print(f"   📋 {line.strip()}")
            
            return "GPU可用: True" in stdout
        else:
            print("❌ GPU检测失败")
            return False
    
    def fix_all_servers(self):
        """修复所有启用的服务器"""
        self.print_header()
        
        enabled_servers = [s for s in self.config.gpu_servers if s.enabled]
        
        if not enabled_servers:
            print("❌ 没有启用的GPU服务器")
            return
        
        print(f"📊 发现 {len(enabled_servers)} 个启用的服务器")
        
        for server in enabled_servers:
            success = self.fix_server_environment(server.name)
            if success:
                print(f"✅ 服务器 {server.name} 修复成功")
            else:
                print(f"❌ 服务器 {server.name} 修复失败")
        
        print("\n" + "=" * 80)
        print("🏁 修复完成")
        print("=" * 80)

def main():
    """主函数"""
    fixer = GPUEnvironmentFixer()
    
    if len(sys.argv) == 2:
        server_name = sys.argv[1]
        fixer.print_header()
        fixer.fix_server_environment(server_name)
    else:
        fixer.fix_all_servers()

if __name__ == "__main__":
    main() 