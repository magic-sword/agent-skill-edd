from typing import List, Dict, Any
from .base_pattern import BaseEvaluationPattern

class BaseTierEvaluator:
    """
    Context for executing evaluation patterns. Specifies the executing tier.
    """
    def __init__(self, skill_name: str, skill_path: str, eval_cases: List[Dict[str, Any]], metadata: Dict[str, Any]):
        self.skill_name = skill_name
        self.skill_path = skill_path
        self.eval_cases = eval_cases
        self.metadata = metadata
        self.patterns: List[BaseEvaluationPattern] = []

    def evaluate_all(self) -> bool:
        results = {}
        for pattern in self.patterns:
            passed, issues = pattern.evaluate(self)
            results[pattern.name] = (passed, issues)
            
        print("\n=== Evaluation Summary (ADK v2.3.0 Strategy-based) ===")
        all_passed = True
        
        for pattern_name, (passed, issues) in results.items():
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  - {pattern_name}: {status}")
            if issues:
                for issue in issues:
                    print(f"    * [DETAILS] {issue}")
            if not passed:
                all_passed = False
                
        return all_passed
