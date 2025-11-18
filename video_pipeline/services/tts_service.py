# ==================== TTS ====================
class TTSService:
    async def generate_dialogue(self, script, job_id: str, title: str):
        """用 ElevenLabs 生成對白"""
        output_dir = Path(f"outputs/{job_id}_{title}/audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / "dialogue.wav"
        
        # 合併所有句子
        full_text = " ".join([s.text for s in script])
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ELEVENLABS_API_URL}/YOUR_VOICE_ID",
                headers={
                    "xi-api-key": settings.ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                },
                json={"text": full_text, "model_id": "eleven_multilingual_v2"}
            )
            
            with open(audio_path, "wb") as f:
                f.write(response.content)
        
        # 用 ffprobe 取時長
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True, text=True
        )
        duration = float(result.stdout.strip())
        
        return {"audio_path": str(audio_path), "duration": duration, "sentence_timings": []}
