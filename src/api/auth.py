"""
API认证模块

安全说明：
- API 密钥必须通过 api_keys 配置项显式配置
- 不再回退到 webhook_secret，避免职责混淆
- 生产环境必须配置 api_keys，否则所有 API 请求将被拒绝
"""

import logging
from typing import Optional
from fastapi import HTTPException, Header
from src.config import settings


logger = logging.getLogger(__name__)


def get_valid_api_keys() -> list:
    """
    获取有效的 API 密钥列表。

    安全策略：
    - 仅从 api_keys 配置获取，不再回退到 webhook_secret
    - 如果未配置，返回空列表（所有请求将被拒绝）

    Returns:
        有效的 API 密钥列表
    """
    api_keys = getattr(settings, 'api_keys', [])

    # 确保返回列表类型
    if not api_keys:
        return []

    # 如果是字符串（单个密钥），转换为列表
    if isinstance(api_keys, str):
        return [api_keys] if api_keys else []

    return list(api_keys)


async def api_key_auth(
    x_api_key: Optional[str] = Header(None, description="API密钥")
) -> str:
    """
    API密钥认证

    Args:
        x_api_key: 请求头中的API密钥

    Returns:
        认证成功返回API密钥

    Raises:
        HTTPException: 认证失败
    """
    if not x_api_key:
        logger.warning("API request without key")
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # 从配置中获取有效的API密钥（不再回退到 webhook_secret）
    valid_api_keys = get_valid_api_keys()

    if not valid_api_keys:
        # 未配置 API 密钥时，拒绝所有请求
        logger.error(
            "API authentication failed: api_keys not configured. "
            "Please set API_KEYS environment variable for production."
        )
        raise HTTPException(
            status_code=503,
            detail="API service not configured. Contact administrator."
        )

    if x_api_key not in valid_api_keys:
        logger.warning(f"Invalid API key attempt: {x_api_key[:8]}...")
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    return x_api_key


async def optional_api_key_auth(
    x_api_key: Optional[str] = Header(None, description="API密钥")
) -> Optional[str]:
    """
    可选的API密钥认证（某些接口可以不需要认证）
    
    Args:
        x_api_key: 请求头中的API密钥
        
    Returns:
        API密钥或None
    """
    if x_api_key:
        try:
            return await api_key_auth(x_api_key)
        except HTTPException:
            return None
    return None
