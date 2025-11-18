# ==================== TTS ====================
import subprocess
from pathlib import Path
from typing import List, Any, Dict

import httpx

try:
    from video_pipeline.config import settings
except Exception:
    from config import settings


class TTSService:
    async def generate_dialogue(self, script: List[Any], job_id: str, title: str) -> Dict:
        """用 ElevenLabs 生成對白 / Generate dialogue audio via ElevenLabs

        注意：此方法假設 `settings.ELEVENLABS_API_KEY` 與 `settings.ELEVENLABS_API_URL` 已設定。
        若環境沒有這些參數，會嘗試仍然完成檔案路徑建立並回傳 stub 結果。
        """
        output_dir = Path(f"outputs/{job_id}_{title}/audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / "dialogue.wav"

        # 合併所有句子文字（若 script 中元素沒有 text 屬性，會忽略）
        texts = []
        for s in script:
            try:
                texts.append(s.text)
            except Exception:
                try:
                    texts.append(str(s))
                except Exception:
                    continue
        full_text = " ".join(texts).strip()

        if full_text and getattr(settings, "ELEVENLABS_API_KEY", None) and getattr(settings, "ELEVENLABS_API_URL", None):
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{settings.ELEVENLABS_API_URL}/YOUR_VOICE_ID",
                    headers={
                        "xi-api-key": settings.ELEVENLABS_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={"text": full_text, "model_id": "eleven_multilingual_v2"}
                )
                try:
                    response.raise_for_status()
                except Exception:
                    # 若 API 呼叫失敗，建立空的檔案並回傳 error duration 0
                    audio_path.write_bytes(b"")
                else:
                    audio_path.write_bytes(response.content)
        else:
            # 沒有可用的 API key 或文字，建立空檔作為 stub
            audio_path.write_bytes(b"")

        # 用 ffprobe 取時長（若 ffprobe 不存在或解析失敗，回傳 0）
        duration = 0.0
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
                capture_output=True, text=True, check=True
            )
            out = result.stdout.strip()
            if out:
                duration = float(out)
        except Exception:
            duration = 0.0

        return {"audio_path": str(audio_path), "duration": duration, "sentence_timings": []}
