"""
ChatGPT API 服務
"""
import openai
import json
from typing import List, Dict, Any
from config import settings
from models import TranscriptSentence, SyllableData, UnifiedData, SentenceWithClips, Clip


class ChatGPTService:
    
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
    
    async def rewrite_script(
        self, 
        original: List[TranscriptSentence],
        syllable_data: SyllableData
    ) -> List[TranscriptSentence]:
        """
        改寫 script，保持句數和發音密度
        """
        prompt = f"""
你是專業編劇。請根據以下原文改寫成全新內容：

原文句子數：{len(original)}
目標發音密度：{syllable_data.syllables_per_sec:.2f} 發音/秒

原文：
{json.dumps([{"index": s.index, "text": s.text, "syllables": s.syllables} for s in original], ensure_ascii=False, indent=2)}

要求：
1. 保持相同句子數量
2. 每句含義可完全不同，但情緒/節奏相似
3. 總發音數接近原文（誤差 ±10%）
4. 返回 JSON 格式

返回格式：
[
  {{"index": 0, "text": "新句子..."}},
  ...
]
"""
        
        response = await openai.ChatCompletion.acreate(
            model=settings.GPT_MODEL,
            messages=[
                {"role": "system", "content": "你是專業編劇和語言學家"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        
        content = response.choices[0].message.content
        # 清理可能的 ```json
        content = content.replace("```json", "").replace("```", "").strip()
        new_sentences_data = json.loads(content)
        
        # 轉回 TranscriptSentence
        new_sentences = []
        for item in new_sentences_data:
            new_sentences.append(
                TranscriptSentence(
                    index=item["index"],
                    text=item["text"],
                    start=0.0,  # 之後會重算
                    end=0.0,
                    duration=0.0
                )
            )
        
        return new_sentences
    
    async def unify_style_and_prompts(
        self,
        analyzed_frames: List[Dict],
        new_script: List[TranscriptSentence],
        syllable_data: SyllableData
    ) -> UnifiedData:
        """
        統一風格 + 生成每句的 base prompt
        """
        prompt = f"""
你是 AI 影片製作專家。根據以下信息：

1. Frame 分析結果（Qwen-VL3 反推）：
{json.dumps(analyzed_frames[:5], ensure_ascii=False, indent=2)}
...（共 {len(analyzed_frames)} 張）

2. 新 script：
{json.dumps([{"index": s.index, "text": s.text} for s in new_script], ensure_ascii=False, indent=2)}

請：
1. 總結影片主題
2. 統一角色設定（外貌、服裝、特徵）
3. 統一場景風格（寫實/卡通、色調、燈光）
4. 為每句生成 base image prompt（不分 clip）

返回 JSON：
{{
  "summary": "影片主題總結...",
  "global_style": {{
    "art_style": "realistic/anime/...",
    "color_tone": "warm/cold/...",
    "lighting": "soft/dramatic/..."
  }},
  "characters": [
    {{"name": "角色A", "appearance": "..."}}
  ],
  "locations": [
    {{"name": "地點1", "description": "..."}}
  ],
  "per_sentence": [
    {{
      "index": 0,
      "text": "...",
      "base_prompt": "統一風格的場景描述..."
    }}
  ]
}}
"""
        
        response = await openai.ChatCompletion.acreate(
            model=settings.GPT_MODEL,
            messages=[
                {"role": "system", "content": "你是 AI 影片風格設計師"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        
        # 計算每句 num_clips
        counter = SyllableCounter()
        per_sentence_with_clips = []
        
        for item in data["per_sentence"]:
            sentence = new_script[item["index"]]
            syllables = counter.count_syllables(sentence.text)
            duration = syllables / syllable_data.syllables_per_sec
            num_clips = max(1, int(duration / 3) + (1 if duration % 3 > 0 else 0))
            
            # 暫時用 base_prompt 重複
            clips = [
                Clip(
                    clip_id=f"{item['index']:02d}{chr(97+i)}",  # 00a, 00b...
                    prompt=item["base_prompt"]
                )
                for i in range(num_clips)
            ]
            
            per_sentence_with_clips.append(
                SentenceWithClips(
                    index=item["index"],
                    text=item["text"],
                    duration=duration,
                    num_clips=num_clips,
                    clips=clips
                )
            )
        
        return UnifiedData(
            summary=data["summary"],
            global_style=data["global_style"],
            characters=data["characters"],
            locations=data["locations"],
            per_sentence=per_sentence_with_clips
        )
    
    async def verify_image_quality(
        self,
        qwen_result: Dict,
        original_prompt: str
    ) -> Dict[str, Any]:
        """
        用 ChatGPT 判斷圖片是否符合要求
        """
        prompt = f"""
原提示詞：{original_prompt}

Qwen-VL3 分析結果：
{json.dumps(qwen_result, ensure_ascii=False)}

判斷：
1. 是否有 NSFW 或不當內容？
2. 是否符合原提示詞的風格和內容？
3. 是否有明顯錯誤（角色錯、場景錯）？

返回 JSON：
{{
  "status": "ok" 或 "bad",
  "reason": "原因..."
}}
"""
        
        response = await openai.ChatCompletion.acreate(
            model=settings.GPT_MODEL,
            messages=[
                {"role": "system", "content": "你是圖片質量審核專家"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)