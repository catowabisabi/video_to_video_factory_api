"""
AI Video Production Pipeline API

檔案說明（File description）:
    - 本檔為整個 AI 影片製作流程的 API 入口。
    - 流程範例：video -> transcription -> rewrite -> image generation -> video generation -> TTS -> music -> assembly
    - 此檔提供 HTTP endpoint 以啟動與查詢 pipeline 作業（在簡易範例中 job 狀態儲存在記憶體）

File description (English):
    - This module exposes FastAPI endpoints to start and monitor an AI video production pipeline.
    - Typical pipeline: video -> transcript -> script rewrite -> image generation -> video generation -> TTS -> music -> final assembly
    - Jobs are stored in an in-memory dict for simplicity; production should use Redis/DB for persistence.

注意 / Notes:
    - Imports like `from services...` assume this module runs with the project root on `PYTHONPATH`.
      If you run via `python -m video_pipeline.main` or with a proper package entry, imports should resolve.
    - 目前以 in-memory `jobs` 儲存狀態；多人或多程序部署時請改用共享儲存（Redis/DB）。
"""

try:
    from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
    from fastapi.responses import JSONResponse
    HAVE_FASTAPI = True
except Exception:
    # 如果 environment 沒有安裝 fastapi，提供最小的 stub 以利模組匯入與非 API 使用情境。
    HAVE_FASTAPI = False

    class FastAPI:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass
        def post(self, path=None, **kwargs):
            def decorator(func):
                return func
            return decorator
        def get(self, path=None, **kwargs):
            def decorator(func):
                return func
            return decorator
        def include_router(self, *args, **kwargs):
            return None

    def File(*args, **kwargs):  # type: ignore
        return None

    class UploadFile:  # type: ignore
        filename: str = ""

        async def read(self):
            return b""

    class BackgroundTasks:  # type: ignore
        def add_task(self, *args, **kwargs):
            return None

    class HTTPException(Exception):
        def __init__(self, status_code: int = 500, detail: str = ""):
            super().__init__(detail)
    
    class JSONResponse:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path

# 假設其他模塊已寫好（下面會提供）
# Use package-qualified imports when possible; fall back to local imports when running as script.
try:
    from video_pipeline.config import settings
except Exception:
    from config import settings

try:
    from video_pipeline.models import *
except Exception:
    from models import *

def _import(name: str, attr: str):
    try:
        module = __import__(f"video_pipeline.{name}", fromlist=[attr])
        return getattr(module, attr)
    except Exception:
        try:
            module = __import__(f"{name}", fromlist=[attr])
            return getattr(module, attr)
        except Exception:
            # 如果找不到該 class 或 module，建立一個最小 stub 以保持匯入成功。
            # Stub 的方法盡量覆蓋 main.py 中會被呼叫到的介面。
            class _Stub:
                def __init__(self, *a, **k):
                    pass

                async def extract_metadata(self, video_path: str):
                    return {"duration": 1.0, "fps": 30.0}

                async def extract_audio(self, video_path: str):
                    return str(Path(video_path).with_suffix('.wav'))

                async def transcribe(self, audio_path: str):
                    return []

                def count_all(self, transcript, duration):
                    return {"syllables_per_sec": 1.0}

                def count_script(self, script):
                    return 1

                async def generate(self, *a, **k):
                    return str(Path('outputs') / 'stub.jpg')

                async def generate_clips(self, *a, **k):
                    return []

                async def generate_dialogue(self, *a, **k):
                    return {"audio_path": "", "duration": 0}

                async def analyze_frames(self, frames_data):
                    return frames_data

                async def verify_image_quality(self, *a, **k):
                    return {"status": "ok"}

                async def check_safety(self, *a, **k):
                    return {"raw": "safe"}

                async def unify_style_and_prompts(self, *a, **k):
                    return {"summary": "", "per_sentence": []}

                async def assemble(self, *a, **k):
                    return {"video_path": "", "duration": 0}

            return _Stub

VideoProcessor = _import('services.video_processor', 'VideoProcessor')
TranscriptionService = _import('services.transcription', 'TranscriptionService')
SyllableCounter = _import('services.syllable_counter', 'SyllableCounter')
FrameExtractor = _import('services.frame_extractor', 'FrameExtractor')
QwenService = _import('services.qwen_service', 'QwenService')
ChatGPTService = _import('services.chatgpt_service', 'ChatGPTService')
ImageGenService = _import('services.image_gen', 'ImageGenService')
VideoGenService = _import('services.video_gen', 'VideoGenService')
TTSService = _import('services.tts_service', 'TTSService')
MusicService = _import('services.music_service', 'MusicService')
VideoAssembler = _import('services.video_assembly', 'VideoAssembler')
FileManager = _import('utils.file_manager', 'FileManager')
retry_with_limit = _import('utils.retry_handler', 'retry_with_limit')

