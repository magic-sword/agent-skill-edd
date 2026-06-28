import os
import sys
import json
import re
import ast
import yaml
from typing import List, Dict, Any, Tuple

TIERS = ["read_only", "draft_only", "action_allowed"]

def get_agent_metadata(agent_path: str) -> Tuple[Dict[str, Any], str, List[str]]:
    skill_md_path = os.path.join(agent_path, "SKILL.md")
    if not os.path.exists(skill_md_path):
        return None, None, ["SKILL.md not found."]
    try:
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()
        parts = content.split("---")
        if len(parts) >= 3:
            metadata = yaml.safe_load(parts[1])
            body = parts[2]
            return metadata, body, []
    except Exception as e:
        return None, None, [f"Failed to parse SKILL.md metadata: {e}"]
    return None, None, ["Invalid SKILL.md structure (missing frontmatter separator ---)."]

def find_agent(agent_name: str, base_dir: str = "./agents") -> Tuple[str, str, str]:
    normalized_names = {
        agent_name.replace("_", "-"),
        agent_name.replace("-", "_")
    }
    for tier in TIERS:
        tier_dir = os.path.join(base_dir, tier)
        if not os.path.exists(tier_dir):
            continue
        for item in os.listdir(tier_dir):
            item_path = os.path.join(tier_dir, item)
            if os.path.isdir(item_path):
                res = get_agent_metadata(item_path)
                meta = res[0] if res else None
                meta_name = meta.get("name") if meta else ""
                if item in normalized_names or meta_name in normalized_names:
                    return tier, item, item_path
    return None, None, None

def find_test_file(agent_path: str) -> str:
    for file in os.listdir(agent_path):
        if file.endswith(".test.json"):
            return os.path.join(agent_path, file)
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

def check_agent_syntax(agent_path: str, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    print("--- [Pre-check] Checking SKILL.md Syntax & Metadata ---")
    issues = []
    
    skill_md_path = os.path.join(agent_path, "SKILL.md")
    if not os.path.exists(skill_md_path):
        issues.append("SKILL.md not found in the agent directory.")
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
        
        adk_version = metadata.get("adk-version")
        if not adk_version:
            print("  * [WARNING] 'adk-version' is missing in frontmatter.")
        else:
            print(f"  - Declared ADK version: {adk_version}")
                
    return len(issues) == 0, issues

def extract_trajectory_from_ast(run_agent_path: str) -> Tuple[List[Dict[str, str]], List[str]]:
    if not os.path.exists(run_agent_path):
        return [], [f"run_agent.py not found at {run_agent_path}"]
        
    try:
        with open(run_agent_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except Exception as e:
        return [], [f"Failed to parse run_agent.py AST: {e}"]
        
    edges = []
    node_calls = {}
    issues = []
    
    # ASTのトラバースを安全に行うため再実装
    try:
        class SimpleVisitor(ast.NodeVisitor):
            def visit_Assign(self, node):
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    if node.targets[0].id in ["agent", "root_agent"]:
                        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "Agent":
                            for kw in node.value.keywords:
                                if kw.arg == "edges":
                                    if isinstance(kw.value, ast.List):
                                        for elt in kw.value.elts:
                                            if isinstance(elt, ast.Tuple):
                                                edge_nodes = []
                                                for item in elt.elts:
                                                    if isinstance(item, ast.Constant):
                                                        edge_nodes.append(item.value)
                                                    elif isinstance(item, ast.Name):
                                                        edge_nodes.append(item.id)
                                                edges.append(edge_nodes)
                self.generic_visit(node)
                
            def visit_FunctionDef(self, node):
                func_name = node.name
                called_funcs = []
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Name):
                        called_funcs.append(subnode.func.id)
                node_calls[func_name] = called_funcs
                self.generic_visit(node)
                
        SimpleVisitor().visit(tree)
    except Exception as e:
        return [], [f"Failed to traverse AST: {e}"]
        
    trajectory = []
    if edges:
        # 順序検証用にシーケンスを単純化
        sequence = [n for n in edges[0] if n != "START"]
        for node_name in sequence:
            if node_name in node_calls:
                for called_f in node_calls[node_name]:
                    if called_f in ["write_node_output", "read_node_input", "run_command", "write_to_file", "view_file"]:
                        trajectory.append({"tool": called_f})
    else:
        issues.append("No Agent edges defined in run_agent.py.")
        
    return trajectory, issues

def check_trajectory(actual: List[Dict[str, str]], expected: List[Dict[str, str]], mode: str) -> bool:
    actual_tools = [x.get("tool") for x in actual]
    expected_tools = [x.get("tool") for x in expected]
    
    if mode == "EXACT":
        return actual_tools == expected_tools
        
    elif mode == "IN_ORDER":
        it = iter(actual_tools)
        return all(x in it for x in expected_tools)
        
    elif mode == "ANY_ORDER":
        from collections import Counter
        actual_cnt = Counter(actual_tools)
        expected_cnt = Counter(expected_tools)
        for t, count in expected_cnt.items():
            if actual_cnt[t] < count:
                return False
        return True
        
    return False
