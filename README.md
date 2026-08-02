# Demo Video Creator — Phase 1（分析與企劃）

輸入參考影片 → 本機前處理（ffprobe + 鏡頭切割）→ Gemini 抽象化理解 →
Claude 產生三套原創企劃與逐鏡提示詞 → 人工審核批准 → 匯出 JSON / Markdown。

Phase 1 **不生成任何影片**，對應 [COMPANY_AI_HANDOFF.md](COMPANY_AI_HANDOFF.md) 第 8 節的最低風險落地方案，改為個人環境直連 API（不經 Bedrock Gateway）。

## 模型配置

| 角色 | 預設模型 | 說明 |
|---|---|---|
| 影片理解 | `gemini-2.5-flash`（Gemini API） | 原生影片輸入，免費層可用 |
| 企劃/分鏡 | `claude-sonnet-5`（Anthropic API） | Phase 1 足夠；輸出驗證失敗或被拒絕時**自動升級** `claude-opus-5` 重試 |

全部可在 `.env` 覆寫（`ANALYZER_MODEL` / `PLANNER_MODEL` / `PLANNER_ESCALATION_MODEL`）。

## 安裝

```powershell
# 1. FFmpeg（若尚未安裝）
winget install Gyan.FFmpeg

# 2. Python 環境
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. API keys
copy .env.example .env
# 編輯 .env 填入 ANTHROPIC_API_KEY 與 GEMINI_API_KEY
```

- Anthropic API key：<https://platform.claude.com/>（pay-as-you-go，需儲值少量額度；與 Claude 訂閱分開計費）
- Gemini API key：<https://aistudio.google.com/apikey>（有免費層）

## 執行

```powershell
streamlit run app.py
```

## 專案結構

```text
app.py                       Streamlit 操作介面（上傳 → 前處理 → 生成 → 審核 → 匯出）
src/
├── config.py                模型與路徑設定（.env 覆寫）
├── schemas.py               Pydantic 資料結構（抽象化分析、企劃、分鏡…）
├── ingest.py                ffprobe / PySceneDetect / OpenCV 影格擷取
├── pipeline.py              流程編排與匯出
├── store.py                 SQLite 紀錄（來源、權利聲明、批准 — 可追溯性）
└── providers/
    ├── base.py              AnalysisProvider / PlanningProvider 抽象層
    ├── gemini_analyzer.py   Gemini 影片理解
    └── claude_planner.py    Claude 企劃生成（Sonnet 5 → Opus 5 自動升級）
workspace/                   （自動建立）影格、輸出、SQLite；已被 .gitignore 排除
```

## 產出

- `workspace/outputs/runN_*.json`：完整結構化企劃（Phase 2 直接取用逐鏡 prompt）
- `workspace/outputs/runN_*.md`：可讀版企劃書
- `workspace/phase1.db`：來源 URL/路徑、權利聲明、模型、批准紀錄

## 原創性守則（內建於 prompt 與 schema）

- 只萃取類型慣例與一般攝影語言，不逐鏡對應參考影片
- 全虛構隊伍/角色/品牌，參考影片中觀察到的受保護元素自動列入禁止清單
- 每套企劃附相似度風險備註（僅風險提示，不代表法律安全）
- 生成前一律人工審核批准，所有紀錄落入 SQLite

## 下一步（Phase 2）

`VideoProvider` 抽象層已預留：接 Veo（Gemini API，付費）逐鏡生成 5 秒測試鏡頭，
沿用 Phase 1 匯出的 `shots[].prompt` 與 negative constraints。
