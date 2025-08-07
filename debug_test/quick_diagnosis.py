#!/usr/bin/env python3
"""VLLM环境快速诊断脚本"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import AiPlatformConfig
from app.services.vllm_service import get_vllm_manager

def print_banner():
    """打印诊断横幅"""
    print("=" * 60)
    print("🔍 VLLM环境快速诊断工具")
    print("=" * 60)

def diagnose_server(server_name: str):
    """诊断指定服务器"""
    print(f"\n📡 正在诊断服务器: {server_name}")
    print("-" * 40)
    
    try:
        config = AiPlatformConfig()
        vllm_manager = get_vllm_manager(config)
        
        # 获取服务器配置
        server_config = None
        for server in config.gpu_servers:
            if server.name == server_name:
                server_config = server
                break
        
        if not server_config:
            print(f"❌ 错误: 服务器 '{server_name}' 在配置中不存在")
            print("\n💡 可用的服务器:")
            for server in config.gpu_servers:
                status = "✅ 启用" if server.enabled else "❌ 禁用"
                print(f"   • {server.name} ({server.host}) - {status}")
            return False
        
        if not server_config.enabled:
            print(f"⚠️  警告: 服务器 '{server_name}' 已禁用")
            return False
        
        # 执行诊断
        print("🔎 开始环境检测...")
        diagnosis = vllm_manager.diagnose_server_environment(server_config)
        
        # 显示结果
        print("\n📋 诊断结果:")
        
        items = [
            ("SSH连接", diagnosis['ssh_connection']),
            ("Python环境", diagnosis['python_version'] is not None),
            ("VLLM安装", diagnosis['vllm_installed']),
            ("GPU可用性", diagnosis['gpu_available']),
            ("NVIDIA驱动", diagnosis['nvidia_smi']),
            ("模型路径", diagnosis['model_path_exists'])
        ]
        
        all_good = True
        for name, status in items:
            icon = "✅" if status else "❌"
            print(f"  {icon} {name}")
            if not status:
                all_good = False
        
        # 显示详细信息
        if diagnosis['python_version']:
            print(f"\n🐍 Python版本: {diagnosis['python_version']}")
        
        if diagnosis['vllm_installed'] and 'vllm_version' in diagnosis:
            print(f"🚀 VLLM版本: {diagnosis['vllm_version']}")
        
        if diagnosis['gpu_info']:
            gpu_info = diagnosis['gpu_info']
            if gpu_info.get('driver_version'):
                print(f"🎮 NVIDIA驱动: {gpu_info['driver_version']}")
            if gpu_info.get('cuda_version'):
                print(f"⚡ CUDA版本: {gpu_info['cuda_version']}")
            if gpu_info.get('gpu_count'):
                print(f"🔢 GPU数量: {gpu_info['gpu_count']}")
        
        # 显示错误和建议
        if diagnosis['errors']:
            print(f"\n⚠️  发现 {len(diagnosis['errors'])} 个问题:")
            for i, error in enumerate(diagnosis['errors'], 1):
                print(f"   {i}. {error}")
        
        if diagnosis['suggestions']:
            print(f"\n💡 修复建议:")
            for i, suggestion in enumerate(diagnosis['suggestions'], 1):
                print(f"   {i}. {suggestion}")
        
        # 总结
        print("\n" + "=" * 40)
        if all_good:
            print("🎉 环境检测通过！可以正常使用VLLM服务")
        else:
            print("⚠️  环境存在问题，请根据上述建议进行修复")
        
        return all_good
        
    except Exception as e:
        print(f"❌ 诊断过程出错: {e}")
        return False

def diagnose_all_servers():
    """诊断所有服务器"""
    try:
        config = AiPlatformConfig()
        enabled_servers = [s for s in config.gpu_servers if s.enabled]
        
        if not enabled_servers:
            print("❌ 未找到已启用的GPU服务器")
            return False
        
        print(f"📡 发现 {len(enabled_servers)} 个已启用的服务器")
        
        results = {}
        for server in enabled_servers:
            results[server.name] = diagnose_server(server.name)
        
        # 汇总结果
        print("\n" + "=" * 60)
        print("📊 诊断汇总:")
        print("-" * 40)
        
        healthy_count = 0
        for server_name, is_healthy in results.items():
            status = "✅ 正常" if is_healthy else "❌ 异常"
            print(f"  • {server_name}: {status}")
            if is_healthy:
                healthy_count += 1
        
        print(f"\n🏆 健康服务器: {healthy_count}/{len(enabled_servers)}")
        
        if healthy_count == len(enabled_servers):
            print("🎉 所有服务器环境正常！")
        elif healthy_count > 0:
            print("⚠️  部分服务器需要修复")
        else:
            print("❌ 所有服务器都存在问题，需要检查配置")
        
        return healthy_count > 0
        
    except Exception as e:
        print(f"❌ 批量诊断出错: {e}")
        return False

def show_config_info():
    """显示配置信息"""
    try:
        config = AiPlatformConfig()
        
        print("\n⚙️  配置信息:")
        print("-" * 40)
        
        print(f"🌐 服务器地址: {config.server_host}:{config.server_port}")
        print(f"📊 数据库: {config.database_url}")
        print(f"🔌 VLLM端口范围: {config.vllm.default_port_range.start}-{config.vllm.default_port_range.end}")
        print(f"💾 GPU内存利用率: {config.vllm.default_gpu_memory_utilization}")
        print(f"📏 默认模型长度: {config.vllm.default_max_model_len}")
        
        print(f"\n🖥️  配置的GPU服务器 ({len(config.gpu_servers)} 个):")
        for server in config.gpu_servers:
            status = "✅ 启用" if server.enabled else "❌ 禁用"
            print(f"  • {server.name}")
            print(f"    地址: {server.host}:{server.port}")
            print(f"    用户: {server.username}")
            print(f"    GPU数量: {server.gpu_count}")
            print(f"    模型路径: {server.model_path}")
            print(f"    状态: {status}")
            print()
    
    except Exception as e:
        print(f"❌ 获取配置信息失败: {e}")

def show_help():
    """显示帮助信息"""
    print("""
📚 使用说明:

🔍 诊断指定服务器:
   python quick_diagnosis.py <服务器名称>
   
🔍 诊断所有服务器:
   python quick_diagnosis.py --all
   
⚙️  显示配置信息:
   python quick_diagnosis.py --config
   
📚 显示帮助:
   python quick_diagnosis.py --help

💡 示例:
   python quick_diagnosis.py GPU-Server-1
   python quick_diagnosis.py --all
   python quick_diagnosis.py --config
   
🚨 常见问题解决:
   1. SSH连接失败 -> 检查服务器地址、端口、用户名和密码
   2. Python未安装 -> 在远程服务器安装Python 3.8+
   3. VLLM未安装 -> 执行: pip install vllm
   4. GPU不可用 -> 检查NVIDIA驱动程序安装
   5. 模型路径不存在 -> 创建目录或检查路径配置
""")

def main():
    """主函数"""
    print_banner()
    
    if len(sys.argv) < 2:
        show_help()
        return
    
    arg = sys.argv[1]
    
    if arg == "--help" or arg == "-h":
        show_help()
    elif arg == "--all":
        diagnose_all_servers()
    elif arg == "--config":
        show_config_info()
    else:
        # 诊断指定服务器
        server_name = arg
        diagnose_server(server_name)

if __name__ == "__main__":
    main() 