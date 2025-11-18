"""
Qwen-VL3 API 服務（阿里雲通義千問）
"""
import httpx
import base64
from typing import List, Dict
from pathlib import Path
from config import settings


class QwenService:
    
    def __init__(self):
        self.api_key = settings.QWEN_API_KEY
        self.api_url = settings.QWEN_API_URL
    
    async def analyze_frames(self, frames_data: List[Dict]) -> List[Dict]:
        """
        批次分析 frames
        """
        results = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for frame in frames_data:
                img_path = frame["img_path"]
                
                # 讀圖並 base64
                with open(img_path, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                
                # 調用 Qwen API
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "qwen-vl-max",
                        "input": {
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {"image": f"data:image/jpeg;base64,{img_b64}"},
                                        {"text": "請描述這張圖，並生成適合重新生成此圖的 prompt（包括：場景、角色、風格、燈光）"}
                                    ]
                                }
                            ]
                        }
                    }
                )
                
                data = response.json()
                caption = data["output"]["choices"][0]["message"]["content"]
                
                results.append({
                    "img_path": img_path,
                    "caption": caption,
                    "prompt": self._extract_prompt(caption)
                })
        
        return results
    
    def _extract_prompt(self, caption: str) -> str:
        """從 caption 提取 prompt（簡化版）"""
        # 實際可用 ChatGPT 再處理
        return caption
    
    async def check_safety(self, img_path: str) -> Dict:
        """
        檢查圖片安全性 + 內容
        """
        with open(img_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen-vl-max",
                    "input": {
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"image": f"data:image/jpeg;base64,{img_b64}"},
                                    {"text": "檢查此圖：1) 是否有 NSFW 或不當內容？2) 描述圖片內容。返回 JSON: {\"safe\": true/false, \"description\": \"...\", \"issues\": []}"}
                                ]
                            }
                        ]
                    }
                }
            )
            
            data = response.json()
            content = data["output"]["choices"][0]["message"]["content"]
            
            # 簡化：直接返回
            return {"raw": content}