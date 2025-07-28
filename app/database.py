"""数据库连接管理"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

from .config import AiPlatformConfig
from .models.base import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: AiPlatformConfig):
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库连接"""
        database_url = self.config.database_url
        
        # SQLite特殊配置
        if database_url.startswith("sqlite"):
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=self.config.database_echo
            )
        else:
            self.engine = create_engine(
                database_url,
                echo=self.config.database_echo
            )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"数据库连接已初始化: {database_url}")
    
    def create_tables(self):
        """创建数据库表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
    
    def drop_tables(self):
        """删除所有表"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("数据库表删除成功")
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话（上下文管理器）"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """获取同步数据库会话"""
        return self.SessionLocal()

# 全局数据库管理器实例
_database_manager = None

def init_database(config: AiPlatformConfig) -> DatabaseManager:
    """初始化数据库管理器"""
    global _database_manager
    _database_manager = DatabaseManager(config)
    return _database_manager

def get_database_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    if _database_manager is None:
        raise RuntimeError("数据库管理器未初始化，请先调用 init_database()")
    return _database_manager

def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话的依赖注入函数"""
    db_manager = get_database_manager()
    with db_manager.get_session() as session:
        yield session 