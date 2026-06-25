import os
import sys
import argparse

# Add current scripts directory to PATH to ensure evaluator_lib imports correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evaluator_lib import (
    TIERS,
    find_skill,
    find_test_file,
    load_eval_cases,
    check_skill_syntax,
    TIER_EVALUATORS,
    helpers
)

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate an Agent Skill against ADK v2.3.0 library standards.")
    parser.add_argument("--skill", required=True, help="Name of the skill (kebab-case or directory name)")
    parser.add_argument("--target-tier", choices=TIERS, default="draft_only", help="The Tier you want to graduate this skill to")
    parser.add_argument("--base-dir", default="./skills", help="Parent directory of the skills library")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 1. Find skill
    current_tier, dir_name, skill_path = find_skill(args.skill, args.base_dir)
    if not skill_path:
        print(f"Error: Skill '{args.skill}' not found in the library.")
        sys.exit(1)
        
    print(f"Evaluating Skill '{args.skill}' ({dir_name}/) under ADK v2.3.0 standard")
    print(f"  Current Tier: {current_tier.upper()}")
    print(f"  Target Tier:  {args.target_tier.upper()}")
    print(f"  Path:         {skill_path}\n")
    
    # Pre-check: syntax
    metadata = helpers.get_skill_metadata(skill_path)
    syntax_pass, syntax_issues = check_skill_syntax(skill_path, metadata)
    if not syntax_pass:
        print("\n=== Pre-check Failed ===")
        for issue in syntax_issues:
            print(f"  * [ISSUE] {issue}")
        sys.exit(1)
        
    # Find ADK standard test file (*.test.json)
    test_file_path = find_test_file(skill_path)
    if not test_file_path:
        print(f"Error: No standard test file (*.test.json) found in {skill_path}")
        sys.exit(1)
        
    print(f"  - Found test file: {os.path.basename(test_file_path)}")
    eval_cases = load_eval_cases(test_file_path)
    
    # 2. Get the appropriate Evaluator class from Factory and execute
    evaluator_class = TIER_EVALUATORS.get(args.target_tier)
    if not evaluator_class:
        print(f"Error: Unsupported target tier: {args.target_tier}")
        sys.exit(1)
        
    evaluator = evaluator_class(args.skill, skill_path, eval_cases, metadata)
    success = evaluator.evaluate_all()
    
    if success:
        print(f"\n[SUCCESS] Skill '{args.skill}' successfully evaluated and eligible for Tier '{args.target_tier}'!")
        sys.exit(0)
    else:
        print(f"\n[FAILURE] Skill '{args.skill}' does not meet the criteria for Tier '{args.target_tier}'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
