#!/usr/bin/env python3
"""检查数据库中的GPU数据"""

import sys
import sqlite3
from datetime import datetime
sys.path.append('.')

def check_gpu_data():
    """检查数据库中的GPU数据"""
    print("🔍 检查数据库中的GPU数据...")
    
    try:
        # 连接数据库
        conn = sqlite3.connect('aiplatform.db')
        cursor = conn.cursor()
        
        # 检查gpu_resources表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gpu_resources'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ gpu_resources表不存在")
            return
        
        print("✅ gpu_resources表存在")
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(gpu_resources)")
        columns = cursor.fetchall()
        print(f"📋 表结构 ({len(columns)}列):")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        
        # 检查数据总数
        cursor.execute("SELECT COUNT(*) FROM gpu_resources")
        total_count = cursor.fetchone()[0]
        print(f"📊 总记录数: {total_count}")
        
        if total_count == 0:
            print("⚠️  数据库中没有GPU数据")
            return
        
        # 检查每个服务器的最新数据
        cursor.execute("""
            SELECT server_name, COUNT(*) as count, MAX(created_at) as latest
            FROM gpu_resources 
            GROUP BY server_name
        """)
        
        server_data = cursor.fetchall()
        print(f"\n📈 按服务器统计:")
        for server_name, count, latest in server_data:
            print(f"   {server_name}: {count}条记录, 最新: {latest}")
            
            # 检查最新记录的详细信息
            cursor.execute("""
                SELECT gpu_index, utilization_gpu, temperature, status, created_at
                FROM gpu_resources 
                WHERE server_name = ? 
                ORDER BY created_at DESC 
                LIMIT 5
            """, (server_name,))
            
            recent_records = cursor.fetchall()
            print(f"     最新5条记录:")
            for gpu_idx, util, temp, status, created_at in recent_records:
                print(f"       GPU{gpu_idx}: {util}% 使用率, {temp}°C, {status}, {created_at}")
        
        # 检查最近5分钟的数据
        cursor.execute("""
            SELECT COUNT(*) FROM gpu_resources 
            WHERE datetime(created_at) > datetime('now', '-5 minutes')
        """)
        recent_count = cursor.fetchone()[0]
        print(f"\n🕐 最近5分钟的记录数: {recent_count}")
        
        if recent_count == 0:
            print("❌ 最近5分钟没有新数据，这可能是显示离线的原因")
        else:
            print("✅ 最近5分钟有新数据")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查数据库失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_gpu_data() 