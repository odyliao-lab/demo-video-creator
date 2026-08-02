"""FalVideoProvider：透過 fal.ai 聚合平台生成影片（Seedance / Kling 等）。

fal.ai 一個帳號可調用多家模型，價格約為 Veo 的 1/10 ~ 1/30：
- bytedance/seedance-2.0/fast/text-to-video   （最便宜，~$0.02/s 量級）
- bytedance/seedance-2.0/text-to-video        （Seedance 標準版）
- fal-ai/kling-video/v3/standard/text-to-video（Kling 3.0）
- fal-ai/kling-video/v3/pro/text-to-video     （Kling 3.0 Pro）

認證：環境變數 FAL_KEY（.env 已由 config 載入）。
"""

import urllib.request
from pathlib import Path

import fal_client

from .. import config
from ..schemas import ShotPrompt
from .base import VideoProvider


class FalVideoProvider(VideoProvider):
    def __init__(self, model: str = config.FAL_MODEL):
        self.model = model

    def clamp_duration(self, seconds: float) -> int:
        # Seedance/Kling 的 text-to-video 常見支援 5 或 10 秒
        return 5 if seconds <= 7 else 10

    def _build_arguments(self, shot: ShotPrompt, negative: str) -> dict:
        duration = self.clamp_duration(shot.duration_seconds)
        model = self.model.lower()
        if "kling" in model:
            args = {
                "prompt": shot.prompt,
                "duration": str(duration),      # Kling 用字串 "5"/"10"
                "aspect_ratio": "16:9",
            }
            if negative:
                args["negative_prompt"] = negative
            return args
        if "seedance" in model:
            return {
                "prompt": shot.prompt,
                "duration": duration,
                "aspect_ratio": "16:9",
                "resolution": config.VIDEO_RESOLUTION,
            }
        # 其他模型：只送最通用的欄位，細節交給 fal 端驗證
        return {"prompt": shot.prompt, "aspect_ratio": "16:9"}

    def generate_shot(self, shot: ShotPrompt, extra_negative: list[str],
                      out_path: Path) -> Path:
        negative = "; ".join(dict.fromkeys(shot.negative_constraints + extra_negative))
        result = fal_client.subscribe(
            self.model,
            arguments=self._build_arguments(shot, negative),
        )

        video_url = (result or {}).get("video", {}).get("url")
        if not video_url:
            raise RuntimeError(
                f"鏡頭 {shot.shot_id}：fal 未回傳影片 URL（回應：{result}）")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(video_url, out_path)
        return out_path
