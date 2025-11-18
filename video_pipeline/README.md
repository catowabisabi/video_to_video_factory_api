# AI Video Auto-Production Engine  
# 全自動 AI 影片製作引擎（Python 版本）

This project is a **fully automated AI video generation pipeline**, powered by Python.  
It processes an input video and produces a completely new AI-generated version with rewritten script, regenerated visuals, music, TTS voice, and final assembly.

本項目是一套 **全自動 AI 影片再創作引擎**，以 Python 為核心。  
輸入一條影片，即可自動完成腳本重寫、圖片反推、生圖、生片、TTS、音樂以及最終影片合成。

---

## 🚀 Key Features / 主要功能

### 🎬 1. Video Processing  
- Extract audio (MP3)  
- Read metadata: FPS, resolution, duration  
- Frame extraction  

### 🎬 1. 影片處理  
- 抽取音頻（MP3）  
- 影片資訊：FPS、解像度、時長  
- 抽取畫面截圖  

---

### 🗣️ 2. Transcription (Whisper ASR)  
- Sentence-level timestamps  
- Language detection  

### 🗣️ 2. 自動字幕辨識（Whisper）  
- 逐句時間戳  
- 語言自動辨識  

---

### 🔢 3. Syllable Counting  
Used to control reading tempo and match the final TTS pacing.

### 🔢 3. 發音數計算  
用於控制語速，令最終 TTS 與影片節奏一致。

---

### ✏️ 4. Script Rewrite (ChatGPT)  
- Rewrites the entire transcript  
- Keeps timing density similar (±10%)  
- Auto-retry until pacing is correct  

### ✏️ 4. ChatGPT 腳本重寫  
- 全文重寫（不同文字、相同意思）  
- 語速密度維持 ±10%  
- 自動重試直到語速吻合  

---

### 🖼️ 5. Frame Extraction → Qwen-VL3 Reverse Caption  
- Extract frames every 3 seconds  
- Qwen-VL3 generates:  
  - Title  
  - Caption  
  - Image generation prompt

### 🖼️ 5. 抽圖 → Qwen-VL3 圖片反推  
- 每 3 秒抽一張圖  
- 使用 Qwen-VL3 生成：  
  - 標題  
  - 內容描述  
  - 文生圖提示詞  

---

### 🎨 6. Image Generation  
- Stable Diffusion / ComfyUI / any external API  
- With automatic NSFW & error checking  

### 🎨 6. 文生圖  
- 支援 Stable Diffusion / ComfyUI / 外部 API  
- 自動 NSFW／錯誤檢查  

---

### 🎞️ 7. Image → Video Clip  
- Generate 3-second clips  
- Maintain style consistency  

### 🎞️ 7. 圖生影片  
- 每張圖生成 3 秒影片  
- 保持畫風一致  

---

### 🔊 8. Audio Generation  
- ElevenLabs TTS  
- Suno AI instrumental music  
- Auto cutting / looping / fading  

### 🔊 8. 聲音生成  
- ElevenLabs 對白  
- Suno 自動生成背景音樂  
- 自動剪接、Loop、Fade Out  

---

### 🧩 9. Video Assembly  
- Merge clips according to timing  
- Adjust clip speed to match TTS  
- Generate final MP4 + SRT  

### 🧩 9. 最終影片組裝  
- 按句子時間拼接片段  
- 自動調速對齊 TTS  
- 輸出最終 MP4 + SRT  

---

## 📂 Project Structure / 專案結構說明

video_pipeline/
├── main.py # FastAPI 程式入口 / API Entry point
├── config.py # 系統設定 / Config & Keys Loader
├── models.py # Pydantic 請求/回應模型

├── services/
│ ├── video_processor.py # 影片處理 / Video metadata + audio extract
│ ├── transcription.py # Whisper ASR / 字幕辨識
│ ├── syllable_counter.py # 發音數計算 / Syllable Calculator
│ ├── frame_extractor.py # 抽 frame / Frame grabbing
│ ├── qwen_service.py # Qwen-VL3 API
│ ├── chatgpt_service.py # ChatGPT API
│ ├── image_gen.py # 文生圖 / Image generation
│ ├── video_gen.py # 圖生片 / Image2Video
│ ├── tts_service.py # ElevenLabs TTS
│ ├── music_service.py # Suno 背景音樂
│ └── video_assembly.py # 合成影片 / Final Assembly

