#!/usr/bin/env python3
"""检查GPU-Server-2的在线状态"""

import sqlite3
from datetime import datetime, timedelta
import os

def check_server_status():
    # 连接数据库
    db_path = os.path.join(os.path.dirname(__file__), '..', 'aiplatform.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查询GPU-Server-2的最新系统资源记录
    cursor.execute('''
        SELECT server_name, cpu_usage, memory_percent, created_at, updated_at 
        FROM system_resources 
        WHERE server_name = "GPU-Server-2" 
        ORDER BY updated_at DESC 
        LIMIT 5
    ''')

    records = cursor.fetchall()
    print("=== GPU-Server-2 最新系统资源记录 ===")
    if records:
        for i, record in enumerate(records):
            print(f"记录 {i+1}:")
            print(f"  服务器: {record[0]}")
            print(f"  CPU: {record[1]}%")
            print(f"  内存: {record[2]}%") 
            print(f"  创建时间: {record[3]}")
            print(f"  更新时间: {record[4]}")
            print("  ---")
    else:
        print("  无记录")

    # 计算时间差
    if records:
        latest_record = records[0]
        updated_at = datetime.fromisoformat(latest_record[4])
        now = datetime.now()
        diff_seconds = (now - updated_at).total_seconds()
        print(f"\n=== 状态分析 ===")
        print(f"最新记录时间: {latest_record[4]}")
        print(f"当前时间: {now}")
        print(f"时间差: {diff_seconds:.1f} 秒 ({diff_seconds/60:.1f} 分钟)")
        status = "在线" if diff_seconds < 300 else "离线"
        print(f"按5分钟规则应显示为: {status}")
        
        # 如果有CPU/内存数据，说明SSH连接过
        if latest_record[1] is not None or latest_record[2] is not None:
            print("✅ 数据库中有系统资源数据，说明SSH曾经连接成功")
        else:
            print("❌ 数据库中无系统资源数据，说明SSH连接失败")

    # 查看所有服务器的记录数量对比
    print(f"\n=== 所有服务器记录数量对比 ===")
    cursor.execute('SELECT server_name, COUNT(*) FROM system_resources GROUP BY server_name')
    server_counts = cursor.fetchall()
    for server_name, count in server_counts:
        print(f"  {server_name}: {count} 条记录")

    conn.close()

if __name__ == "__main__":
    check_server_status() 