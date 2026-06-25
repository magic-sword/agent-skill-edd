import argparse
import json
import sys

TIERS = ["read_only", "draft_only", "action_allowed"]

LIBRARY_CONFIG = {
    "skills": {
        "tiers": TIERS,
        "base_dir": "./skills",
        "paths": {
            "draft_only": "./skills/draft_only",
            "read_only": "./skills/read_only",
            "action_allowed": "./skills/action_allowed"
        }
    },
    "workflows": {
        "tiers": TIERS,
        "base_dir": "./workflows",
        "paths": {
            "draft_only": "./workflows/draft_only",
            "read_only": "./workflows/read_only",
            "action_allowed": "./workflows/action_allowed"
        }
    }
}

def parse_args():
    parser = argparse.ArgumentParser(description="Get configuration metadata for Skills and Workflows library.")
    parser.add_argument(
        "--type", 
        choices=["skills", "workflows", "all"], 
        default="all", 
        help="Type of library configuration to retrieve (default: all)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.type == "skills":
        output = LIBRARY_CONFIG["skills"]
    elif args.type == "workflows":
        output = LIBRARY_CONFIG["workflows"]
    else:
        output = LIBRARY_CONFIG
        
    # Output as formatted JSON
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
