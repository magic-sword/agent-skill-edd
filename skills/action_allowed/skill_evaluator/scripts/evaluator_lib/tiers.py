from typing import List, Dict, Any
from .base_tier import BaseTierEvaluator
from .patterns import (
    UnitTestPattern,
    GoldenDatasetPattern,
    LlmAsJudgePattern,
    AdversarialPattern,
    CanaryPattern
)

class ReadOnlyTierEvaluator(BaseTierEvaluator):
    def __init__(self, skill_name: str, skill_path: str, eval_cases: List[Dict[str, Any]], metadata: Dict[str, Any]):
        super().__init__(skill_name, skill_path, eval_cases, metadata)
        self.patterns = [
            UnitTestPattern(),
            LlmAsJudgePattern()
        ]


class DraftOnlyTierEvaluator(BaseTierEvaluator):
    def __init__(self, skill_name: str, skill_path: str, eval_cases: List[Dict[str, Any]], metadata: Dict[str, Any]):
        super().__init__(skill_name, skill_path, eval_cases, metadata)
        self.patterns = [
            UnitTestPattern(),
            GoldenDatasetPattern(),
            LlmAsJudgePattern()
        ]


class ActionAllowedTierEvaluator(BaseTierEvaluator):
    def __init__(self, skill_name: str, skill_path: str, eval_cases: List[Dict[str, Any]], metadata: Dict[str, Any]):
        super().__init__(skill_name, skill_path, eval_cases, metadata)
        self.patterns = [
            UnitTestPattern(),
            GoldenDatasetPattern(),
            LlmAsJudgePattern(),
            AdversarialPattern(),
            CanaryPattern()
        ]


# Factory mapping target_tier to appropriate Evaluator Subclass
TIER_EVALUATORS = {
    "read_only": ReadOnlyTierEvaluator,
    "draft_only": DraftOnlyTierEvaluator,
    "action_allowed": ActionAllowedTierEvaluator
}
