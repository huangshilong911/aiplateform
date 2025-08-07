#!/usr/bin/env python3
"""测试GPU API接口"""

import requests
import json
from datetime import datetime

def test_gpu_api():
    """测试GPU相关的API接口"""
    print("🔍 测试GPU API接口...")
    
    base_url = "http://localhost:8088"
    
    try:
        # 1. 测试健康检查
        print("\n1️⃣ 测试健康检查 /health")
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ 健康检查通过")
        else:
            print(f"   ❌ 健康检查失败")
            
        # 2. 测试当前GPU状态
        print("\n2️⃣ 测试当前GPU状态 /api/gpu/current")
        response = requests.get(f"{base_url}/api/gpu/current", timeout=10)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API调用成功")
            print(f"   返回数据结构: {type(data)}")
            
            if 'data' in data:
                gpu_list = data['data']
                print(f"   GPU数量: {len(gpu_list)}")
                
                for i, gpu in enumerate(gpu_list):
                    print(f"   GPU {i}:")
                    print(f"     服务器: {gpu.get('server_name')}")
                    print(f"     GPU索引: {gpu.get('gpu_index')}")
                    print(f"     使用率: {gpu.get('utilization_gpu')}%")
                    print(f"     温度: {gpu.get('temperature')}°C")
                    print(f"     状态: {gpu.get('status')}")
                    print(f"     更新时间: {gpu.get('updated_at')}")
            else:
                print(f"   ⚠️  返回数据格式异常: {data}")
        else:
            print(f"   ❌ API调用失败")
            print(f"   响应内容: {response.text}")
            
        # 3. 测试GPU摘要
        print("\n3️⃣ 测试GPU摘要 /api/gpu/summary")
        response = requests.get(f"{base_url}/api/gpu/summary", timeout=10)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ GPU摘要获取成功")
            if 'data' in data:
                summary = data['data']
                print(f"   总GPU数: {summary.get('total_gpus')}")
                print(f"   可用GPU数: {summary.get('available_gpus')}")
                print(f"   忙碌GPU数: {summary.get('busy_gpus')}")
                print(f"   平均使用率: {summary.get('average_gpu_utilization')}%")
                print(f"   服务器数: {summary.get('servers')}")
        else:
            print(f"   ❌ GPU摘要获取失败")
            print(f"   响应内容: {response.text}")
            
        # 4. 测试系统当前状态（对比）
        print("\n4️⃣ 测试系统当前状态 /api/system/current")
        response = requests.get(f"{base_url}/api/system/current", timeout=10)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 系统状态获取成功")
            if 'data' in data:
                systems = data['data']
                print(f"   系统服务器数: {len(systems)}")
                for system in systems:
                    print(f"   服务器: {system.get('server_name')}")
                    print(f"     状态: {system.get('server_status', '未知')}")
                    print(f"     CPU使用率: {system.get('cpu_usage')}%")
                    print(f"     内存使用率: {system.get('memory_percent')}%")
        else:
            print(f"   ❌ 系统状态获取失败")
            
    except requests.exceptions.ConnectinError:
        print("❌ 无法连接到服务器，请检查服务是否启动")
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")

if __name__ == "__main__":
    test_gpu_api() 