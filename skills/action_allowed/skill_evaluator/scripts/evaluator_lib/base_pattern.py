from typing import Tuple, List, Any

class BaseEvaluationPattern:
    def __init__(self, name: str):
        self.name = name

    def evaluate(self, context: Any) -> Tuple[bool, List[str]]:
        """
        Runs the evaluation pattern using the provided context (Evaluator instance).
        Returns a tuple of (success, issues_or_warnings).
        """
        raise NotImplementedError
