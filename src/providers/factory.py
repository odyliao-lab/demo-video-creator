"""依 .env 的 VIDEO_PROVIDER 選擇影片生成供應商。"""

from .. import config
from .base import VideoProvider


def get_video_provider() -> VideoProvider:
    if config.VIDEO_PROVIDER == "fal":
        from .fal_provider import FalVideoProvider
        return FalVideoProvider()
    if config.VIDEO_PROVIDER == "veo":
        from .veo_provider import GeminiVeoProvider
        return GeminiVeoProvider()
    raise ValueError(
        f"未知的 VIDEO_PROVIDER: {config.VIDEO_PROVIDER}（支援 fal / veo）")
