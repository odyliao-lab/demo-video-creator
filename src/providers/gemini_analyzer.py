"""GeminiVideoAnalyzer：用 Gemini API（原生影片輸入）做抽象化影片理解。

取代交接文件中的 BedrockNovaVideoAnalyzer。Gemini API 有免費層，
且能直接吃整支影片檔，不需自行抽影格上傳。
"""

import time
from pathlib import Path

from google import genai

from .. import config
from ..schemas import ReferenceAbstraction, SceneObservation
from .base import AnalysisProvider

ANALYSIS_PROMPT = """\
你是影片分析助手。請對這支參考影片做「抽象化」分析，目的是之後產生完全原創的新作品。

規則：
1. 只萃取不受著作權保護的層面：主題事實、類型慣例、一般攝影語言、節奏風格。
2. 不要輸出逐鏡的鏡頭順序、精確剪輯點、可對應複製的細節。
3. 把影片中觀察到的受保護元素（品牌、隊徽、真實人物/球隊、招牌台詞、轉播包裝）\
列進 protected_elements_observed，供後續列為禁止沿用清單。

輔助資訊：本機鏡頭切割結果顯示此影片共有 {scene_count} 個鏡頭，\
平均鏡頭長度約 {avg_shot:.1f} 秒（僅供節奏描述參考，請勿逐鏡對應）。
"""


class GeminiVideoAnalyzer(AnalysisProvider):
    def __init__(self, model: str = config.ANALYZER_MODEL):
        self.model = model
        self.client = genai.Client()  # 讀 GEMINI_API_KEY

    def analyze_video(self, video_path: str | Path,
                      scenes: list[SceneObservation]) -> ReferenceAbstraction:
        video_file = self.client.files.upload(file=str(video_path))
        # 影片上傳後需等待伺服器端處理完成
        while video_file.state and video_file.state.name == "PROCESSING":
            time.sleep(3)
            video_file = self.client.files.get(name=video_file.name)
        if video_file.state and video_file.state.name == "FAILED":
            raise RuntimeError(f"Gemini 影片處理失敗: {video_file.name}")

        durations = [s.end_seconds - s.start_seconds for s in scenes]
        prompt = ANALYSIS_PROMPT.format(
            scene_count=len(scenes),
            avg_shot=(sum(durations) / len(durations)) if durations else 0.0,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=[video_file, prompt],
            config={
                "response_mime_type": "application/json",
                "response_schema": ReferenceAbstraction,
            },
        )
        parsed = response.parsed
        if isinstance(parsed, ReferenceAbstraction):
            return parsed
        # response_schema 未回傳物件時，退回手動驗證 JSON 文字
        return ReferenceAbstraction.model_validate_json(response.text)
