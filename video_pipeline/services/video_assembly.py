class VideoAssembler:
    async def assemble(self, clips, dialogue, music, srt_data, job_id: str, title: str):
        """最終組裝"""
        output_dir = Path(f"outputs/{job_id}_{title}")
        final_video = output_dir / "final_video.mp4"
        srt_path = output_dir / "subtitles.srt"
        
        # 1. 用 ffmpeg concat clips
        concat_list = output_dir / "concat.txt"
        with open(concat_list, "w") as f:
            for clip in clips:
                f.write(f"file '{clip['video_path']}'\n")
        
        temp_video = output_dir / "temp_video.mp4"
        subprocess.run([
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", str(concat_list), "-c", "copy", "-y", str(temp_video)
        ], check=True)
        
        # 2. 加入 audio（dialogue + music）
        # 先 mix audio
        mixed_audio = output_dir / "mixed_audio.mp3"
        subprocess.run([
            "ffmpeg",
            "-i", dialogue["audio_path"],
            "-i", music,
            "-filter_complex", "[0:a]volume=1.0[a1];[1:a]volume=0.3[a2];[a1][a2]amix=inputs=2[aout]",
            "-map", "[aout]", "-y", str(mixed_audio)
        ], check=True)
        
        # 3. 合併 video + audio
        subprocess.run([
            "ffmpeg",
            "-i", str(temp_video),
            "-i", str(mixed_audio),
            "-c:v", "copy", "-c:a", "aac", "-shortest",
            "-y", str(final_video)
        ], check=True)
        
        # 4. 生成 SRT
        self._generate_srt(srt_data, srt_path)
        
        return {
            "video_path": str(final_video),
            "srt_path": str(srt_path),
            "duration": dialogue["duration"],
            "clips_count": len(clips)
        }
    
    def _generate_srt(self, script, output_path):
        """生成 .srt 字幕"""
        with open(output_path, "w", encoding="utf-8") as f:
            for i, sentence in enumerate(script):
                start_time = self._format_srt_time(sentence.start)
                end_time = self._format_srt_time(sentence.end)
                f.write(f"{i+1}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{sentence.text}\n\n")
    
    def _format_srt_time(self, seconds: float) -> str:
        """00:00:00,000 格式"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"