#!/usr/bin/env python3
"""GPU监控调试脚本"""

import sys
sys.path.append('.')

from app.config import AiPlatformConfig
from app.services.ssh_manager import SSHManager

def test_gpu_monitoring():
    """测试GPU监控功能"""
    print("🔍 开始GPU监控诊断...")
    
    try:
        # 1. 加载配置
        config = AiPlatformConfig()
        print(f"✅ 配置加载成功")
        print(f"   GPU服务器数量: {len(config.gpu_servers)}")
        
        # 2. 创建SSH管理器
        ssh_manager = SSHManager()
        print(f"✅ SSH管理器初始化成功")
        
        # 3. 测试每个服务器
        for server_config in config.gpu_servers:
            if not server_config.enabled:
                print(f"⚠️  跳过禁用的服务器: {server_config.name}")
                continue
                
            print(f"\n🔗 测试服务器: {server_config.name} ({server_config.host})")
            
            # 测试基本连接
            exit_code, stdout, stderr = ssh_manager.execute_command(
                server_config, "echo 'test'", timeout=10
            )
            
            if exit_code != 0:
                print(f"❌ SSH连接失败:")
                print(f"   退出码: {exit_code}")
                print(f"   错误: {stderr}")
                continue
            
            print(f"✅ SSH连接正常")
            
            # 测试nvidia-smi命令
            nvidia_cmd = "nvidia-smi --query-gpu=index,name,uuid,utilization.gpu,utilization.memory,memory.total,memory.used,memory.free,temperature.gpu,power.draw,power.limit --format=csv,noheader,nounits"
            
            print("🔍 执行nvidia-smi命令...")
            exit_code, stdout, stderr = ssh_manager.execute_command(
                server_config, nvidia_cmd, timeout=30
            )
            
            if exit_code != 0:
                print(f"❌ nvidia-smi命令执行失败:")
                print(f"   退出码: {exit_code}")
                print(f"   错误: {stderr}")
                
                # 尝试简单的nvidia-smi
                print("🔍 尝试简单的nvidia-smi命令...")
                exit_code, stdout, stderr = ssh_manager.execute_command(
                    server_config, "nvidia-smi", timeout=30
                )
                
                if exit_code != 0:
                    print(f"❌ 简单nvidia-smi也失败:")
                    print(f"   退出码: {exit_code}")
                    print(f"   错误: {stderr}")
                else:
                    print(f"✅ 简单nvidia-smi成功，可能是查询参数问题")
                    print(f"   输出: {stdout[:200]}...")
                continue
            
            print(f"✅ nvidia-smi命令执行成功")
            print(f"   输出行数: {len(stdout.strip().split('\n'))}")
            
            # 解析输出
            lines = stdout.strip().split('\n')
            print("🔍 解析GPU数据:")
            
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                    
                print(f"   GPU {i}: {line}")
                
                try:
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) >= 11:
                        print(f"     ✅ 数据解析成功: {len(parts)} 个字段")
                        print(f"     - GPU索引: {parts[0]}")
                        print(f"     - GPU名称: {parts[1]}")
                        print(f"     - 使用率: {parts[3]}%")
                        print(f"     - 内存使用率: {parts[4]}%")
                        print(f"     - 温度: {parts[8]}°C")
                    else:
                        print(f"     ❌ 数据字段不足: {len(parts)} 个字段")
                        print(f"     原始数据: {parts}")
                        
                except Exception as e:
                    print(f"     ❌ 数据解析失败: {e}")
                    print(f"     原始行: {line}")
        
        print("\n🎉 GPU监控诊断完成")
        
    except Exception as e:
        print(f"❌ 诊断过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gpu_monitoring() 