from pathlib import Path

# flexible settings import
try:
    from video_pipeline.config import settings
except Exception:
    try:
        from config import settings
    except Exception:
        settings = type("_S", (), {})()

class MusicService:
    async def generate_and_cut_music(self, summary: str, target_duration: float, job_id: str, title: str):
        """生成音樂並 cut 到指定長度"""
        output_dir = Path(f"outputs/{job_id}_{title}/audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        music_path = output_dir / "music.mp3"
        
        # 假設用 Suno API
        # 暫時返回空檔案
        
        # 用 pydub cut（若未安裝 pydub，則建立空檔作為 stub）
        try:
            from pydub import AudioSegment
            # audio = AudioSegment.from_mp3(...)
            # cut_audio = audio[:int(target_duration * 1000)]
            # cut_audio.export(music_path, format="mp3")
        except Exception:
            music_path.write_bytes(b"")
        
        return str(music_path)
