"""Provider 抽象層（文件 7.2 節）：模型可獨立替換，不綁死單一供應商。"""

from abc import ABC, abstractmethod
from pathlib import Path

from ..schemas import (
    ReferenceAbstraction,
    SceneObservation,
    ShotPrompt,
    TreatmentSet,
)


class AnalysisProvider(ABC):
    """影片理解：輸入影片 -> 抽象化分析。"""

    @abstractmethod
    def analyze_video(self, video_path: str | Path,
                      scenes: list[SceneObservation]) -> ReferenceAbstraction: ...


class PlanningProvider(ABC):
    """企劃生成：抽象化分析 + 使用者需求 -> 三套原創企劃與分鏡。

    回傳 (TreatmentSet, 實際使用的模型 id)。
    """

    @abstractmethod
    def create_treatments(self, abstraction: ReferenceAbstraction,
                          user_request: str) -> tuple[TreatmentSet, str]: ...


class VideoProvider(ABC):
    """影片生成（Phase 2）：單鏡提示詞 -> 影片檔。付費 API，呼叫端需自行做成本護欄。"""

    @abstractmethod
    def generate_shot(self, shot: ShotPrompt, extra_negative: list[str],
                      out_path: Path) -> Path:
        """生成單一鏡頭並存到 out_path，回傳實際檔案路徑。失敗時 raise。"""
        ...
