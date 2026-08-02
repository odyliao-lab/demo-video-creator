# AI 影片創作工具：公司環境能力盤點與 MVP 評估交接文件

更新日期：2026-08-01
預計程式碼 Repository：<https://github.com/odyliao-lab/demo-video-creator.git>

## 1. 給接手 AI 的任務

請以公司目前實際核准的 AI、Amazon Bedrock Gateway、AWS 帳號權限及本機工具為準，評估本文描述的 AI 影片創作工具能做到什麼程度。

本階段只要求：

1. 唯讀盤點公司可用資源與限制。
2. 提供有證據的能力矩陣。
3. 提出可落地的 MVP 方案與缺口。
4. 列出需要向平台、資安、法務或採購團隊確認的事項。

除非使用者另行明確授權，請勿：

- 建立或修改雲端資源。
- 啟用新模型、提高 quota 或產生付費影片。
- 建立 S3 Bucket、IAM Role、KMS Key 或外部 API 帳號。
- clone、修改或 push 上述 Repository。
- 上傳任何公司機密、第三方影片或可能受著作權保護的素材。
- 顯示、保存或要求使用者貼出 API key、AWS secret、session token 等憑證。

## 2. 使用者的核心想法

使用者希望開發一個 Python 程式，輸入來源可以是：

- 使用者電腦中的影片檔案；或
- 公開 YouTube 影片網址（必須受公司政策、平台條款及權利確認機制限制）。

使用者另行輸入希望加入或修改的創作要求，程式先分析參考影片，產生一份「抽象化、原創化」的影片企劃及逐鏡提示詞。使用者確認或編輯後，程式才呼叫影片生成模型，最後依指定技術規格輸出。

目標流程：

```text
YouTube URL／本機影片
        ↓
權利及使用範圍確認
        ↓
影片解析、音訊轉錄、場景切割、代表影格擷取
        ↓
多模態模型理解內容
        ↓
只保留主題、事實、類型慣例與一般攝影語言
        ↓
加入使用者的角色、故事、視覺風格及輸出要求
        ↓
產生多套原創企劃、分鏡、鏡頭提示及禁止元素
        ↓
人工修改及批准
        ↓
逐鏡生成短影片
        ↓
剪輯、字幕、記分板、旁白、音效及來源紀錄
        ↓
輸出 MP4，例如 3840×2160、30fps、指定 bitrate／檔案大小
```

## 3. 代表性使用案例

參考來源可能是一支足球賽事 Highlight，但成品不是替換原影片角色的仿製品。

使用者希望建立完全虛構的賽事，例如：

- 鋼角犀牛隊（Steelhorn Rhinos）
- 極光白熊隊（Aurora Polar Bears）
- 虛構球員、球場、球衣、隊徽、比分及轉播包裝
- 不使用真實 FIFA／世界盃／聯賽／球隊／球員／贊助商品牌
- 明確標示為虛構 AI 生成賽事

可以參考足球 Highlight 的一般製作語言，例如：

- 高位廣角追球
- 場邊低角度攝影
- 球門後方鏡頭
- 球員反應特寫
- 慢動作重播
- 戰術圖解

不得以「避開偵測」為目的，也不得逐秒重製單一來源影片的：

- 鏡頭順序
- 攝影機位置與運鏡組合
- 攻防事件及跑位
- 剪輯節奏與轉場
- 招牌台詞、旁白、音樂或音效
- 記分板、字幕、Logo 或轉播視覺包裝

輸出格式範例：

```yaml
container: mp4
video_codec: h264
width: 3840
height: 2160
fps: 30
video_bitrate: 40M
audio_codec: aac
audio_bitrate: 384k
pixel_format: yuv420p
```

如果影片模型只生成 720p／1080p 或 24fps，程式必須清楚標示最終成品是升頻或插幀，不得宣稱為原生 4K／30fps。

## 4. 產品安全與權利原則

本工具的目標是「從參考影片萃取不受保護的概念、事實、功能及類型慣例，再產生獨立的新作品」，不是把原作修改到難以辨識。

系統至少應設置以下關卡：

1. 來源權利聲明：自有、已授權、Creative Commons／公版，或僅作抽象化分析。
2. 禁止直接沿用原畫面、音軌、字幕、Logo、人物及品牌元素。
3. 產生新企劃時主動改變敘事順序、角色、場景、事件、鏡頭排列及聲音設計。
4. 生成前提供人工審核，不得自動發布。
5. 保存來源 URL、使用者聲明、提示詞、模型、版本、素材授權及批准紀錄。
6. 對寫實但未真實發生的內容保留 AI 生成標示及平台揭露資訊。
7. 相似度檢查只能作為風險提示，不能宣稱「法律安全」或提供固定安全百分比。

