"""ClaudePlanner：用 Anthropic API 產生三套原創企劃與逐鏡提示詞。

模型策略：預設 claude-sonnet-5（Phase 1 的結構化企劃工作已足夠、成本約為
Opus 的四成）。若輸出無法通過 schema 驗證或被安全機制拒絕，
自動升級到 claude-opus-5 重試一次（可用 .env 調整兩者）。
"""

import anthropic

from .. import config
from ..schemas import ReferenceAbstraction, TreatmentSet
from .base import PlanningProvider

SYSTEM_PROMPT = """\
你是影片企劃總監。你的工作是根據「參考影片的抽象化分析」與使用者的創作需求，\
產生三套差異明顯、完全原創的影片企劃與逐鏡提示詞。

必須遵守的原創性規則：
- 只能參考類型慣例與一般攝影語言，主動改變敘事順序、角色、場景、事件與聲音設計。
- 所有隊伍、角色、球場、隊徽、比分、轉播包裝都必須完全虛構，\
不得使用任何真實品牌、聯賽、球隊、球員或贊助商。
- 分析中列出的 protected_elements_observed 一律列入全片禁止元素。
- 每套企劃的 similarity_risk_notes 誠實記錄可能與參考影片過度對應之處；\
這只是風險提示，不得宣稱法律安全。
- 每鏡 prompt 用英文撰寫（影片生成模型的慣用語言），其餘欄位用繁體中文。
- 單鏡長度以 5 秒為上限（對齊主流影片生成模型的限制）。
"""

USER_TEMPLATE = """\
## 參考影片抽象化分析
{abstraction_json}

## 使用者創作需求
{user_request}

請產出三套差異明顯的原創企劃（TreatmentSet）。
"""


class ClaudePlanner(PlanningProvider):
    def __init__(self, model: str = config.PLANNER_MODEL,
                 escalation_model: str = config.PLANNER_ESCALATION_MODEL):
        self.model = model
        self.escalation_model = escalation_model
        self.client = anthropic.Anthropic()  # 讀 ANTHROPIC_API_KEY

    def create_treatments(self, abstraction: ReferenceAbstraction,
                          user_request: str) -> tuple[TreatmentSet, str]:
        user_msg = USER_TEMPLATE.format(
            abstraction_json=abstraction.model_dump_json(indent=2),
            user_request=user_request.strip() or "（未指定，請自由發揮但遵守原創性規則）",
        )

        errors: list[str] = []
        # dict.fromkeys 去重：兩個設定指到同一模型時只跑一次
        for model in dict.fromkeys([self.model, self.escalation_model]):
            try:
                response = self.client.messages.parse(
                    model=model,
                    max_tokens=16000,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_msg}],
                    output_format=TreatmentSet,
                )
            except anthropic.APIStatusError as e:
                errors.append(f"{model}: API error {e.status_code} {e.message}")
                continue

            if response.stop_reason == "refusal":
                errors.append(f"{model}: 請求被安全機制拒絕")
                continue
            if response.stop_reason == "max_tokens":
                errors.append(f"{model}: 輸出超過 max_tokens 被截斷")
                continue
            if response.parsed_output is None:
                errors.append(f"{model}: 輸出未通過 schema 驗證")
                continue

            return response.parsed_output, model

        raise RuntimeError("所有企劃模型都失敗：\n" + "\n".join(errors))
