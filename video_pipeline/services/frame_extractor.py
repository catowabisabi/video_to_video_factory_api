"""
其他 Services 骨架（你可根據實際 API 完善）
"""

# ==================== Frame Extractor ====================
import subprocess
from pathlib import Path

# flexible settings import (not required but kept for consistency)
try:
    from video_pipeline.config import settings
except Exception:
    try:
        from config import settings
    except Exception:
        settings = type("_S", (), {})()

class FrameExtractor:
    async def extract_frames_per_sentence(
        self, video_path: str, sentences, fps: float, job_id: str, title: str
    ):
        """每句每 3 秒抽一張 frame"""
        output_dir = Path(f"outputs/{job_id}_{title}/img_raw")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        frames = []
        for sentence in sentences:
            start, end = sentence.start, sentence.end
            t = start
            frame_idx = 0
            
            while t < end:
                frame_path = output_dir / f"sentence_{sentence.index:02d}_frame_{frame_idx:02d}.jpg"
                
                # ffmpeg 抽 frame
                subprocess.run([
                    "ffmpeg", "-ss", str(t), "-i", video_path,
                    "-frames:v", "1", "-q:v", "2", "-y", str(frame_path)
                ], check=True)
                
                frames.append({
                    "sentence_index": sentence.index,
                    "frame_time": t,
                    "img_path": str(frame_path)
                })
                
                t += 3.0
                frame_idx += 1
        
        return frames