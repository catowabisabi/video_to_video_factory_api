"""
ASR 服務 - Whisper
"""
from typing import List
from models import TranscriptSentence

# flexible settings import
try:
    from video_pipeline.config import settings
except Exception:
    try:
        from config import settings
    except Exception:
        settings = type("_S", (), {})()

# whisper fallback
try:
    import whisper
except Exception:
    class _WhisperModelStub:
        def transcribe(self, audio_path, **kwargs):
            return {"segments": []}

    class _Whisper:
        @staticmethod
        def load_model(name):
            return _WhisperModelStub()

    whisper = _Whisper()


class TranscriptionService:
    
    def __init__(self):
        self.model = whisper.load_model(getattr(settings, 'WHISPER_MODEL', 'base'))
    
    async def transcribe(self, audio_path: str) -> List[TranscriptSentence]:
        """
        用 Whisper 轉文字，帶時間戳
        """
        result = self.model.transcribe(
            audio_path,
            word_timestamps=True,
            verbose=False
        )
        
        sentences = []
        for i, segment in enumerate(result["segments"]):
            sentences.append(
                TranscriptSentence(
                    index=i,
                    text=segment["text"].strip(),
                    start=segment["start"],
                    end=segment["end"],
                    duration=segment["end"] - segment["start"]
                )
            )
        
        return sentences