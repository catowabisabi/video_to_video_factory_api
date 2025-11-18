"""
Pydantic 數據模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class TranscriptSentence(BaseModel):
    """單句 transcript"""
    index: int
    text: str
    start: float  # 秒
    end: float
    duration: float = 0.0
    syllables: int = 0
    syllables_per_sec: float = 0.0


class VideoMetadata(BaseModel):
    """影片 metadata"""
    fps: float
    total_frames: int
    width: int
    height: int
    duration: float  # 秒


class SyllableData(BaseModel):
    """發音數據"""
    total_syllables: int
    total_duration: float
    syllables_per_sec: float
    sentences: List[TranscriptSentence]


class Frame(BaseModel):
    """單張 frame"""
    sentence_index: int
    frame_time: float  # 在影片中的時間點
    img_path: str
    qwen_title: Optional[str] = None
    qwen_caption: Optional[str] = None
    qwen_prompt: Optional[str] = None


class Clip(BaseModel):
    """單個 3 秒 clip"""
    clip_id: str  # e.g., "00a", "00b"
    prompt: str
    img_path: Optional[str] = None
    video_path: Optional[str] = None
    status: str = "pending"  # pending, ok, bad


class SentenceWithClips(BaseModel):
    """單句 + 對應 clips"""
    index: int
    text: str
    duration: float
    num_clips: int
    clips: List[Clip]


class UnifiedData(BaseModel):
    """統一風格後的數據"""
    summary: str
    global_style: Dict[str, Any]
    characters: List[Dict[str, Any]]
    locations: List[Dict[str, Any]]
    per_sentence: List[SentenceWithClips]


class DialogueAudio(BaseModel):
    """TTS 結果"""
    audio_path: str
    duration: float
    sentence_timings: List[Dict[str, float]]  # [{"start": 0.0, "end": 3.2}, ...]


class FinalVideo(BaseModel):
    """最終輸出"""
    video_path: str
    srt_path: str
    duration: float
    clips_count: int