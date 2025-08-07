#!/usr/bin/env python3
"""检查模型服务数据库记录"""

import sqlite3
import json
from datetime import datetime

def check_model_services():
    """检查模型服务记录"""
    try:
        conn = sqlite3.connect('aiplatform.db')
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='model_services'")
        table_exists = cursor.fetchone() is not None
        print(f"model_services表存在: {table_exists}")
        
        if not table_exists:
            print("表不存在，退出检查")
            return
        
        # 获取表结构
        cursor.execute("PRAGMA table_info(model_services)")
        columns = cursor.fetchall()
        print("\n表结构:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # 获取记录总数
        cursor.execute("SELECT COUNT(*) FROM model_services")
        total_count = cursor.fetchone()[0]
        print(f"\n总记录数: {total_count}")
        
        # 获取最近的记录
        cursor.execute("""
            SELECT id, name, model_path, port, status, extra_params, created_at 
            FROM model_services 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        records = cursor.fetchall()
        
        print("\n最近5条模型服务记录:")
        for r in records:
            extra_params = r[5] if r[5] else '{}'
            try:
                if isinstance(extra_params, str):
                    params_dict = json.loads(extra_params)
                else:
                    params_dict = extra_params
                params_str = json.dumps(params_dict, ensure_ascii=False, indent=2)
            except:
                params_str = str(extra_params)
            
            print(f"\n  记录 {r[0]}:")
            print(f"    名称: {r[1]}")
            print(f"    路径: {r[2]}")
            print(f"    端口: {r[3]}")
            print(f"    状态: {r[4]}")
            print(f"    创建时间: {r[6]}")
            print(f"    额外参数: {params_str}")
        
        conn.close()
        
    except Exception as e:
        print(f"检查失败: {e}")

if __name__ == "__main__":
    check_model_services()