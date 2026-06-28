from typing import List, Dict, Any
from .base_tier import BaseTierEvaluator
from .patterns import UnitTestPattern, E2eTrajectoryPattern

class DraftOnlyAgentEvaluator(BaseTierEvaluator):
    def __init__(self, agent_name: str, agent_path: str, eval_cases: List[Dict[str, Any]], metadata: Dict[str, Any], target_tier: str):
        super().__init__(agent_name, agent_path, eval_cases, metadata, target_tier)
        self.patterns = [
            UnitTestPattern(),
            E2eTrajectoryPattern()
        ]

class ReadOnlyAgentEvaluator(BaseTierEvaluator):
    def __init__(self, agent_name: str, agent_path: str, eval_cases: List[Dict[str, Any]], metadata: Dict[str, Any], target_tier: str):
        super().__init__(agent_name, agent_path, eval_cases, metadata, target_tier)
        self.patterns = [
            UnitTestPattern(),
            E2eTrajectoryPattern()
        ]

class ActionAllowedAgentEvaluator(BaseTierEvaluator):
    def __init__(self, agent_name: str, agent_path: str, eval_cases: List[Dict[str, Any]], metadata: Dict[str, Any], target_tier: str):
        super().__init__(agent_name, agent_path, eval_cases, metadata, target_tier)
        self.patterns = [
            UnitTestPattern(),
            E2eTrajectoryPattern()
        ]

# Factory mapping target_tier to appropriate Evaluator Subclass
TIER_EVALUATORS = {
    "read_only": ReadOnlyAgentEvaluator,
    "draft_only": DraftOnlyAgentEvaluator,
    "action_allowed": ActionAllowedAgentEvaluator
}
