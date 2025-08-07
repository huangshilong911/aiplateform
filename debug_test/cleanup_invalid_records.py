#!/usr/bin/env python3
"""清理无效的系统资源记录"""

import sqlite3
from datetime import datetime, timedelta
import os

def cleanup_invalid_records():
    # 连接数据库
    db_path = os.path.join(os.path.dirname(__file__), '..', 'aiplatform.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=== 清理前状态 ===")
    
    # 查看清理前的状态
    cursor.execute('SELECT server_name, COUNT(*) FROM system_resources GROUP BY server_name')
    server_counts = cursor.fetchall()
    for server_name, count in server_counts:
        print(f"  {server_name}: {count} 条记录")

    # 查看GPU-Server-2无效记录数量
    cursor.execute('''
        SELECT COUNT(*) FROM system_resources 
        WHERE server_name = "GPU-Server-2" 
        AND cpu_usage IS NULL 
        AND memory_percent IS NULL
    ''')
    invalid_count = cursor.fetchone()[0]
    print(f"  GPU-Server-2无效记录: {invalid_count} 条")

    # 删除GPU-Server-2的无效记录（CPU和内存都为None的记录）
    print(f"\n=== 开始清理 ===")
    cursor.execute('''
        DELETE FROM system_resources 
        WHERE server_name = "GPU-Server-2" 
        AND cpu_usage IS NULL 
        AND memory_percent IS NULL
    ''')
    
    deleted_count = cursor.rowcount
    print(f"已删除 {deleted_count} 条无效记录")
    
    # 提交更改
    conn.commit()
    
    print(f"\n=== 清理后状态 ===")
    cursor.execute('SELECT server_name, COUNT(*) FROM system_resources GROUP BY server_name')
    server_counts = cursor.fetchall()
    for server_name, count in server_counts:
        print(f"  {server_name}: {count} 条记录")

    # 检查剩余的GPU-Server-2记录
    cursor.execute('''
        SELECT server_name, cpu_usage, memory_percent, created_at, updated_at 
        FROM system_resources 
        WHERE server_name = "GPU-Server-2" 
        ORDER BY updated_at DESC 
        LIMIT 3
    ''')
    
    remaining_records = cursor.fetchall()
    if remaining_records:
        print(f"\n=== 剩余的GPU-Server-2记录 ===")
        for record in remaining_records:
            print(f"  CPU: {record[1]}%, 内存: {record[2]}%, 时间: {record[4]}")
    else:
        print(f"\n✅ GPU-Server-2无剩余记录，现在应该显示为离线")

    conn.close()

if __name__ == "__main__":
    cleanup_invalid_records() 