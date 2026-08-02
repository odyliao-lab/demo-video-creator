"""集中設定：模型選擇與路徑。全部可用環境變數（.env）覆寫。"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 固定讀專案根目錄的 .env，與啟動時的工作目錄無關
load_dotenv(PROJECT_ROOT / ".env")

# 影片理解（多模態、原生影片輸入）
ANALYZER_MODEL = os.getenv("ANALYZER_MODEL", "gemini-2.5-flash")

# 企劃/分鏡生成：預設 Sonnet 5（Phase 1 的結構化企劃工作已足夠）。
# 驗證失敗或被拒絕時自動升級到 escalation model 重試一次。
PLANNER_MODEL = os.getenv("PLANNER_MODEL", "claude-sonnet-5")
PLANNER_ESCALATION_MODEL = os.getenv("PLANNER_ESCALATION_MODEL", "claude-opus-5")

WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", PROJECT_ROOT / "workspace"))
FRAMES_DIR = WORKSPACE_DIR / "frames"
OUTPUT_DIR = WORKSPACE_DIR / "outputs"
DB_PATH = WORKSPACE_DIR / "phase1.db"

for _d in (WORKSPACE_DIR, FRAMES_DIR, OUTPUT_DIR):
    _d.mkdir(parents=True, exist_ok=True)
