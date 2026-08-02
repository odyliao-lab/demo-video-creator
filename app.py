"""Phase 1 Streamlit 操作介面。

流程：上傳影片 -> 權利聲明 -> 本機前處理 -> Gemini 抽象化分析
     -> Claude 產生三套企劃 -> 人工編輯/批准 -> 匯出 JSON/Markdown。

執行：streamlit run app.py
"""

import os
from pathlib import Path

import streamlit as st

from src import config, pipeline, store
from src.schemas import OriginalTreatment, Phase1Result, RightsDeclaration

st.set_page_config(page_title="Demo Video Creator — Phase 1", layout="wide")
st.title("🎬 Demo Video Creator — Phase 1：分析與企劃")

ss = st.session_state

# ---------- 側欄：環境狀態 ----------
with st.sidebar:
    st.header("環境")
    ok_ant = bool(os.getenv("ANTHROPIC_API_KEY"))
    ok_gem = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    st.write(("✅" if ok_ant else "❌") + " ANTHROPIC_API_KEY")
    st.write(("✅" if ok_gem else "❌") + " GEMINI_API_KEY")
    st.divider()
    st.caption(f"分析模型：`{config.ANALYZER_MODEL}`")
    st.caption(f"企劃模型：`{config.PLANNER_MODEL}`（失敗自動升級 `{config.PLANNER_ESCALATION_MODEL}`）")
    st.divider()
    runs = store.list_runs()
    if runs:
        st.caption(f"歷史紀錄：{len(runs)} 筆（見 workspace/outputs/）")

if not (ok_ant and ok_gem):
    st.warning("請先把 `.env.example` 複製為 `.env` 並填入 API keys，再重新整理頁面。")

# ---------- Step 1：來源與權利聲明 ----------
st.subheader("1️⃣ 來源影片與權利聲明")
uploaded = st.file_uploader("上傳參考影片（MP4）", type=["mp4", "mov", "mkv"])
rights_label = {
    RightsDeclaration.OWNED: "自有素材",
    RightsDeclaration.LICENSED: "已取得授權",
    RightsDeclaration.CC_OR_PUBLIC: "Creative Commons / 公版",
    RightsDeclaration.ABSTRACT_ONLY: "僅作抽象化分析（不沿用任何內容）",
}
rights = st.selectbox("來源權利聲明", list(rights_label), format_func=rights_label.get)
user_request = st.text_area(
    "創作需求（想加入或修改什麼？）",
    placeholder="例：建立完全虛構的『鋼角犀牛 vs 極光白熊』賽事 Highlight，賽博龐克視覺風格…",
    height=100,
)

if uploaded is not None:
    video_path = config.WORKSPACE_DIR / "sources" / uploaded.name
    video_path.parent.mkdir(parents=True, exist_ok=True)
    if not video_path.exists() or video_path.stat().st_size != uploaded.size:
        video_path.write_bytes(uploaded.getbuffer())
    ss["video_path"] = str(video_path)

# ---------- Step 2：本機前處理 ----------
st.subheader("2️⃣ 本機前處理（ffprobe + 鏡頭切割，不呼叫 API）")
if st.button("執行前處理", disabled="video_path" not in ss):
    with st.spinner("分析中…"):
        technical, scenes = pipeline.preprocess(ss["video_path"])
        ss["technical"], ss["scenes"] = technical, scenes

if "technical" in ss:
    t = ss["technical"]
    st.success(
        f"{t.width}x{t.height} @ {t.fps}fps ・ {t.duration_seconds:.1f}s ・ "
        f"codec {t.video_codec} ・ 共 {len(ss['scenes'])} 個鏡頭"
    )
    frame_paths = [s.frame_path for s in ss["scenes"] if s.frame_path]
    if frame_paths:
        with st.expander(f"代表影格（{len(frame_paths)} 張）"):
            cols = st.columns(6)
            for i, fp in enumerate(frame_paths):
                cols[i % 6].image(fp, caption=f"#{i}", use_container_width=True)

# ---------- Step 3：AI 分析與企劃 ----------
st.subheader("3️⃣ 抽象化分析 + 產生三套原創企劃")
if st.button("呼叫模型生成", disabled="scenes" not in ss or not (ok_ant and ok_gem)):
    with st.status("執行中…", expanded=True) as status:
        st.write(f"Gemini（{config.ANALYZER_MODEL}）分析影片…")
        abstraction = pipeline.analyze(ss["video_path"], ss["scenes"])
        ss["abstraction"] = abstraction
        st.write(f"Claude 產生企劃（預設 {config.PLANNER_MODEL}）…")
        treatment_set, model_used = pipeline.plan(abstraction, user_request)
        ss["treatment_set"], ss["planner_model_used"] = treatment_set, model_used
        status.update(label=f"完成（企劃模型：{model_used}）", state="complete")

if "abstraction" in ss:
    with st.expander("抽象化分析結果"):
        st.json(ss["abstraction"].model_dump())

# ---------- Step 4：人工審核與匯出 ----------
if "treatment_set" in ss:
    st.subheader("4️⃣ 人工審核 → 批准並匯出")
    ts = ss["treatment_set"]
    tabs = st.tabs([f"企劃 {i+1}：{tr.title}" for i, tr in enumerate(ts.treatments)])
    for i, (tab, tr) in enumerate(zip(tabs, ts.treatments)):
        with tab:
            st.markdown(f"**Logline：** {tr.logline}")
            st.markdown(f"**世界觀：** {tr.world_and_characters}")
            st.markdown(f"**視覺風格：** {tr.visual_style}")
            st.markdown(f"**敘事結構：** {tr.narrative_outline}")
            st.markdown("**全片禁止元素：** " + "、".join(tr.global_negative_constraints))
            st.caption(f"相似度風險備註：{tr.similarity_risk_notes}")
            st.dataframe(
                [{"#": s.shot_id, "秒數": s.duration_seconds, "鏡位": s.camera,
                  "動作": s.action, "Prompt": s.prompt} for s in tr.shots],
                use_container_width=True,
            )
            edited = st.text_area(
                "可直接編輯此企劃的 JSON 後再批准：",
                value=tr.model_dump_json(indent=2),
                height=300, key=f"edit_{i}",
            )
            if st.button(f"✅ 批准企劃 {i+1} 並匯出", key=f"approve_{i}"):
                try:
                    approved = OriginalTreatment.model_validate_json(edited)
                except Exception as e:
                    st.error(f"編輯後的 JSON 未通過驗證：{e}")
                else:
                    ts.treatments[i] = approved
                    result = Phase1Result(
                        source_path=ss["video_path"],
                        rights=rights,
                        user_request=user_request,
                        technical=ss["technical"],
                        scenes=ss["scenes"],
                        abstraction=ss["abstraction"],
                        treatment_set=ts,
                        analyzer_model=config.ANALYZER_MODEL,
                        planner_model_used=ss["planner_model_used"],
                    )
                    json_path, md_path, run_id = pipeline.export_result(result)
                    store.save_approval(run_id, approved.title, edited)
                    st.success(f"已匯出（run #{run_id}）：\n\n- `{json_path}`\n- `{md_path}`")
