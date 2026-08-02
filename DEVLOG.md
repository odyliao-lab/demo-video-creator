# 開發歷程

從公司環境評估文件（[COMPANY_AI_HANDOFF.md](COMPANY_AI_HANDOFF.md)）到個人電腦可執行的實作紀錄。
最後更新：2026-08-02。

## 起點：為什麼模型層要整個換掉

交接文件假設所有模型存取統一走**公司的 Amazon Bedrock Gateway**（Nova 2 Lite 影片理解、
Bedrock Claude/GPT 企劃、Nova Canvas 圖像、Luma Ray 2 影片生成、S3 非同步輸出、IAM/KMS 權限）。
個人環境沒有這些，因此改為直連各家 API。

一個關鍵觀念：**訂閱 ≠ API**。Claude / ChatGPT / Gemini 的訂閱是聊天與 coding agent 的使用權，
不含程式呼叫的 API 額度。正確分工是——**訂閱拿來當開發工具，執行時用另外申請的 API key**。

### 模型替換對照

| 原設定（公司 Bedrock） | 個人環境替代 | 說明 |
|---|---|---|
| Nova 2 Lite（影片理解） | **Gemini API** `gemini-2.5-flash` | 原生吃影片輸入，有免費層 |
| Bedrock Claude/GPT（企劃分鏡） | **Anthropic API** `claude-sonnet-5` | 結構化輸出足夠；失敗自動升級 `claude-opus-5` |
| Nova Canvas（圖像） | 暫未實作 | Phase 2 未使用參考圖 |
| Luma Ray 2 + S3（影片生成） | **fal.ai** Seedance/Kling（預設）或 **Veo**（Gemini API） | 見下方成本比較 |
| boto3 / S3 / IAM / KMS | 本機檔案系統 + SQLite | 全部移除 |

文件 7.2 節的 Provider 抽象層設計**原封保留**，只換實作——這個決定後來讓「加入 fal.ai」
只需新增一個檔案加一個工廠函式，沒有動到任何既有流程。

## Phase 1：分析與企劃（已完成）

流程：上傳影片 → 權利聲明 → 本機前處理（ffprobe + PySceneDetect + OpenCV 影格）
→ Gemini 抽象化理解 → Claude 產生三套原創企劃與逐鏡提示詞 → 人工審核批准 → 匯出 JSON/Markdown。

**首次實測（run1）：** 來源影片切出 126 個鏡頭，Gemini 完成抽象化分析，
`claude-sonnet-5` **一次通過、未觸發升級**，產出三套各 6 鏡的企劃
（《紫宸迷局》《海上折枝》《琉璃長夜》）。成本僅數美分——印證了 Sonnet 5 足以應付企劃工作。

### 踩到的坑：ffprobe WinError 2

winget 剛裝完 FFmpeg 時，**已在執行中的 Streamlit 伺服器仍持有安裝前的 PATH**，
直接呼叫 `ffprobe` 會噴 `WinError 2 系統找不到指定的檔案`。
解法是不依賴 PATH：`shutil.which` 找不到時，回退掃描 winget 的 Links/Packages 目錄（commit `4f92d14`）。

## Phase 2：逐鏡生成（已完成）

讀取 Phase 1 匯出 → 選企劃與鏡頭 → 成本確認 → 逐鏡生成 → 記錄驗收指標。

**三層成本護欄**（因為影片生成是整條 pipeline 唯一昂貴的環節）：
預設只勾前 3 鏡、單批上限 `MAX_SHOTS_PER_BATCH`、必須勾選「我了解這會呼叫付費 API」才能生成。

### 供應商選擇：從 Veo 轉向 fal.ai

初版接 Veo（文件 6.6 節推薦），但實際比價後發現差距極大（2026 年中第三方比價資料）：

| 模型 | 約略單價 | 5 鏡 × 5 秒的成本 |
|---|---|---|
| Seedance 2.0 Fast（fal） | ~$0.022/秒 | ~$0.55 |
| Kling 3.0（fal） | ~$0.029/秒 | ~$0.73 |
| Veo 3.1 Fast | ~$0.15/秒 | ~$3.75 |
| Veo 3.1 標準 | ~$0.40–0.75/秒 | ~$10–19 |

於是新增 `FalVideoProvider` 與 provider 工廠，用 `.env` 的 `VIDEO_PROVIDER` 一行切換
`fal` / `veo`，兩邊實作都保留（commit `e67e76f`）。

實作差異需注意：Veo 支援 4/6/8 秒、Seedance/Kling 支援 5/10 秒，
故 `clamp_duration()` 下放到各 provider 自行決定；
**Seedance 不吃 negative prompt，Kling 支援**——若很在意「不得出現真實品牌」這類約束能傳達給模型，Kling 較安全。

### 首次生成實測（Seedance 2.0 Fast，5 鏡）

| 指標 | 結果 |
|---|---|
| 成功率 | 5/5（100%） |
| 平均生成耗時 | 178 秒／鏡（144–269 秒） |
| 重試 | 1 鏡重試一次後成功 |
| 總成本 | 25 秒 ≈ **$0.55 USD** |

比 Veo 標準版路線便宜約 20–30 倍。但**生成速度不快**——每鏡約 3 分鐘，
未來生成完整一分鐘影片（12–15 鏡）需預留半小時以上。

## 目前狀態與已知缺口

- Phase 1、Phase 2 皆可端到端執行，紀錄落在 `workspace/phase1.db`（`runs` / `approvals` / `generation_jobs`）
- **尚未做品質驗收**：文件第 12 章的角色一致性、球衣顏色、球體變形、鏡頭連續性、
  是否出現真實品牌等項目，需人工看片評估
- **重試記錄缺口**：目前只有「最終失敗」才寫入 error，重試後成功的第一次失敗原因會遺失
- **Phase 3 未開始**：串接鏡頭、字幕/比分/AI 生成標示、4K 升頻與插幀（需 GPU 或雲端服務）

## 下一步選項

1. 換 Kling 或 Seedance 標準版跑同一批鏡頭，做品質／成本對照
2. 進 Phase 3：FFmpeg 串接成片、加字幕與 AI 生成標示
3. 補上每次嘗試都記錄錯誤的邏輯，累積「哪類 prompt 容易失敗」的資料
