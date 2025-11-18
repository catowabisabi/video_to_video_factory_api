import subprocess
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    # prefer package-qualified import (works when running as package)
    from video_pipeline.config import settings
except Exception:
    try:
        from config import settings
    except Exception:
        settings = None


class VideoAssembler:
    async def assemble(self, clips: Iterable[Any], dialogue: Dict[str, Any], music: str, srt_data: List[Any], job_id: str, title: str) -> Dict[str, Any]:
        """Assemble final video.

        - Ensures `outputs/{job_id}_{title}` exists.
        - Guards ffmpeg calls and returns helpful error info on failure.
        """
        base = Path(getattr(settings, "BASE_DIR", Path.cwd())) if settings else Path.cwd()
        output_dir = base / f"outputs/{job_id}_{title}"
        output_dir.mkdir(parents=True, exist_ok=True)

        final_video = output_dir / "final_video.mp4"
        srt_path = output_dir / "subtitles.srt"

        # helper to normalize clip item -> video path string
        def _clip_path(c: Any) -> Optional[str]:
            if isinstance(c, dict):
                return c.get("video_path")
            # support objects with attribute
            return getattr(c, "video_path", None)

        # 1. Use ffmpeg concat for clips
        concat_list = output_dir / "concat.txt"
        with open(concat_list, "w", encoding="utf-8") as f:
            written = 0
            for clip in clips:
                p = _clip_path(clip)
                if not p:
                    continue
                f.write(f"file '{p}'\n")
                written += 1

        if written == 0:
            return {"error": "no valid clips to assemble", "clips_count": 0}

        temp_video = output_dir / "temp_video.mp4"

        ffmpeg_cmd = shutil.which("ffmpeg") or "ffmpeg"

        try:
            subprocess.run([
                ffmpeg_cmd, "-f", "concat", "-safe", "0",
                "-i", str(concat_list), "-c", "copy", "-y", str(temp_video)
            ], check=True)
        except FileNotFoundError:
            return {"error": "ffmpeg not found on PATH"}
        except subprocess.CalledProcessError as e:
            return {"error": "ffmpeg concat failed", "details": str(e)}

        # 2. Mix dialogue + music audio
        mixed_audio = output_dir / "mixed_audio.mp3"
        dialogue_audio = dialogue.get("audio_path") if isinstance(dialogue, dict) else getattr(dialogue, "audio_path", None)
        if not dialogue_audio:
            return {"error": "dialogue audio not provided"}

        try:
            subprocess.run([
                ffmpeg_cmd,
                "-i", str(dialogue_audio),
                "-i", str(music),
                "-filter_complex", "[0:a]volume=1.0[a1];[1:a]volume=0.3[a2];[a1][a2]amix=inputs=2[aout]",
                "-map", "[aout]", "-y", str(mixed_audio)
            ], check=True)
        except FileNotFoundError:
            return {"error": "ffmpeg not found on PATH"}
        except subprocess.CalledProcessError as e:
            return {"error": "ffmpeg mix failed", "details": str(e)}

        # 3. Merge video + audio
        try:
            subprocess.run([
                ffmpeg_cmd,
                "-i", str(temp_video),
                "-i", str(mixed_audio),
                "-c:v", "copy", "-c:a", "aac", "-shortest",
                "-y", str(final_video)
            ], check=True)
        except FileNotFoundError:
            return {"error": "ffmpeg not found on PATH"}
        except subprocess.CalledProcessError as e:
            return {"error": "ffmpeg merge failed", "details": str(e)}

        # 4. Generate SRT
        try:
            self._generate_srt(srt_data, srt_path)
        except Exception as e:
            return {"error": "srt generation failed", "details": str(e)}

        duration = dialogue.get("duration") if isinstance(dialogue, dict) else getattr(dialogue, "duration", None)

        return {
            "video_path": str(final_video),
            "srt_path": str(srt_path),
            "duration": duration,
            "clips_count": written
        }

    def _generate_srt(self, script: List[Any], output_path: Path) -> None:
        """Write .srt subtitle file. Accepts list of objects or dicts with start/end/text."""
        with open(output_path, "w", encoding="utf-8") as f:
            for i, sentence in enumerate(script):
                start = sentence.start if hasattr(sentence, "start") else sentence.get("start")
                end = sentence.end if hasattr(sentence, "end") else sentence.get("end")
                text = sentence.text if hasattr(sentence, "text") else sentence.get("text")
                start_time = self._format_srt_time(float(start or 0))
                end_time = self._format_srt_time(float(end or 0))
                f.write(f"{i+1}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text or ''}\n\n")

    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to 00:00:00,000"""
        try:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds % 1) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
        except Exception:
            return "00:00:00,000"