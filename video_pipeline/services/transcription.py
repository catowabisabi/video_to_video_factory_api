"""
ASR 服務 - Whisper
"""
import whisper
from typing import List
from models import TranscriptSentence


class TranscriptionService:
    
    def __init__(self):
        from config import settings
        self.model = whisper.load_model(settings.WHISPER_MODEL)
    
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