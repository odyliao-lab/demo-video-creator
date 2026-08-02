"""Phase 1 資料結構（對應交接文件 7.3 節的子集）。

所有跨模型傳遞的資料都經過這些 Pydantic schema 驗證，
確保「分析 -> 企劃 -> 匯出」每一步都是結構化、可追溯的。
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RightsDeclaration(str, Enum):
    """來源權利聲明（文件 4 節關卡 1）。"""

    OWNED = "owned"                # 自有素材
    LICENSED = "licensed"          # 已取得授權
    CC_OR_PUBLIC = "cc_or_public"  # Creative Commons / 公版
    ABSTRACT_ONLY = "abstract_only"  # 僅作抽象化分析，不沿用任何內容


class TechnicalMetadata(BaseModel):
    """ffprobe 讀出的來源影片技術資料。"""

    container: str
    video_codec: str
    width: int
    height: int
    fps: float
    duration_seconds: float
    video_bitrate: Optional[int] = None
    audio_codec: Optional[str] = None


class SceneObservation(BaseModel):
    """PySceneDetect 切出的單一鏡頭與其代表影格。"""

    index: int
    start_seconds: float
    end_seconds: float
    frame_path: Optional[str] = None


# ---------- 影片理解（Gemini）輸出 ----------

class ReferenceAbstraction(BaseModel):
    """對參考影片的抽象化理解——只保留不受保護的概念層資訊。"""

    subject_summary: str = Field(description="影片主題與事實層面的摘要")
    genre_conventions: list[str] = Field(description="此類型影片的一般製作慣例（如高位廣角追球、慢動作重播）")
    cinematography_language: list[str] = Field(description="一般性攝影語言描述，不含逐鏡對應")
    pacing_notes: str = Field(description="整體節奏的抽象描述（不含逐秒剪輯點）")
    audio_style: str = Field(description="旁白/音樂/音效的風格類型描述")
    protected_elements_observed: list[str] = Field(
        description="影片中觀察到「不得沿用」的受保護元素（品牌、隊徽、真實人物、招牌台詞等），供後續列入禁止清單"
    )


# ---------- 企劃/分鏡（Claude）輸出 ----------

class ShotPrompt(BaseModel):
    """單一鏡頭的生成提示詞（Phase 2 之後餵給影片模型）。"""

    shot_id: int
    duration_seconds: float = Field(description="建議 5 秒以內")
    camera: str = Field(description="鏡位與運鏡，例如：場邊低角度、緩慢推軌")
    action: str = Field(description="畫面中發生的事")
    prompt: str = Field(description="給影片生成模型的完整英文提示詞")
    negative_constraints: list[str] = Field(description="此鏡禁止出現的元素")


class OriginalTreatment(BaseModel):
    """一套原創企劃。"""

    title: str
    logline: str = Field(description="一句話故事概念")
    world_and_characters: str = Field(description="完全虛構的世界觀、隊伍、角色設定")
    visual_style: str
    narrative_outline: str = Field(description="敘事結構，需與參考影片的事件順序明顯不同")
    shots: list[ShotPrompt]
    global_negative_constraints: list[str] = Field(
        description="全片禁止元素：真實品牌/球隊/球員/Logo/招牌台詞等"
    )
    similarity_risk_notes: str = Field(
        description="自我檢查：此企劃與參考影片可能過度對應之處與已採取的差異化措施（僅供風險提示）"
    )


class TreatmentSet(BaseModel):
    """Claude 一次產出的三套差異明顯的企劃。"""

    source_abstraction_ack: str = Field(
        description="確認僅使用了抽象層資訊，未複製受保護元素的簡短聲明"
    )
    treatments: list[OriginalTreatment] = Field(description="三套差異明顯的企劃")


# ---------- 整體 Phase 1 產出 ----------

class Phase1Result(BaseModel):
    source_path: str
    rights: RightsDeclaration
    user_request: str
    technical: TechnicalMetadata
    scenes: list[SceneObservation]
    abstraction: ReferenceAbstraction
    treatment_set: TreatmentSet
    analyzer_model: str
    planner_model_used: str
