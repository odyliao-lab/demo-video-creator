"""本機影片前處理：ffprobe 技術資料、PySceneDetect 鏡頭切割、代表影格擷取。"""

import json
import subprocess
from pathlib import Path

import cv2
from scenedetect import ContentDetector, detect

from .schemas import SceneObservation, TechnicalMetadata


def probe(video_path: str | Path) -> TechnicalMetadata:
    """用 ffprobe 讀取來源影片的技術資料。"""
    cmd = [
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(video_path),
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    data = json.loads(out)

    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)

    num, _, den = video.get("avg_frame_rate", "0/1").partition("/")
    fps = (float(num) / float(den)) if den and float(den) else 0.0

    fmt = data["format"]
    return TechnicalMetadata(
        container=fmt.get("format_name", "unknown"),
        video_codec=video.get("codec_name", "unknown"),
        width=int(video["width"]),
        height=int(video["height"]),
        fps=round(fps, 3),
        duration_seconds=float(fmt.get("duration", 0)),
        video_bitrate=int(fmt["bit_rate"]) if fmt.get("bit_rate") else None,
        audio_codec=audio.get("codec_name") if audio else None,
    )


def detect_scenes(video_path: str | Path, frames_dir: Path) -> list[SceneObservation]:
    """PySceneDetect 切割鏡頭，並用 OpenCV 擷取每個鏡頭中點的代表影格。

    高速剪接的體育影片是文件特別點名要用本機切割補強的場景，
    避免雲端模型低取樣率漏掉快速剪接。
    """
    frames_dir.mkdir(parents=True, exist_ok=True)
    scene_list = detect(str(video_path), ContentDetector())

    cap = cv2.VideoCapture(str(video_path))
    observations: list[SceneObservation] = []
    try:
        for i, (start, end) in enumerate(scene_list):
            start_s, end_s = start.get_seconds(), end.get_seconds()
            mid_s = (start_s + end_s) / 2
            cap.set(cv2.CAP_PROP_POS_MSEC, mid_s * 1000)
            ok, frame = cap.read()
            frame_path = None
            if ok:
                frame_path = str(frames_dir / f"scene_{i:04d}.jpg")
                cv2.imwrite(frame_path, frame)
            observations.append(SceneObservation(
                index=i,
                start_seconds=round(start_s, 3),
                end_seconds=round(end_s, 3),
                frame_path=frame_path,
            ))
    finally:
        cap.release()

    # 沒有剪接點的短片：整片視為單一場景
    if not observations:
        meta_duration = probe(video_path).duration_seconds
        observations.append(SceneObservation(index=0, start_seconds=0.0,
                                             end_seconds=meta_duration))
    return observations
