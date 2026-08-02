"""GeminiVeoProvider：用 Veo（Gemini API）逐鏡生成短影片。

注意：Veo 是付費功能、無免費層，按生成秒數計價。
呼叫端（Streamlit Phase 2 頁）在生成前必須經過成本確認。
"""

import time
from pathlib import Path

from google import genai

from .. import config
from ..schemas import ShotPrompt
from .base import VideoProvider

# Veo 支援的單鏡長度（秒）；企劃的 duration 會被收斂到最接近的值
_SUPPORTED_DURATIONS = (4, 6, 8)
_POLL_INTERVAL_S = 10
_TIMEOUT_S = 15 * 60


def _clamp_duration(seconds: float) -> int:
    return min(_SUPPORTED_DURATIONS, key=lambda d: abs(d - seconds))


class GeminiVeoProvider(VideoProvider):
    def __init__(self, model: str = config.VIDEO_MODEL):
        self.model = model
        self.client = genai.Client()  # 讀 GEMINI_API_KEY

    def clamp_duration(self, seconds: float) -> int:
        return _clamp_duration(seconds)

    def generate_shot(self, shot: ShotPrompt, extra_negative: list[str],
                      out_path: Path) -> Path:
        negative = "; ".join(dict.fromkeys(shot.negative_constraints + extra_negative))
        operation = self.client.models.generate_videos(
            model=self.model,
            prompt=shot.prompt,
            config={
                "aspect_ratio": "16:9",
                "resolution": config.VIDEO_RESOLUTION,
                "duration_seconds": _clamp_duration(shot.duration_seconds),
                "negative_prompt": negative or None,
            },
        )

        deadline = time.monotonic() + _TIMEOUT_S
        while not operation.done:
            if time.monotonic() > deadline:
                raise TimeoutError(f"鏡頭 {shot.shot_id} 生成逾時（>{_TIMEOUT_S}s）")
            time.sleep(_POLL_INTERVAL_S)
            operation = self.client.operations.get(operation)

        if operation.error:
            raise RuntimeError(f"鏡頭 {shot.shot_id} 生成失敗：{operation.error}")

        videos = operation.response.generated_videos
        if not videos:
            raise RuntimeError(f"鏡頭 {shot.shot_id}：API 未回傳影片（可能被安全過濾）")

        video = videos[0]
        self.client.files.download(file=video.video)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        video.video.save(str(out_path))
        return out_path

    def list_video_models(self) -> list[str]:
        """列出帳號可用、名稱含 veo 的模型 id（VIDEO_MODEL 設錯時用來排查）。"""
        return [m.name for m in self.client.models.list() if "veo" in (m.name or "").lower()]
