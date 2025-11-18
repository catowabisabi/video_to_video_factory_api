from pathlib import Path
import subprocess

# flexible settings import
try:
    from video_pipeline.config import settings
except Exception:
    try:
        from config import settings
    except Exception:
        settings = type("_S", (), {})()


class VideoGenService:
    async def generate_clips(self, images_result: dict, job_id: str, title: str):
        """圖生 3 秒影片（Runway / Pika / 自己 ComfyUI）"""
        output_dir = Path(f"outputs/{job_id}_{title}/video")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        clips = []
        for img_data in images_result["ok"]:
            clip_id = img_data["clip_id"]
            img_path = img_data["img_path"]
            video_path = output_dir / f"clip_{clip_id}.mp4"
            
            # 示範：假設用 Runway API
            # 實際你可用 ComfyUI workflow
            
            # 暫時用 ffmpeg 做靜態 3 秒片（佔位）
            subprocess.run([
                "ffmpeg", "-loop", "1", "-i", img_path,
                "-c:v", "libx264", "-t", "3", "-pix_fmt", "yuv420p",
                "-vf", "scale=576:1024", "-y", str(video_path)
            ], check=True)
            
            clips.append({
                "clip_id": clip_id,
                "video_path": str(video_path)
            })
        
        return clips