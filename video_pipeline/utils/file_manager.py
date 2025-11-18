"""
工具模塊
"""
from pathlib import Path
import shutil
import asyncio
from functools import wraps


# ==================== File Manager ====================
class FileManager:
    
    @staticmethod
    def move_to_bad(img_path: str, job_id: str, title: str) -> str:
        """把失敗的圖移到 bad_img"""
        bad_dir = Path(f"outputs/{job_id}_{title}/bad_img")
        bad_dir.mkdir(parents=True, exist_ok=True)
        
        src = Path(img_path)
        dst = bad_dir / src.name
        shutil.move(str(src), str(dst))
        
        return str(dst)
    
    @staticmethod
    def ensure_dir(path: str):
        """確保目錄存在"""
        Path(path).mkdir(parents=True, exist_ok=True)


