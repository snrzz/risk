"""
数据库连接和会话管理
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings, DATABASE_URL, DATABASE_TYPE

# 创建同步引擎 (用于 migrations 和某些工具)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 创建异步引擎 (用于 FastAPI)
if DATABASE_TYPE == "sqlite":
    async_engine = create_async_engine(
        DATABASE_URL.replace("sqlite", "sqlite+aiosqlite"),
        pool_pre_ping=True,
        pool_recycle=3600,
    )
else:
    async_engine = create_async_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=DEBUG if hasattr(settings.app, 'debug') else False,
    )

# 异步会话工厂
async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 同步会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# 声明基类
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """依赖注入: 获取数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """上下文管理器: 获取数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """删除数据库表"""
    Base.metadata.drop_all(bind=engine)
