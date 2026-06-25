import os
import sys
import json
import yaml
from typing import List, Dict, Any, Tuple

TIERS = ["read_only", "draft_only", "action_allowed"]

def get_skill_metadata(skill_path: str) -> Dict[str, Any]:
    skill_md_path = os.path.join(skill_path, "SKILL.md")
    if not os.path.exists(skill_md_path):
        return None
    try:
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()
        parts = content.split("---")
        if len(parts) >= 3:
            metadata = yaml.safe_load(parts[1])
            return metadata
    except Exception:
        pass
    return None

def find_skill(skill_name: str, base_dir: str = "./skills") -> Tuple[str, str, str]:
    normalized_names = {
        skill_name.replace("_", "-"),
        skill_name.replace("-", "_")
    }
    
    for tier in TIERS:
        tier_dir = os.path.join(base_dir, tier)
        if not os.path.exists(tier_dir):
            continue
        for item in os.listdir(tier_dir):
            item_path = os.path.join(tier_dir, item)
            if os.path.isdir(item_path):
                meta = get_skill_metadata(item_path)
                meta_name = meta.get("name") if meta else ""
                if item in normalized_names or meta_name in normalized_names:
                    return tier, item, item_path
    return None, None, None

def find_test_file(skill_path: str) -> str:
    for file in os.listdir(skill_path):
        if file.endswith(".test.json"):
            return os.path.join(skill_path, file)
    return None

def load_eval_cases(test_file_path: str) -> List[Dict[str, Any]]:
    try:
        with open(test_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data.get("eval_cases", [])
        elif isinstance(data, list):
            return data
    except Exception:
        pass
    return []

def check_skill_syntax(skill_path: str, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    print("--- [Pre-check] Checking SKILL.md Syntax & word count ---")
    issues = []
    
    skill_md_path = os.path.join(skill_path, "SKILL.md")
    if not os.path.exists(skill_md_path):
        issues.append("SKILL.md not found in the skill directory.")
        return False, issues
        
    try:
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()
        body = content.split("---")[-1]
        word_count = len(body.split())
        print(f"  - SKILL.md Body Word Count: {word_count} (Limit: 5000)")
        if word_count > 5000:
            issues.append(f"SKILL.md body exceeds 5000 words (got {word_count}). Move details to references/.")
    except Exception as e:
        issues.append(f"Failed to read/parse SKILL.md: {e}")
        
    if not metadata:
        issues.append("Invalid or missing YAML frontmatter in SKILL.md.")
    else:
        required_fields = ["name", "description"]
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                issues.append(f"Missing required frontmatter field: '{field}'.")
                
    return len(issues) == 0, issues
