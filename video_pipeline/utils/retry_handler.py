# ==================== Retry Handler ====================
"""
工具模塊
"""
from pathlib import Path
import shutil
import asyncio
from functools import wraps

def retry_with_limit(max_attempts: int = 3, delay: float = 1.0):
    """
    重試裝飾器
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
                    else:
                        raise last_exception
            
            raise last_exception
        
        return wrapper
    return decorator