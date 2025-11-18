class MusicService:
    async def generate_and_cut_music(self, summary: str, target_duration: float, job_id: str, title: str):
        """生成音樂並 cut 到指定長度"""
        output_dir = Path(f"outputs/{job_id}_{title}/audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        music_path = output_dir / "music.mp3"
        
        # 假設用 Suno API
        # 暫時返回空檔案
        
        # 用 pydub cut
        from pydub import AudioSegment
        # audio = AudioSegment.from_mp3(...)
        # cut_audio = audio[:int(target_duration * 1000)]
        # cut_audio.export(music_path, format="mp3")
        
        return str(music_path)
