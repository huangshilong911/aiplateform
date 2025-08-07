#!/usr/bin/env python3
"""
AI平台管理系统启动脚本

使用方法：
    python run.py

环境要求：
    - Python 3.8+
    - 安装requirements.txt中的依赖包
    - 配置config/config.yaml文件
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("aiplatform.log", encoding='utf-8')
        ]
    )

def check_dependencies():
    """检查必要的依赖"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'paramiko',
        'psutil',
        'pydantic',
        'yaml'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少必要依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ 依赖包检查通过")

def check_config():
    """检查配置文件"""
    config_file = project_root / "config" / "config.yaml"
    if not config_file.exists():
        print(f"❌ 配置文件不存在: {config_file}")
        print("请创建配置文件 config/config.yaml")
        sys.exit(1)
    
    print("✅ 配置文件检查通过")

def create_directories():
    """创建必要的目录"""
    directories = [
        project_root / "models",
        project_root / "logs",
        project_root / "data"
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
    
    print("✅ 目录结构检查通过")

def main():
    """主函数"""
    print("🚀 正在启动AI平台管理系统...")
    print("=" * 50)
    
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 检查环境
        check_dependencies()
        check_config()
        create_directories()
        
        print("=" * 50)
        print("✅ 环境检查完成，正在启动服务器...")
        
        # 导入并启动应用
        import uvicorn
        from app.config import AiPlatformConfig
        
        # 加载配置
        config = AiPlatformConfig()
        
        print(f"🌐 服务器地址: http://{config.server_host}:{config.server_port}")
        print(f"📚 API文档: http://{config.server_host}:{config.server_port}/docs")
        print(f"🔧 健康检查: http://{config.server_host}:{config.server_port}/health")
        print("=" * 50)
        
        # 启动服务器
        uvicorn.run(
            "app.main:app",
            host=config.server_host,
            port=config.server_port,
            workers=1,  # 单进程模式，因为使用了全局状态
            reload=False,
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 用户中断，正在关闭服务器...")
        logger.info("用户中断服务器")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 