如公司法務有更嚴格要求，以公司政策為準。

## 5. 已知的公司技術背景

使用者表示公司提供 Claude、Gemini、Codex，但模型存取統一經過 Amazon Bedrock Gateway。

目前尚不清楚：

- 「Gateway」是 AWS 原生 `bedrock-runtime`／`bedrock-mantle`，還是公司自建代理。
- 公司所稱 Gemini 是獨立 Google／Vertex AI 路由、Bedrock 中的 Gemma，或只是聊天產品。
- 公司所稱 Codex 是 Codex 產品、OpenAI GPT 模型，或公司包裝的程式代理。
- Gateway 是否只代理同步 Chat／Responses／Messages API。
- Gateway 是否支援 AWS `StartAsyncInvoke`、S3 非同步輸出及影片模型。
- 哪些 model ID、Region、Inference Profile、quota 及 IAM action 已核准。

不要從產品名稱推斷能力；請查實際 model ID、輸入／輸出 modality 和公司 allowlist。

## 6. 公開 AWS 文件顯示的候選能力

以下只是截至 2026-08-01 的公開資料，不能視為公司帳號已經開放。請在公司環境重新驗證。

### 6.1 影片理解

候選：Amazon Nova 2 Lite

- 可接受文字、圖片及影片輸入。
- 輸出是文字，不是影片。
- 可用於影片摘要、事件描述及企劃前處理。
- 高速足球影片仍應搭配本機 PySceneDetect／OpenCV，避免低取樣率漏掉快速剪接。

官方參考：<https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-2-lite.html>

Claude 或 OpenAI LLM 也可用於企劃及提示詞，但若模型不接受影片輸入，必須先由本機程式抽取影格、音訊與時間碼。

### 6.2 企劃、分鏡與結構化輸出

可考慮公司 Gateway 已核准的：

- Anthropic Claude Sonnet／Opus 系列；或
- OpenAI GPT-5.6 Terra／Sol 系列；或
- Amazon Nova 系列。

用途包括：

- 參考內容抽象化
- 合併使用者需求
- 建立原創角色及世界觀
- 產生三套差異明顯的企劃
- 產生結構化分鏡 JSON
- 產生每鏡 prompt／negative constraints
- 檢查新分鏡是否過度對應來源

模型選擇必須依公司實際 model ID、成本、資料政策及評測結果決定。

### 6.3 圖像生成

候選：Amazon Nova Canvas，或公司已核准的 Stability AI 圖像模型。

用途：

- 原創球隊隊徽
- 球衣與角色 design sheet
- 場館概念圖
- 每鏡開始／結束參考影格

所有參考圖都應自行生成、拍攝或具有足夠商用授權。

### 6.4 影片生成

公開 Bedrock 文件中的直接候選：Luma Ray 2

```text
modelId: luma.ray-v2:0
```

公開規格顯示：

- 文字轉影片
- 圖片轉影片
- 可指定開始／結束 keyframe
- 5 秒或 9 秒
- 540p 或 720p
- 使用 `StartAsyncInvoke`
- 成品寫入指定 S3 Bucket

官方參考：<https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-luma.html>

因此即使公司開放 Luma Ray 2，4K 30fps 仍需要後製升頻及插幀；第一版應將「720p 生成」與「4K 交付」分開描述。

### 6.5 不建議採用的候選

Amazon Nova Reel 已被 AWS 列為 Legacy，公開文件顯示 EOL 為 2026-09-30，不宜作為新專案核心。

官方參考：<https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-reel.html>

OpenAI Sora 2 Videos API 也已公告將於 2026-09-24 關閉，不宜建立新的長期相依。

官方參考：<https://developers.openai.com/api/docs/guides/video-generation>

### 6.6 Bedrock以外的可能選項

若公司 Gateway 另有正式核准路由，可以再評估：

- Google Gemini Omni Flash：快速影片生成及對話式修改。
- Google Veo 3.1：4K、參考圖、首尾影格及原生音訊。
- Adobe Firefly Video：企業商用及智慧財產權治理導向。
- Runway Gen-4.5：文字／圖片轉影片及成熟的創作 API。
- Kling Video 3.0：多鏡頭、動作及元素一致性。

若公司只允許 Bedrock，請不要把這些模型列為可直接使用；應列入「需要新增供應商或 Gateway 路由」的缺口。