├── utils/
│ ├── file_manager.py # 檔案管理 / File utils
│ └── retry_handler.py # 重試策略 / Retry logic

├── .env # API key（勿上傳）
├── .env.example # 範例設定
├── .gitignore # Git 忽略項目
└── requirements.txt # 套件依賴

## 🔧 Environment Variables (.env)  

API Keys / API 密鑰
OPENAI_API_KEY=sk-xxxxx
QWEN_API_KEY=sk-xxxxx
ELEVENLABS_API_KEY=xxxxx
SUNO_API_KEY=xxxxx
IMAGE_GEN_API_KEY=xxxxx
VIDEO_GEN_API_KEY=xxxxx

Settings / 系統設定
WHISPER_MODEL=large-v3
GPT_MODEL=gpt-4o
LANGUAGE=zh-TW

---

bash# 1. 安裝依賴
pip install -r requirements.txt

# 2. 安裝 ffmpeg（如未安裝）
# Ubuntu/Debian:
sudo apt update && sudo apt install ffmpeg

# macOS:
brew install ffmpeg

# 3. 建立 .env
cp .env.example .env
# 填入你的 API keys

# 4. 啟動 API
python main.py

# 或用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

使用方式
1. 上傳影片啟動 pipeline
bashcurl -X POST "http://localhost:8000/api/pipeline/start" \
  -F "file=@video1.mp4" \
  -F "title=我的影片"
回應：
json{
  "job_id": "20241117_153045",
  "message": "Pipeline started"
}
2. 查詢進度
bashcurl "http://localhost:8000/api/pipeline/status/20241117_153045"
回應：
json{
  "status": "running",
  "current_step": "image_generation",
  "progress": 65,
  "errors": [],
  "warnings": ["Attempt 2: 發音數差 12.3%..."]
}
```

---

## 評論與建議

### ✅ 優點
1. **模塊化設計**：每個步驟獨立 service，易於測試和替換
2. **非同步處理**：用 async/await，適合 I/O 密集任務
3. **錯誤處理**：重試機制 + 警告通知
4. **靈活性**：可以輕鬆換 API（例如 Whisper → Deepgram）

### ⚠️ 需要注意
1. **成本**：
   - 一條 5 分鐘影片可能需要：
     - Whisper: ~$0.30
     - ChatGPT 多次調用: $1-3
     - Qwen-VL3: $2-5（看圖片數）
     - 文生圖 20-50 張: $5-20
     - 圖生影片: $10-50
     - TTS + 音樂: $2-5
   - **總計：$20-80+**

2. **時間**：
   - 單條影片可能需要 **30-120 分鐘**（視 API 速度）

3. **質量控制**：
   - 發音數匹配只是「近似」，實際 TTS 會有停頓
   - 圖片生成質量不穩定，可能需要多次重試

4. **建議優化**：
   - 用 **Celery + Redis** 做任務隊列（而非簡單 BackgroundTasks）
   - 加入 **數據庫**（PostgreSQL）儲存 job 狀態
   - 用 **Webhook** 通知完成（而非輪詢）
   - 加入 **前端 UI**（React + WebSocket 實時進度）

---

## 與 n8n 整合方案

如果你想用 **n8n 做編排**：

1. **n8n 負責**：
   - HTTP Request nodes 調用此 API
   - 條件判斷（IF）
   - Email / Telegram 通知
   - Schedule（排程）

2. **Python API 負責**：
   - 所有重計算邏輯
   - 文件處理
   - API 調用

**範例 n8n workflow**：
```
[Webhook] → [HTTP: /api/pipeline/start] 
    → [Wait 1min] 
    → [Loop: Check /api/pipeline/status] 
    → [IF status=completed] 
        → [Send Email] 
    → [ELSE IF status=failed] 
        → [Telegram Alert]


🧑‍💻 Author / 作者
Catowabisabi (CL)