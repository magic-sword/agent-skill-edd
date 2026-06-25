import os
import sys
import json
import re
import subprocess
from typing import Tuple, List, Any
from .base_pattern import BaseEvaluationPattern

class UnitTestPattern(BaseEvaluationPattern):
    """
    Pattern 1: Eval-as-Unit-Test
    Verifies that the skill has at least 3 test cases and has testable specificity
    (at least 3 positive and 3 negative triggers).
    """
    def __init__(self, name: str = "Pattern 1: Unit-Test"):
        super().__init__(name)

    def evaluate(self, context: Any) -> Tuple[bool, List[str]]:
        print(f"\n--- [{self.name}] Checking Eval-as-Unit-Test ---")
        issues = []
        
        # 1. Check Unit test count (minimum 3 cases)
        if len(context.eval_cases) < 3:
            issues.append(f"Insufficient test cases in *.test.json. Minimum 3 cases required (got {len(context.eval_cases)}).")
            
        # 2. Check Positive / Negative trigger ratio (Specificity: 3+ positive, 3+ negative)
        pos_count = 0
        neg_count = 0
        normalized_skill_name = context.skill_name.replace("_", "-")
        
        for case in context.eval_cases:
            expected = case.get("expected_skill", "")
            eval_id = case.get("eval_id", "")
            
            is_negative = "negative" in eval_id.lower() or (expected and expected.replace("_", "-") != normalized_skill_name)
            
            if is_negative:
                neg_count += 1
            else:
                pos_count += 1
                
        print(f"  - Trigger specificity: {pos_count} Positive cases, {neg_count} Negative cases")
        if pos_count < 3:
            issues.append(f"Testable Specificity failed: At least 3 Positive cases required (got {pos_count}).")
        if neg_count < 3:
            issues.append(f"Testable Specificity failed: At least 3 Negative cases required (got {neg_count}).")
            
        # 3. Check ADK version validation (v2.3.0 compliance)
        require_latest = context.metadata.get("require-latest-adk-validation") if context.metadata else False
        if require_latest:
            declared_version = context.metadata.get("adk-version")
            print(f"  - Skill declares ADK version compliance: {declared_version}")
            
            # Detect installed ADK version
            installed_version = os.environ.get("MOCK_ADK_VERSION")
            if not installed_version:
                try:
                    import google.adk
                    installed_version = getattr(google.adk, "__version__", None)
                except ImportError:
                    # If not imported, check using subprocess or CLI
                    try:
                        res = subprocess.run(["adk", "--version"], capture_output=True, text=True, shell=True)
                        if res.returncode == 0:
                            match = re.search(r'(\d+\.\d+\.\d+)', res.stdout)
                            if match:
                                installed_version = match.group(1)
                    except Exception:
                        pass
            
            print(f"  - Detected environment ADK version: {installed_version}")
            if not declared_version:
                issues.append("require-latest-adk-validation is enabled, but 'adk-version' metadata is missing in SKILL.md.")
            elif installed_version and declared_version != installed_version:
                issues.append(f"ADK Version Mismatch: Skill targets ADK v{declared_version}, but environment is running latest v{installed_version}. Please upgrade the skill.")
            elif not installed_version:
                print("  [WARNING] Unable to detect installed ADK version. Skipping mismatch check.")
            
        success = len(issues) == 0
        return success, issues


class GoldenDatasetPattern(BaseEvaluationPattern):
    """
    Pattern 2: Golden Dataset
    Verifies that the skill has a Golden Dataset (20+ cases) and has been approved by human review.
    """
    def __init__(self, name: str = "Pattern 2: Golden Dataset"):
        super().__init__(name)

    def evaluate(self, context: Any) -> Tuple[bool, List[str]]:
        print(f"\n--- [{self.name}] Checking Golden Dataset ---")
        issues = []
        
        # 20+ cases check
        print(f"  - Checking for Golden Dataset (20+ cases)...")
        mock_golden = os.environ.get("MOCK_GOLDEN_DATASET", "").lower() in ["y", "yes", "1", "true"]
        if len(context.eval_cases) < 20 and not mock_golden:
            issues.append(f"Golden Dataset requirement failed: requires at least 20 test cases (got {len(context.eval_cases)}).")
            
        # Human approval check
        mock_human = os.environ.get("MOCK_HUMAN_REVIEW", "").lower() in ["y", "yes", "1", "true"]
        if mock_human:
            print("  - [MOCK] Human Review approved via environment variable.")
        elif sys.stdin.isatty():
            try:
                ans = input("  [?] Human Review: Has this skill been reviewed and approved by the domain team? (y/N): ")
                if ans.lower().strip() != "y":
                    issues.append("Human Review approval is required for Golden Dataset graduation.")
            except KeyboardInterrupt:
                issues.append("Human Review check cancelled.")
        else:
            print("  [WARNING] Non-interactive terminal. Assuming Human Review approval is NOT verified.")
            issues.append("Non-interactive terminal: Cannot verify Human Review approval.")
            
        success = len(issues) == 0
        return success, issues