## 7. 建議的 Python 技術架構

### 7.1 本機及後端元件

```text
Python 3.12+
├── Streamlit：MVP操作介面
├── FastAPI：後續正式API
├── Pydantic：分析及分鏡schema
├── FFmpeg／ffprobe：音訊、影格、剪輯、編碼
├── PySceneDetect：鏡頭切割
├── OpenCV：影格處理及相似度輔助
├── SQLite：工作、批准及素材紀錄
├── boto3：Bedrock／S3／非同步工作
└── RQ／Celery：正式版背景工作佇列
```

### 7.2 模型供應商抽象層

不要把應用程式直接綁死在單一 model ID：

```python
class AnalysisProvider:
    def analyze_video(self, source, policy): ...

class PlanningProvider:
    def create_treatment(self, analysis, user_request): ...

class ImageProvider:
    def create_reference(self, prompt): ...

class VideoProvider:
    def generate_shot(self, shot, references, output_location): ...
```

預期實作：

```text
AnalysisProvider
└── BedrockNovaVideoAnalyzer

PlanningProvider
├── BedrockClaudePlanner
├── BedrockOpenAIPlanner
└── BedrockNovaPlanner

ImageProvider
└── BedrockNovaCanvasProvider

VideoProvider
├── BedrockLumaProvider
├── VertexVeoProvider（只有公司核准後）
├── AdobeFireflyProvider（只有公司核准後）
└── RunwayProvider（只有公司核准後）
```

### 7.3 建議資料結構

至少定義：

- `SourceAsset`
- `SourceRightsDeclaration`
- `TechnicalMetadata`
- `TranscriptSegment`
- `SceneObservation`
- `ReferenceAbstraction`
- `AvoidedElements`
- `OriginalTreatment`
- `CharacterBible`
- `ShotPlan`
- `ShotPrompt`
- `ApprovalRecord`
- `GenerationJob`
- `AssetLicenseRecord`
- `DeliverySpec`
- `RiskReview`

記分板、字幕、Logo、比分和聲明應以程式後製，不應交由影片模型直接生成，以免文字錯誤。

## 8. 建議 MVP 範圍

### Phase 0：公司能力盤點

- 列出 Gateway 實際 model ID。
- 確認 input／output modality。
- 確認同步與非同步 API。
- 確認 S3、IAM、KMS、Region、quota、日誌和資料保存政策。
- 確認能否將本機影片上傳至公司核准環境。

### Phase 1：只做分析及企劃，不生成影片

- 上傳本機 MP4。
- `ffprobe` 讀取技術資料。
- PySceneDetect分析剪接點。
- 擷取代表影格及音訊。
- 公司核准模型產生抽象摘要及三套原創企劃。
- 使用者編輯並批准。
- 匯出完整企劃 JSON／Markdown。

此階段最容易落地，且不需要影片生成 API。

### Phase 2：小型影片 PoC

- 使用自製或生成的虛構角色參考圖。
- 只生成 3～5 個、每個 5 秒的測試鏡頭。
- 比較動作、球、角色、球衣及鏡頭一致性。
- 不製作完整一分鐘影片。
- 記錄每鏡成本、耗時、失敗率及重試次數。

### Phase 3：完整影片

- 逐鏡生成。
- 加入旁白、音效、字幕及比分。
- 串接 S3工作和背景佇列。
- 組合 Master。
- FFmpeg／AI upscaler／插幀輸出 4K 30fps。
- 產生來源、模型、提示及授權報告。

## 9. 請在公司環境查證的問題

請逐項回答，未知就標示「未知」，不要猜測。

### Gateway與模型

1. Gateway 的正式名稱、Base URL類型及維護團隊為何？
2. 它是 `bedrock-runtime`、`bedrock-mantle` 還是公司自建代理？
3. 可用 model ID完整清單為何？
4. 哪些模型接受影片輸入？
5. 哪些模型輸出影片？
6. 公司所稱 Gemini實際對應哪個 model ID和供應商？
7. 公司所稱 Codex實際是 Codex產品、OpenAI模型，還是內部代理？
8. 是否開放 `luma.ray-v2:0`？
9. 是否有其他影片模型，但未出現在一般 LLM model picker？

### API與AWS權限

10. Gateway是否支援 `StartAsyncInvoke`、`GetAsyncInvoke`及工作取消？
11. 是否允許應用程式指定 S3 output URI？
12. 是否已有專案專用 Bucket、prefix及 lifecycle policy？
13. 所需 IAM action及 service role為何？
14. S3與 Bedrock是否必須在同一 Region？
15. 是否要求 KMS CMK、VPC endpoint或 PrivateLink？
16. 可用 quota、併發數、影片生成日／月預算為何？
17. 是否允許使用 company-managed Bedrock API key，或必須使用 IAM role／STS？

