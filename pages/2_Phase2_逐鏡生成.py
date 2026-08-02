"""Phase 2：逐鏡生成 PoC（Veo，付費 API）。

讀取 Phase 1 匯出的企劃 JSON -> 選擇企劃與鏡頭 -> 成本確認 -> 逐鏡生成
-> 每鏡記錄耗時/重試/失敗（文件第 12 章驗收指標）。
"""

import time
from pathlib import Path

import streamlit as st

from src import config, store
from src.providers.veo_provider import GeminiVeoProvider, _clamp_duration
from src.schemas import Phase1Result

st.set_page_config(page_title="Phase 2 — 逐鏡生成", layout="wide")
st.title("🎥 Phase 2：逐鏡生成 PoC（Veo）")

st.warning(
    "Veo 是**付費**功能（無免費層，按生成秒數計價）。"
    "本頁每次生成前都會顯示預估秒數，並需勾選確認。", icon="💰",
)

# ---------- 選擇 Phase 1 匯出 ----------
exports = sorted(config.OUTPUT_DIR.glob("run*.json"), reverse=True)
if not exports:
    st.info("還沒有 Phase 1 匯出。請先在主頁完成「批准並匯出」。")
    st.stop()

export_path = st.selectbox("選擇 Phase 1 匯出", exports, format_func=lambda p: p.name)
result = Phase1Result.model_validate_json(Path(export_path).read_text(encoding="utf-8"))

titles = [t.title for t in result.treatment_set.treatments]
t_idx = st.radio("選擇企劃", range(len(titles)), format_func=lambda i: titles[i],
                 horizontal=True)
treatment = result.treatment_set.treatments[t_idx]

st.dataframe(
    [{"#": s.shot_id, "企劃秒數": s.duration_seconds,
      "實際生成秒數": _clamp_duration(s.duration_seconds),
      "鏡位": s.camera, "動作": s.action} for s in treatment.shots],
    use_container_width=True,
)

# ---------- 選鏡與成本確認 ----------
shot_ids = [s.shot_id for s in treatment.shots]
default_ids = shot_ids[:3]
selected = st.multiselect(
    f"選擇要生成的鏡頭（單批上限 {config.MAX_SHOTS_PER_BATCH} 鏡，建議先 3 鏡試水溫）",
    shot_ids, default=default_ids,
)
if len(selected) > config.MAX_SHOTS_PER_BATCH:
    st.error(f"超過單批上限 {config.MAX_SHOTS_PER_BATCH} 鏡（.env 的 MAX_SHOTS_PER_BATCH 可調）")
    st.stop()

chosen = [s for s in treatment.shots if s.shot_id in selected]
total_seconds = sum(_clamp_duration(s.duration_seconds) for s in chosen)

if config.VIDEO_PRICE_PER_SECOND > 0:
    est = total_seconds * config.VIDEO_PRICE_PER_SECOND
    st.metric("本批預估", f"{total_seconds} 秒 ≈ ${est:.2f} USD")
else:
    st.metric("本批預估", f"{total_seconds} 秒")
    st.caption("尚未設定 VIDEO_PRICE_PER_SECOND，無法估算金額——請到 Gemini API 定價頁"
               "查 Veo 每秒單價後填入 .env。")

st.caption(f"生成模型：`{config.VIDEO_MODEL}` ・ 解析度：{config.VIDEO_RESOLUTION}"
           "（模型 id 可在 .env 的 VIDEO_MODEL 調整）")

confirmed = st.checkbox("我了解這會呼叫付費 API，確認生成上述鏡頭")
if st.button("🎬 開始生成", disabled=not (confirmed and chosen)):
    provider = GeminiVeoProvider()
    out_dir = config.SHOTS_DIR / Path(export_path).stem / f"t{t_idx+1}"
    results = []
    for shot in chosen:
        with st.status(f"鏡頭 {shot.shot_id} 生成中…", expanded=False) as status:
            out_path = out_dir / f"shot_{shot.shot_id:02d}.mp4"
            start = time.monotonic()
            attempts, error, ok = 0, None, False
            while attempts < 2 and not ok:
                attempts += 1
                try:
                    provider.generate_shot(shot, treatment.global_negative_constraints,
                                           out_path)
                    ok = True
                except Exception as e:  # 記錄失敗原因，重試一次
                    error = str(e)
                    status.write(f"第 {attempts} 次嘗試失敗：{error}")
            elapsed = time.monotonic() - start

            store.save_generation_job(
                source_export=str(export_path), treatment_title=treatment.title,
                shot_id=shot.shot_id, model=config.VIDEO_MODEL,
                status="succeeded" if ok else "failed",
                video_path=str(out_path) if ok else None,
                duration_seconds=_clamp_duration(shot.duration_seconds),
                elapsed_seconds=round(elapsed, 1), attempts=attempts,
                error=None if ok else error,
            )
            results.append({"#": shot.shot_id, "狀態": "✅" if ok else "❌",
                            "耗時(s)": round(elapsed, 1), "嘗試": attempts,
                            "錯誤": error or ""})
            if ok:
                status.update(label=f"鏡頭 {shot.shot_id} 完成（{elapsed:.0f}s）",
                              state="complete")
                st.video(str(out_path))
            else:
                status.update(label=f"鏡頭 {shot.shot_id} 失敗", state="error")
                if error and ("not found" in error.lower() or "permission" in error.lower()):
                    try:
                        st.info("帳號可用的 Veo 模型：" +
                                "、".join(provider.list_video_models() or ["（無）"]))
                    except Exception:
                        pass

    st.subheader("本批結果（已寫入 workspace/phase1.db 的 generation_jobs）")
    st.dataframe(results, use_container_width=True)
    st.caption(f"影片輸出目錄：`{out_dir}`")