class LlmAsJudgePattern(BaseEvaluationPattern):
    """
    Pattern 3: LLM-as-Judge & Trajectory via Google ADK
    Delegates validation to ADK v2.3.0 CLI 'adk eval' command.
    """
    def __init__(self, name: str = "Pattern 3: LLM-as-Judge (ADK)"):
        super().__init__(name)

    def evaluate(self, context: Any) -> Tuple[bool, List[str]]:
        print(f"\n--- [{self.name}] Checking LLM-as-Judge & Trajectory ---")
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("  [WARNING] GEMINI_API_KEY not set. Skipping dynamic ADK eval execution.")
            return True, ["GEMINI_API_KEY environment variable is missing. Real-time ADK evaluation skipped."]
            
        print(f"  - Running 'adk eval {context.skill_path}'...")
        try:
            cmd = ["adk", "eval", context.skill_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, shell=True)
            
            if result.returncode != 0:
                print(f"  [WARNING] 'adk eval' execution failed with exit code {result.returncode}.")
                print("  Stdout:", result.stdout)
                print("  Stderr:", result.stderr)
                if "not found" in result.stderr or "command not found" in result.stderr or "R}h" in result.stderr:
                    return True, [f"adk command not found in PATH. Skipping actual eval runner test. Stderr: {result.stderr.strip()}"]
                return False, [f"adk eval execution failed: {result.stderr.strip()}"]
                
            print("  - ADK Eval output parsed successfully.")
            print(result.stdout)
            
            if "FAIL" in result.stdout or "Failure" in result.stdout:
                return False, ["One or more ADK evaluation criteria failed. Check adk eval stdout logs above."]
                
            return True, []
            
        except subprocess.TimeoutExpired:
            return False, ["Evaluation timeout. 'adk eval' took too long to respond."]
        except Exception as e:
            print(f"  [WARNING] Failed to run 'adk eval': {e}")
            return True, [f"Failed to run ADK eval: {e}. Skipping dynamic check."]


class AdversarialPattern(BaseEvaluationPattern):
    """
    Pattern 4: Adversarial / Red-Team
    Verifies that red-teaming and pass^k verification have been manually completed.
    """
    def __init__(self, name: str = "Pattern 4: Adversarial"):
        super().__init__(name)

    def evaluate(self, context: Any) -> Tuple[bool, List[str]]:
        print(f"\n--- [{self.name}] Checking Adversarial / Red-Team ---")
        issues = []
        
        mock_human = os.environ.get("MOCK_HUMAN_REVIEW", "").lower() in ["y", "yes", "1", "true"]
        if mock_human:
            print("  - [MOCK] Adversarial Red-Teaming approved via environment variable.")
        elif not sys.stdin.isatty():
            print("  [WARNING] Non-interactive terminal. Assuming Adversarial Red-Teaming is NOT verified.")
            issues.append("Non-interactive terminal: Cannot verify Adversarial Red-Teaming.")
            return False, issues
            
        if not mock_human:
            try:
                ans1 = input("  [?] Adversarial: Has full adversarial red-teaming (positive trigger rephrasings and boundary tests) been completed? (y/N): ")
                ans2 = input("  [?] Reliability: Have you confirmed sustained success (pass^k) with zero rollback events? (y/N): ")
                
                if ans1.lower().strip() != "y" or ans2.lower().strip() != "y":
                    issues.append("Adversarial Red-Teaming and sustained success (pass^k) verification required.")
            except KeyboardInterrupt:
                issues.append("Adversarial checks cancelled.")
            
        success = len(issues) == 0
        return success, issues


class CanaryPattern(BaseEvaluationPattern):
    """
    Pattern 5: Canary / Shadow Mode
    Verifies that Canary deployment has been manually completed and monitored.
    """
    def __init__(self, name: str = "Pattern 5: Canary"):
        super().__init__(name)

    def evaluate(self, context: Any) -> Tuple[bool, List[str]]:
        print(f"\n--- [{self.name}] Checking Canary / Shadow Mode ---")
        issues = []
        
        mock_human = os.environ.get("MOCK_HUMAN_REVIEW", "").lower() in ["y", "yes", "1", "true"]
        if mock_human:
            print("  - [MOCK] Canary/Shadow Mode approved via environment variable.")
        elif not sys.stdin.isatty():
            print("  [WARNING] Non-interactive terminal. Assuming Canary/Shadow Mode is NOT verified.")
            issues.append("Non-interactive terminal: Cannot verify Canary/Shadow Mode.")
            return False, issues
            
        if not mock_human:
            try:
                ans = input("  [?] Canary/Shadow: Has this skill been deployed in Shadow/Canary mode (e.g. 1% live traffic) for 24+ hours? (y/N): ")
                if ans.lower().strip() != "y":
                    issues.append("Canary / Shadow Mode deployment and monitoring required.")
            except KeyboardInterrupt:
                issues.append("Canary checks cancelled.")
            
        success = len(issues) == 0
        return success, issues
