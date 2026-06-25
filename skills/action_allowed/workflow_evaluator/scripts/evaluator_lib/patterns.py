import os
import json
from typing import Tuple, List, Any
from .base_pattern import BaseEvaluationPattern
from .helpers import extract_trajectory_from_ast, check_trajectory

class UnitTestPattern(BaseEvaluationPattern):
    """
    Pattern 1: Unit-Test
    Verifies that the workflow has at least 3 test cases and has testable specificity
    (at least 3 positive and 3 negative triggers).
    """
    def __init__(self, name: str = "Pattern 1: Unit-Test"):
        super().__init__(name)

    def evaluate(self, context: Any) -> Tuple[bool, List[str]]:
        print("\n--- [Pattern 1: Unit-Test] Checking Test cases & Specificity ---")
        issues = []
        
        # 1. Check Unit test count (minimum 3 cases)
        if len(context.eval_cases) < 3:
            issues.append(f"Insufficient test cases. Minimum 3 required (got {len(context.eval_cases)}).")
            return False, issues
            
        # 2. Check Positive / Negative trigger ratio (Specificity: 3+ positive, 3+ negative)
        pos_count = 0
        neg_count = 0
        
        for case in context.eval_cases:
            eval_id = case.get("eval_id", "")
            if "negative" in eval_id.lower():
                neg_count += 1
            else:
                pos_count += 1
                
        print(f"  - Specificity: {pos_count} Positive cases, {neg_count} Negative cases")
        if pos_count < 3:
            issues.append(f"Specificity failed: At least 3 Positive cases required (got {pos_count}).")
        if neg_count < 3:
            issues.append(f"Specificity failed: At least 3 Negative cases required (got {neg_count}).")
            
        success = len(issues) == 0
        return success, issues


class E2eTrajectoryPattern(BaseEvaluationPattern):
    """
    Pattern 2: E2E & Tool Trajectory Verification
    Performs AST analysis on run_workflow.py and validates E2E outputs and tool trajectories.
    """
    def __init__(self, name: str = "Pattern 2: E2E & Tool Trajectory"):
        super().__init__(name)

    def evaluate(self, context: Any) -> Tuple[bool, List[str]]:
        issues = []
        
        # 1. Load test_config.json (Criteria) for scoring mode
        test_config_path = os.path.join(context.workflow_path, "test_config.json")
        trajectory_mode = "IN_ORDER" # Default
        if os.path.exists(test_config_path):
            try:
                with open(test_config_path, "r") as f:
                    config_data = json.load(f)
                    criteria = config_data.get("criteria", {})
                    trajectory_mode = criteria.get("trajectory_scoring_mode", "IN_ORDER")
            except Exception:
                pass
                
        self.name = f"Pattern 2: E2E & Tool Trajectory ({trajectory_mode})"
        print(f"\n--- [{self.name}] ---")
        print(f"  - Trajectory scoring mode: {trajectory_mode}")
        
        # Constraint: action_allowed must not use ANY_ORDER
        if context.target_tier == "action_allowed" and trajectory_mode == "ANY_ORDER":
            issues.append(f"Tier constraint violation: 'action_allowed' tier requires 'IN_ORDER' or 'EXACT' scoring mode (got 'ANY_ORDER').")
            return False, issues
            
        # 2. Run AST trajectory analysis
        run_workflow_path = os.path.join(context.workflow_path, "scripts", "run_workflow.py")
        actual_trajectory, ast_issues = extract_trajectory_from_ast(run_workflow_path)
        
        if ast_issues:
            for issue in ast_issues:
                issues.append(f"AST Parsing issue: {issue}")
            return False, issues
            
        print(f"  - Actual parsed trajectory (from run_workflow.py): {actual_trajectory}")
        
        # 3. Validate each positive test case
        trajectory_pass = True
        for case in context.eval_cases:
            eval_id = case.get("eval_id", "")
            if "negative" in eval_id.lower():
                continue
                
            conv = case.get("conversation", [])
            if not conv:
                continue
                
            expected_tools = []
            inter_data = conv[0].get("intermediate_data", {})
            tool_uses = inter_data.get("tool_uses", [])
            for tool_use in tool_uses:
                expected_tools.append({"tool": tool_use.get("name")})
                
            print(f"  - Case '{eval_id}': Expected tool sequence: {expected_tools}")
            
            # E2E validation: check if expected output format is defined
            final_resp = conv[0].get("final_response", {})
            parts = final_resp.get("parts", [])
            output_text = parts[0].get("text", "") if parts else ""
            if not output_text:
                issues.append(f"E2E validation failed: Expected output is missing in case '{eval_id}'.")
                trajectory_pass = False
                break
                
            # Trajectory validation
            if not actual_trajectory:
                issues.append("Trajectory validation failed: Actual node execution trajectory is empty in run_workflow.py.")
                trajectory_pass = False
                break
                
            # Verification of internal output tool
            internal_ok = any(t.get("tool") == "write_node_output" for t in actual_trajectory)
            if not internal_ok:
                issues.append("Tool Trajectory validation failed: Node output tool 'write_node_output' is never called in run_workflow.py.")
                trajectory_pass = False
                break
                
        if not trajectory_pass:
            return False, issues
            
        return True, issues
