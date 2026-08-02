"""Phase 1 流程編排：前處理 -> 影片理解 -> 企劃生成 -> 匯出。"""

import json
from datetime import datetime
from pathlib import Path

from . import config, ingest, store
from .providers.claude_planner import ClaudePlanner
from .providers.gemini_analyzer import GeminiVideoAnalyzer
from .schemas import (
    OriginalTreatment,
    Phase1Result,
    ReferenceAbstraction,
    RightsDeclaration,
    SceneObservation,
    TechnicalMetadata,
)


def preprocess(video_path: str | Path) -> tuple[TechnicalMetadata, list[SceneObservation]]:
    """本機前處理（不呼叫任何 API）。"""
    video_path = Path(video_path)
    technical = ingest.probe(video_path)
    frames_dir = config.FRAMES_DIR / video_path.stem
    scenes = ingest.detect_scenes(video_path, frames_dir)
    return technical, scenes


def analyze(video_path: str | Path,
            scenes: list[SceneObservation]) -> ReferenceAbstraction:
    return GeminiVideoAnalyzer().analyze_video(video_path, scenes)


def plan(abstraction: ReferenceAbstraction, user_request: str):
    return ClaudePlanner().create_treatments(abstraction, user_request)


def export_result(result: Phase1Result) -> tuple[Path, Path, int]:
    """匯出完整企劃 JSON 與 Markdown，並寫入 SQLite。回傳 (json路徑, md路徑, run_id)。"""
    run_id = store.save_run(result)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = config.OUTPUT_DIR / f"run{run_id}_{stamp}"

    json_path = base.with_suffix(".json")
    json_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    md_path = base.with_suffix(".md")
    md_path.write_text(_to_markdown(result), encoding="utf-8")
    return json_path, md_path, run_id


def _to_markdown(result: Phase1Result) -> str:
    t = result.technical
    lines = [
        "# 影片企劃（Phase 1 產出）",
        "",
        f"- 來源：`{result.source_path}`",
        f"- 權利聲明：{result.rights.value}",
        f"- 分析模型：{result.analyzer_model}／企劃模型：{result.planner_model_used}",
        f"- 來源規格：{t.width}x{t.height} @ {t.fps}fps，{t.duration_seconds:.1f}s，"
        f"{len(result.scenes)} 個鏡頭",
        "",
        "## 參考影片抽象化分析",
        "",
        result.abstraction.subject_summary,
        "",
        "**類型慣例：** " + "、".join(result.abstraction.genre_conventions),
        "",
        "**禁止沿用的受保護元素：** " + "、".join(
            result.abstraction.protected_elements_observed or ["（無）"]),
        "",
    ]
    for i, tr in enumerate(result.treatment_set.treatments, 1):
        lines += [
            f"## 企劃 {i}：{tr.title}",
            "",
            f"> {tr.logline}",
            "",
            f"**世界觀與角色：** {tr.world_and_characters}",
            "",
            f"**視覺風格：** {tr.visual_style}",
            "",
            f"**敘事結構：** {tr.narrative_outline}",
            "",
            f"**全片禁止元素：** {'、'.join(tr.global_negative_constraints)}",
            "",
            "### 分鏡",
            "",
            "| # | 秒數 | 鏡位 | 動作 | Prompt |",
            "|---|------|------|------|--------|",
        ]
        for s in tr.shots:
            prompt_cell = s.prompt.replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| {s.shot_id} | {s.duration_seconds} | {s.camera} | {s.action} "
                f"| {prompt_cell} |")
        lines += ["", f"**相似度風險備註：** {tr.similarity_risk_notes}", ""]
    return "\n".join(lines)
