"""
配置文件 - API keys 同路徑
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    SUNO_API_KEY: str = os.getenv("SUNO_API_KEY", "")
    IMAGE_GEN_API_KEY: str = os.getenv("IMAGE_GEN_API_KEY", "")  # Stability AI / DALL-E
    VIDEO_GEN_API_KEY: str = os.getenv("VIDEO_GEN_API_KEY", "")  # Runway / Pika
    
    # API Endpoints
    QWEN_API_URL: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    OPENAI_API_URL: str = "https://api.openai.com/v1/chat/completions"
    ELEVENLABS_API_URL: str = "https://api.elevenlabs.io/v1/text-to-speech"
    SUNO_API_URL: str = "https://api.suno.ai/v1/generate"
    
    # 路徑
    BASE_DIR: Path = Path(__file__).parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    TEMP_DIR: Path = BASE_DIR / "temp"
    
    # 模型設定
    WHISPER_MODEL: str = "large-v3"  # or "base", "small", "medium"
    GPT_MODEL: str = "gpt-4o"
    
    # 其他參數
    MAX_RETRIES: int = 3
    TIMEOUT: int = 300  # 5 分鐘
    
    # 語言 (用作 syllable counting)
    LANGUAGE: str = "zh-TW"  # 或 "en", "zh-CN"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# 建立必要資料夾
for folder in [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.TEMP_DIR]:
    folder.mkdir(parents=True, exist_ok=True)