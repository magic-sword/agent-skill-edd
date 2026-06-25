from typing import List, Dict, Any
from .base_tier import BaseTierEvaluator
from .patterns import UnitTestPattern, E2eTrajectoryPattern

class DraftOnlyWorkflowEvaluator(BaseTierEvaluator):
    def __init__(self, workflow_name: str, workflow_path: str, eval_cases: List[Dict[str, Any]], metadata: Dict[str, Any], target_tier: str):
        super().__init__(workflow_name, workflow_path, eval_cases, metadata, target_tier)
        self.patterns = [
            UnitTestPattern(),
            E2eTrajectoryPattern()
        ]

class ReadOnlyWorkflowEvaluator(BaseTierEvaluator):
    def __init__(self, workflow_name: str, workflow_path: str, eval_cases: List[Dict[str, Any]], metadata: Dict[str, Any], target_tier: str):
        super().__init__(workflow_name, workflow_path, eval_cases, metadata, target_tier)
        self.patterns = [
            UnitTestPattern(),
            E2eTrajectoryPattern()
        ]

class ActionAllowedWorkflowEvaluator(BaseTierEvaluator):
    def __init__(self, workflow_name: str, workflow_path: str, eval_cases: List[Dict[str, Any]], metadata: Dict[str, Any], target_tier: str):
        super().__init__(workflow_name, workflow_path, eval_cases, metadata, target_tier)
        self.patterns = [
            UnitTestPattern(),
            E2eTrajectoryPattern()
        ]

# Factory mapping target_tier to appropriate Evaluator Subclass
TIER_EVALUATORS = {
    "read_only": ReadOnlyWorkflowEvaluator,
    "draft_only": DraftOnlyWorkflowEvaluator,
    "action_allowed": ActionAllowedWorkflowEvaluator
}
