import os
import sys
import shutil
import argparse
import yaml

TIERS = ["read_only", "draft_only", "action_allowed"]

def parse_args():
    parser = argparse.ArgumentParser(description="Manage Workflows Library.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # list command
    subparsers.add_parser("list", help="List all workflows in the library by Tier")
    
    # promote command
    promote_parser = subparsers.add_parser("promote", help="Promote a workflow to a higher Tier")
    promote_parser.add_argument("--workflow", required=True, help="Name of the workflow (kebab-case or directory name)")
    promote_parser.add_argument("--to", choices=TIERS, help="Target Tier to promote to (optional)")
    
    # demote command
    demote_parser = subparsers.add_parser("demote", help="Demote a workflow to a lower Tier")
    demote_parser.add_argument("--workflow", required=True, help="Name of the workflow (kebab-case or directory name)")
    demote_parser.add_argument("--to", required=True, choices=TIERS, help="Target Tier to demote to")
    
    return parser.parse_args()

def get_workflow_metadata(workflow_path):
    skill_md_path = os.path.join(workflow_path, "SKILL.md")
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

def find_workflow(workflow_name, base_dir="./workflows"):
    normalized_names = {
        workflow_name.replace("_", "-"),
        workflow_name.replace("-", "_")
    }
    
    for tier in TIERS:
        tier_dir = os.path.join(base_dir, tier)
        if not os.path.exists(tier_dir):
            continue
        for item in os.listdir(tier_dir):
            item_path = os.path.join(tier_dir, item)
            if os.path.isdir(item_path):
                meta = get_workflow_metadata(item_path)
                meta_name = meta.get("name") if meta else ""
                if item in normalized_names or meta_name in normalized_names:
                    return tier, item, item_path
    return None, None, None

def list_workflows(base_dir="./workflows"):
    print("=== Workflows Library ===")
    for tier in TIERS:
        print(f"\n[{tier.upper()}]")
        tier_dir = os.path.join(base_dir, tier)
        if not os.path.exists(tier_dir) or not os.listdir(tier_dir):
            print("  (No workflows)")
            continue
        for item in os.listdir(tier_dir):
            item_path = os.path.join(tier_dir, item)
            if os.path.isdir(item_path):
                meta = get_workflow_metadata(item_path)
                if meta:
                    name = meta.get("name", item)
                    description = meta.get("description", "").strip().split("\n")[0]
                    print(f"  - {name} ({item}/)")
                    print(f"    Description: {description}")
                else:
                    print(f"  - {item}/ (No SKILL.md or invalid metadata)")

def move_workflow(workflow_name, target_tier, base_dir="./workflows"):
    current_tier, dir_name, current_path = find_workflow(workflow_name, base_dir)
    if not current_path:
        print(f"Error: Workflow '{workflow_name}' not found in library.")
        sys.exit(1)
        
    if current_tier == target_tier:
        print(f"Workflow '{workflow_name}' is already in Tier '{target_tier}'.")
        return
        
    target_dir = os.path.join(base_dir, target_tier, dir_name)
    
    try:
        shutil.move(current_path, target_dir)
        print(f"Successfully moved workflow '{workflow_name}' from '{current_tier}' to '{target_tier}'.")
        print(f"  Path: {target_dir}")
    except Exception as e:
        print(f"Error: Failed to move workflow. {e}")
        sys.exit(1)

def main():
    args = parse_args()
    base_dir = "./workflows"
    
    try:
        import yaml
    except ImportError:
        print("Error: 'pyyaml' package is required. Please install it with 'pip install pyyaml'.")
        sys.exit(1)
        
    if args.command == "list":
        list_workflows(base_dir)
    elif args.command == "promote":
        current_tier, _, _ = find_workflow(args.workflow, base_dir)
        if not current_tier:
            print(f"Error: Workflow '{args.workflow}' not found in library.")
            sys.exit(1)
            
        if args.to:
            target_tier = args.to
            if TIERS.index(target_tier) <= TIERS.index(current_tier):
                print(f"Error: Cannot promote from '{current_tier}' to '{target_tier}' (target tier is not higher).")
                sys.exit(1)
        else:
            current_idx = TIERS.index(current_tier)
            if current_idx >= len(TIERS) - 1:
                print(f"Workflow '{args.workflow}' is already at the highest Tier: '{current_tier}'.")
                sys.exit(0)
            target_tier = TIERS[current_idx + 1]
            
        move_workflow(args.workflow, target_tier, base_dir)
        
    elif args.command == "demote":
        current_tier, _, _ = find_workflow(args.workflow, base_dir)
        if not current_tier:
            print(f"Error: Workflow '{args.workflow}' not found in library.")
            sys.exit(1)
            
        target_tier = args.to
        if TIERS.index(target_tier) >= TIERS.index(current_tier):
            print(f"Error: Cannot demote from '{current_tier}' to '{target_tier}' (target tier is not lower).")
            sys.exit(1)
            
        move_workflow(args.workflow, target_tier, base_dir)

if __name__ == "__main__":
    main()
