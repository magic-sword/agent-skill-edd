import os
import sys
import shutil
import argparse
import yaml

TIERS = ["read_only", "draft_only", "action_allowed"]

def parse_args():
    parser = argparse.ArgumentParser(description="Manage Agent Skills Library.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # list command
    subparsers.add_parser("list", help="List all skills in the library by Tier")
    
    # promote command
    promote_parser = subparsers.add_parser("promote", help="Promote a skill to a higher Tier")
    promote_parser.add_argument("--skill", required=True, help="Name of the skill (kebab-case or directory name)")
    promote_parser.add_argument("--to", choices=TIERS, help="Target Tier to promote to (optional)")
    
    # demote command
    demote_parser = subparsers.add_parser("demote", help="Demote a skill to a lower Tier")
    demote_parser.add_argument("--skill", required=True, help="Name of the skill (kebab-case or directory name)")
    demote_parser.add_argument("--to", required=True, choices=TIERS, help="Target Tier to demote to")
    
    return parser.parse_args()

def get_skill_metadata(skill_path):
    skill_md_path = os.path.join(skill_path, "SKILL.md")
    if not os.path.exists(skill_md_path):
        return None
    try:
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Extract YAML frontmatter
        parts = content.split("---")
        if len(parts) >= 3:
            metadata = yaml.safe_load(parts[1])
            return metadata
    except Exception:
        pass
    return None

def find_skill(skill_name, base_dir="./skills"):
    # Normalize names (kebab-case and snake_case)
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
                # Check directory name or metadata name
                meta = get_skill_metadata(item_path)
                meta_name = meta.get("name") if meta else ""
                if item in normalized_names or meta_name in normalized_names:
                    return tier, item, item_path
    return None, None, None

def list_skills(base_dir="./skills"):
    print("=== Agent Skills Library ===")
    for tier in TIERS:
        print(f"\n[{tier.upper()}]")
        tier_dir = os.path.join(base_dir, tier)
        if not os.path.exists(tier_dir) or not os.listdir(tier_dir):
            print("  (No skills)")
            continue
        for item in os.listdir(tier_dir):
            item_path = os.path.join(tier_dir, item)
            if os.path.isdir(item_path):
                meta = get_skill_metadata(item_path)
                if meta:
                    name = meta.get("name", item)
                    description = meta.get("description", "").strip().split("\n")[0]
                    print(f"  - {name} ({item}/)")
                    print(f"    Description: {description}")
                else:
                    print(f"  - {item}/ (No SKILL.md or invalid metadata)")

def move_skill(skill_name, target_tier, base_dir="./skills"):
    current_tier, dir_name, current_path = find_skill(skill_name, base_dir)
    if not current_path:
        print(f"Error: Skill '{skill_name}' not found in library.")
        sys.exit(1)
        
    if current_tier == target_tier:
        print(f"Skill '{skill_name}' is already in Tier '{target_tier}'.")
        return
        
    target_dir = os.path.join(base_dir, target_tier, dir_name)
    
    # Perform move
    try:
        shutil.move(current_path, target_dir)
        print(f"Successfully moved '{skill_name}' from '{current_tier}' to '{target_tier}'.")
        print(f"  Path: {target_dir}")
    except Exception as e:
        print(f"Error: Failed to move skill. {e}")
        sys.exit(1)

def main():
    args = parse_args()
    base_dir = "./skills"
    
    # Check if pyyaml is installed (since we parse YAML)
    try:
        import yaml
    except ImportError:
        print("Error: 'pyyaml' package is required. Please install it with 'pip install pyyaml'.")
        sys.exit(1)
        
    if args.command == "list":
        list_skills(base_dir)
    elif args.command == "promote":
        current_tier, _, _ = find_skill(args.skill, base_dir)
        if not current_tier:
            print(f"Error: Skill '{args.skill}' not found in library.")
            sys.exit(1)
            
        if args.to:
            target_tier = args.to
            # Check if it's actually a promotion (higher index)
            if TIERS.index(target_tier) <= TIERS.index(current_tier):
                print(f"Error: Cannot promote from '{current_tier}' to '{target_tier}' (target tier is not higher).")
                sys.exit(1)
        else:
            current_idx = TIERS.index(current_tier)
            if current_idx >= len(TIERS) - 1:
                print(f"Skill '{args.skill}' is already at the highest Tier: '{current_tier}'.")
                sys.exit(0)
            target_tier = TIERS[current_idx + 1]
            
        move_skill(args.skill, target_tier, base_dir)
        
    elif args.command == "demote":
        current_tier, _, _ = find_skill(args.skill, base_dir)
        if not current_tier:
            print(f"Error: Skill '{args.skill}' not found in library.")
            sys.exit(1)
            
        target_tier = args.to
        if TIERS.index(target_tier) >= TIERS.index(current_tier):
            print(f"Error: Cannot demote from '{current_tier}' to '{target_tier}' (target tier is not lower).")
            sys.exit(1)
            
        move_skill(args.skill, target_tier, base_dir)

if __name__ == "__main__":
    main()
