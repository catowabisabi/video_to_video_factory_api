
# ==================== Image Gen ====================
import httpx

class ImageGenService:
    async def generate(self, prompt: str, job_id: str, title: str, clip_id: str) -> str:
        """調用文生圖 API（Stability AI / DALL-E / 自己 SD）"""
        output_dir = Path(f"outputs/{job_id}_{title}/img")
        output_dir.mkdir(parents=True, exist_ok=True)
        img_path = output_dir / f"clip_{clip_id}.jpg"
        
        # 示範：假設用 Stability AI
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Authorization": f"Bearer {settings.IMAGE_GEN_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "text_prompts": [{"text": prompt}],
                    "cfg_scale": 7,
                    "height": 1024,
                    "width": 576,  # 9:16
                    "samples": 1
                }
            )
            
            data = response.json()
            img_b64 = data["artifacts"][0]["base64"]
            
            import base64
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(img_b64))
        
        return str(img_path)