app = FastAPI(title="AI Video Pipeline", version="1.0.0")

# 全局 job 狀態（生產環境用 Redis/DB）
jobs: Dict[str, Dict[str, Any]] = {}


@app.post("/api/pipeline/start")
async def start_pipeline(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = None
):
    """
    啟動完整 pipeline
    """
    job_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 儲存上傳檔案
    upload_path = Path(settings.UPLOAD_DIR) / job_id
    upload_path.mkdir(parents=True, exist_ok=True)
    video_path = upload_path / file.filename
    
    with open(video_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 注意：此處將整個上傳檔讀入記憶體，對大檔案可能會造成記憶體壓力。
    # Note: reading the whole uploaded file into memory may cause high memory usage for large files.
    
    # 初始化 job 狀態
    jobs[job_id] = {
        "status": "started",
        "video_path": str(video_path),
        "title": title or f"video_{job_id}",
        "current_step": "uploading",
        "progress": 0,
        "errors": [],
        "warnings": []
    }
    
    # 背景執行
    # BackgroundTasks 可以接受 coroutine function；FastAPI/Starlette 會將其排程執行。
    # BackgroundTasks accepts coroutine functions; Starlette will schedule them on the event loop.
    background_tasks.add_task(run_pipeline, job_id, str(video_path), title)
    
    return {"job_id": job_id, "message": "Pipeline started"}


@app.get("/api/pipeline/status/{job_id}")
async def get_status(job_id: str):
    """查詢 job 狀態"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


async def run_pipeline(job_id: str, video_path: str, title: str):
    """
    主 pipeline 流程
    """
    # NOTE: Each service used below (VideoProcessor, TranscriptionService, etc.)
    # should implement appropriate error handling and timeouts.
    # 如果希望更細緻的錯誤回復/重試策略，可在各服務或此處加入 retry 機制。
    try:
        # 1. 影片預處理
        jobs[job_id]["current_step"] = "video_processing"
        jobs[job_id]["progress"] = 5
        
        processor = VideoProcessor()
        video_meta = await processor.extract_metadata(video_path)
        audio_path = await processor.extract_audio(video_path)
        
        jobs[job_id]["video_meta"] = video_meta
        jobs[job_id]["audio_path"] = audio_path
        
        # 2. 語音轉文字
        jobs[job_id]["current_step"] = "transcription"
        jobs[job_id]["progress"] = 15
        
        transcriber = TranscriptionService()
        transcript = await transcriber.transcribe(audio_path)
        
        jobs[job_id]["transcript"] = transcript
        
        # 3. 計算發音數
        jobs[job_id]["current_step"] = "syllable_counting"
        jobs[job_id]["progress"] = 20
        
        counter = SyllableCounter()
        syllable_data = counter.count_all(transcript, video_meta["duration"])
        
        jobs[job_id]["syllable_data"] = syllable_data
        
        # 4. ChatGPT 改寫 script
        jobs[job_id]["current_step"] = "script_rewriting"
        jobs[job_id]["progress"] = 25
        
        chatgpt = ChatGPTService()
        new_script = await rewrite_script_with_retry(
            chatgpt, transcript, syllable_data, video_meta["duration"], job_id
        )
        
        jobs[job_id]["new_script"] = new_script
        
        # 5. 抽 frame
        jobs[job_id]["current_step"] = "frame_extraction"
        jobs[job_id]["progress"] = 35
        
        extractor = FrameExtractor()
        frames_data = await extractor.extract_frames_per_sentence(
            video_path, transcript, video_meta["fps"], job_id, title
        )
        
        # 6. Qwen-VL3 反推
        jobs[job_id]["current_step"] = "qwen_analysis"
        jobs[job_id]["progress"] = 45
        
        qwen = QwenService()
        analyzed_frames = await qwen.analyze_frames(frames_data)
        
        # 7. 統一風格 + 生成 prompts
        jobs[job_id]["current_step"] = "style_unification"
        jobs[job_id]["progress"] = 55
        
        unified_data = await chatgpt.unify_style_and_prompts(
            analyzed_frames, new_script, syllable_data
        )
        
        jobs[job_id]["unified_data"] = unified_data
        
        # 8. 文生圖
        jobs[job_id]["current_step"] = "image_generation"
        jobs[job_id]["progress"] = 65
        
        image_gen = ImageGenService()
        images_result = await generate_images_with_safety(
            image_gen, qwen, chatgpt, unified_data, job_id, title
        )
        
        # 9. 圖生影片
        jobs[job_id]["current_step"] = "video_generation"
        jobs[job_id]["progress"] = 75
        
        video_gen = VideoGenService()
        clips = await video_gen.generate_clips(images_result, job_id, title)
        
        # 10. TTS
        jobs[job_id]["current_step"] = "tts_generation"
        jobs[job_id]["progress"] = 85
        
        tts = TTSService()
        dialogue_audio = await tts.generate_dialogue(new_script, job_id, title)
        
        # 11. 音樂
        jobs[job_id]["current_step"] = "music_generation"
        jobs[job_id]["progress"] = 90
        
        music_service = MusicService()
        music_path = await music_service.generate_and_cut_music(
            unified_data["summary"], dialogue_audio["duration"], job_id, title
        )
        
        # 12. 最終組裝
        jobs[job_id]["current_step"] = "final_assembly"
        jobs[job_id]["progress"] = 95
        
        assembler = VideoAssembler()
        final_video = await assembler.assemble(
            clips=clips,
            dialogue=dialogue_audio,
            music=music_path,
            srt_data=new_script,
            job_id=job_id,
            title=title
        )
        
        # 完成
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["final_video"] = final_video
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["errors"].append(str(e))
        print(f"Pipeline failed: {e}")


async def rewrite_script_with_retry(
    chatgpt: Any,
    transcript: List[dict],
    syllable_data: dict,
    duration: float,
    job_id: str,
    max_attempts: int = 10
) -> List[dict]:
    """
    改寫 script 並檢查發音數，最多重試 10 次
    """
    # 健全性檢查：避免除以零（duration 或 target_sps 為 0）
    counter = SyllableCounter()
    target_sps = syllable_data.get("syllables_per_sec", 0)
    duration_safe = duration if (duration and duration > 0) else 1e-6

    for attempt in range(max_attempts):
        new_script = await chatgpt.rewrite_script(transcript, syllable_data)

        # 計算新 script 發音數
        new_syllables = counter.count_script(new_script)
        new_sps = new_syllables / duration_safe

        # 如果 target_sps 為 0，無法以相對比例比較，改採絕對判斷（若雙方皆為 0 則視為通過）
        if target_sps == 0:
            if new_syllables == 0:
                return new_script
            else:
                diff_pct = float("inf")
        else:
            diff_pct = abs(new_sps - target_sps) / target_sps

        if diff_pct <= 0.1:  # 差異 <= 10%
            return new_script

        # 差太多，要求調整
        feedback = f"發音數差 {diff_pct*100:.1f}%，目標 {target_sps:.2f}/s，你給 {new_sps:.2f}/s"
        jobs[job_id]["warnings"].append(f"Attempt {attempt+1}: {feedback}")
    
    # 超過 10 次
    jobs[job_id]["warnings"].append("⚠️ 發音數調整失敗，需人工處理")
    return new_script  # 返回最後一次結果


async def generate_images_with_safety(
    image_gen: Any,
    qwen: Any,
    chatgpt: Any,
    unified_data: dict,
    job_id: str,
    title: str,
    max_retries: int = 3
) -> dict:
    """
    生成圖片 + 安全檢查，最多重試 3 次
    """
    results = {"ok": [], "bad": []}
    
    for sentence in unified_data["per_sentence"]:
        for clip in sentence["clips"]:
            clip_id = clip["clip_id"]
            prompt = clip["prompt"]
            
            attempt = 0
            success = False
            
            while attempt < max_retries and not success:
                # 生圖
                img_path = await image_gen.generate(prompt, job_id, title, clip_id)
                
                # Qwen 安全檢查
                safety_result = await qwen.check_safety(img_path)
                
                # ChatGPT 二次判斷
                gpt_check = await chatgpt.verify_image_quality(
                    safety_result, prompt
                )
                
                if gpt_check["status"] == "ok":
                    results["ok"].append({
                        "clip_id": clip_id,
                        "img_path": img_path,
                        "prompt": prompt
                    })
                    success = True
                else:
                    attempt += 1
                    if attempt >= max_retries:
                        # 放入 bad
                        bad_path = FileManager.move_to_bad(img_path, job_id, title)
                        results["bad"].append({
                            "clip_id": clip_id,
                            "img_path": bad_path,
                            "reason": gpt_check["reason"]
                        })
                        jobs[job_id]["warnings"].append(
                            f"⚠️ {clip_id} 生圖失敗 3 次，需人工處理"
                        )
    
    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)