### 資安、資料及法務

18. 是否允許把本機影片、公開 YouTube影片或第三方授權影片傳入模型？
19. 哪些資料分類禁止上傳？
20. Prompt、輸入影片、輸出影片和日誌保存多久？
21. 是否允許 preview／Marketplace第三方模型？
22. Luma使用條款及公司合約是否允許商業輸出？
23. 是否有內容憑證、浮水印或 AI揭露要求？
24. 法務是否要求人工審核、授權紀錄或相似度門檻？

### 本機運算

25. 開發機是否已有 FFmpeg／ffprobe？
26. 是否可安裝 PySceneDetect、OpenCV及 Python套件？
27. 是否有 NVIDIA GPU可執行 RIFE或 AI upscaler？
28. 如果沒有 GPU，是否允許使用 AWS MediaConvert或其他核准服務？

## 10. 可使用的唯讀盤點方法

請優先使用公司現有文件、Gateway `/models`端點及 AWS唯讀 API。不要輸出憑證。

AWS原生例子：

```powershell
aws bedrock list-foundation-models
aws bedrock list-foundation-models --by-input-modality VIDEO
aws bedrock list-foundation-models --by-output-modality VIDEO
aws bedrock get-foundation-model --model-identifier luma.ray-v2:0
```

若 Gateway提供 OpenAI相容介面：

```http
GET /v1/models
```

注意：Gateway `/v1/models`可能只列出公司 allowlist，而 AWS API可能列出帳號可見但員工無權呼叫的模型。兩者都要區分「可見」與「可實際使用」。

## 11. 接手 AI 的回覆格式

請用以下結構回覆使用者：

### A. 結論

- 目前公司環境最高可做到哪一階段：Phase 0／1／2／3。
- 能否直接生成影片。
- 能否達成原生或後製 4K 30fps。

### B. 已確認資源

以表格列出：

| Model ID／工具 | 來源 | 輸入 | 輸出 | API | Region | 權限狀態 | 證據 |
|---|---|---|---|---|---|---|---|

### C. 尚未確認項目

- 明確列出未知事項。
- 說明需要哪個團隊或文件才能確認。

### D. 可落地架構

- 逐階段列出實際使用的模型、Python套件、API及儲存位置。
- 標明哪些是公司現有，哪些需要申請。

### E. PoC計畫

- 建議最小測試素材。
- 預計生成鏡頭數及秒數。
- 驗收標準。
- 估計成本、時間及失敗處理方式；若無價格資料，不要虛構數字。

### F. 阻礙及申請項目

- IAM／S3／模型存取／quota／法務／資安／外部供應商。

### G. 建議下一步

- 只提出一個風險最低、資訊增益最高的下一步。

## 12. PoC驗收標準

第一個影片生成 PoC不以「看起來很華麗」為唯一標準，至少評估：

- Prompt遵循程度
- 犀牛／北極熊角色一致性
- 球衣及隊伍顏色一致性
- 足球是否變形、消失或瞬移
- 球員數量是否不合理變動
- 動作與攝影機運動是否自然
- 鏡頭之間能否維持連續性
- 是否出現真實球隊、FIFA或第三方品牌元素
- 是否能成功加入正確比分與字幕
- 每鏡生成耗時
- 每鏡成本
- 失敗率及重試結果
- 720p升頻至4K後的品質
- 24fps轉30fps後是否產生重影或扭曲
- 完整來源、提示詞、模型及批准紀錄是否可追溯

## 13. 期望的最終方向

若公司只允許同步 LLM Gateway，仍可完成 Phase 1：參考影片分析、原創企劃、分鏡及提示詞產生器。

若公司另行開放 Bedrock非同步影片生成、Luma Ray 2和 S3，則可完成 Phase 2，並評估 Phase 3；但 Bedrock公開規格中的 Luma Ray 2只生成最高720p，4K30需要後製。

如果公司需要原生4K、更高動作品質或更完整的角色一致性，應在完成 Bedrock PoC後，以實測證據向平台及採購團隊提出 Veo、Adobe Firefly、Runway或其他核准影片供應商需求，而不是一開始就繞過公司 Gateway。

本專案程式應始終採用可替換的 Provider架構，讓分析 LLM、圖像模型、影片模型與後製工具可以獨立替換。
