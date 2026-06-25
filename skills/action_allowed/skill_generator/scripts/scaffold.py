import os
import sys
import argparse
import json
import re
import subprocess

def parse_args():
    parser = argparse.ArgumentParser(description="Create a new Agent Skill scaffold compliant with ADK v2.3.0.")
    parser.add_argument("--name", help="Name of the skill in kebab-case (e.g., csv-converter)")
    parser.add_argument("--description", help="Description for the YAML frontmatter")
    parser.add_argument("--allowed-tools", default="", help="Comma-separated list of allowed tools")
    parser.add_argument("--instructions", help="Markdown body content of the SKILL.md file")
    parser.add_argument("--config", help="Path to a JSON configuration file containing the above options")
    parser.add_argument("--output-dir", default="./skills/read_only", help="Parent directory where the skill will be created")
    return parser.parse_args()

def validate_kebab_case(name):
    return re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', name) is not None

def main():
    args = parse_args()
    
    # Load configuration from JSON if provided
    config_data = {}
    if args.config:
        try:
            with open(args.config, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception as e:
            print(f"Error: Failed to load config file '{args.config}'. {e}")
            sys.exit(1)
            
    name = config_data.get("name") or args.name
    description = config_data.get("description") or args.description
    allowed_tools = config_data.get("allowed_tools") or args.allowed_tools
    instructions = config_data.get("instructions") or args.instructions
    output_dir = config_data.get("output_dir") or args.output_dir
    
    if not name or not description or not instructions:
        print("Error: Missing required arguments. Provide them via CLI flags or --config.")
        print("Required fields: name, description, instructions")
        sys.exit(1)
        
    if not validate_kebab_case(name):
        print(f"Error: Skill name '{name}' must be in kebab-case (lowercase, numbers, and hyphens only).")
        sys.exit(1)
        
    # Directory name should be in snake_case
    dir_name = name.replace("-", "_")
    skill_dir = os.path.abspath(os.path.join(output_dir, dir_name))
    
    if os.path.exists(skill_dir):
        print(f"Error: Target directory '{skill_dir}' already exists.")
        sys.exit(1)
        
    # Create directory structure
    os.makedirs(skill_dir, exist_ok=True)
    os.makedirs(os.path.join(skill_dir, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(skill_dir, "references"), exist_ok=True)
    os.makedirs(os.path.join(skill_dir, "assets"), exist_ok=True)
    
    # Process allowed-tools
    if isinstance(allowed_tools, list):
        tools_list = allowed_tools
    else:
        tools_list = [t.strip() for t in allowed_tools.split(",") if t.strip()]
        
    tools_str = "\n".join([f"  - {t}" for t in tools_list])
    if tools_str:
        allowed_tools_yaml = f"allowed-tools:\n{tools_str}"
    else:
        allowed_tools_yaml = "allowed-tools: []"
        
    # Format SKILL.md content
    skill_md_content = f"""---
name: {name}
description: |
  {description.strip()}
version: 1.0.0
license: MIT
{allowed_tools_yaml}
---

{instructions.strip()}
"""
    
    # Write SKILL.md
    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    with open(skill_md_path, "w", encoding="utf-8") as f:
        f.write(skill_md_content)
        
    # Write test_config.json (ADK Criteria)
    test_config = {
        "criteria": {
            "tool_trajectory_avg_score": 1.0,
            "response_match_score": 0.8
        }
    }
    test_config_path = os.path.join(skill_dir, "test_config.json")
    with open(test_config_path, "w", encoding="utf-8") as f:
        json.dump(test_config, f, indent=2)
        
    # Write env_simulation_config.json (ADK Environment Simulation)
    env_sim_config = {
        "tool_simulation_configs": []
    }
    env_sim_path = os.path.join(skill_dir, "env_simulation_config.json")
    with open(env_sim_path, "w", encoding="utf-8") as f:
        json.dump(env_sim_config, f, indent=2)

    # ----------------------------------------------------
    # Generate User Simulation Config and call adk eval_set
    # ----------------------------------------------------
    eval_set_id = f"{dir_name}_test_set"
    test_json_name = f"{dir_name}.test.json"
    test_json_path = os.path.join(skill_dir, test_json_name)
    
    # Read user simulation template and write customized config
    template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "user_simulation_config_template.json")
    user_sim_path = os.path.join(skill_dir, "user_simulation_config.json")
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
        
        # Replace template placeholders
        trigger_example = description.strip().split("\n")[0]
        config_content = template_content.replace("{{skill_name}}", name).replace("{{trigger_example}}", trigger_example)
        
        with open(user_sim_path, "w", encoding="utf-8") as f:
            f.write(config_content)
            
    except Exception as e:
        print(f"Warning: Failed to create user_simulation_config.json: {e}")
        user_sim_path = None

    # Attempt AI test case generation via ADK
    ai_generation_success = False
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if api_key and user_sim_path:
        print("  - GEMINI_API_KEY detected. Attempting AI-assisted test case generation via ADK...")
        
        # 1. Create a temporary dummy agent file for ADK CLI parser
        temp_agent_path = os.path.join(skill_dir, "temp_agent.py")
        dummy_agent_code = """
from google.adk.agents import LlmAgent
agent = LlmAgent(
    name="temp_scaffold_agent",
    model="gemini-2.5-flash",
    instruction="Temporary agent for evaluation scaffolding",
    tools=[]
)
"""
        try:
            with open(temp_agent_path, "w", encoding="utf-8") as f:
                f.write(dummy_agent_code)
                
            # 2. Run adk eval_set generate_eval_cases
            cmd = [
                "adk", "eval_set", "generate_eval_cases", 
                temp_agent_path, eval_set_id,
                "--user_simulation_config_file", user_sim_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90, shell=True)
            
            if result.returncode == 0:
                print("  - ADK test cases generated successfully.")
                ai_generation_success = True
                
                # The adk command outputs the generated file to a default location or storage URI.
                # Usually, it creates the file dynamically. We check if it produced the test.json.
                # If the CLI outputs to a default file, we find it and rename it.
                # If it's not found, we fall back to static.
                generated_file_name = f"{eval_set_id}.test.json"
                if os.path.exists(generated_file_name):
                    shutil.move(generated_file_name, test_json_path)
                elif os.path.exists(os.path.join(skill_dir, f"{eval_set_id}.test.json")):
                    pass # Already in directory
            else:
                print(f"  [WARNING] 'adk eval_set generate_eval_cases' failed: {result.stderr}")
                
        except Exception as e:
            print(f"  [WARNING] Failed to run AI-assisted test generation: {e}")
        finally:
            # Cleanup temp agent file
            if os.path.exists(temp_agent_path):
                os.remove(temp_agent_path)
                
    # Fallback to static test template if AI generation skipped or failed
    if not ai_generation_success:
        print("  - Falling back to static test template.")
        static_template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "test_template.json")
        try:
            with open(static_template_path, "r", encoding="utf-8") as f:
                template_data = f.read()
            
            # Simple placeholder replacement
            trigger_example = description.strip().split("\n")[0]
            replaced_data = (template_data
                             .replace("{{skill_name}}", name)
                             .replace("{{skill_name_underscore}}", dir_name)
                             .replace("{{test_input_1}}", trigger_example)
                             .replace("{{expected_output_1}}", f"CSV outputs for {name}")
                             .replace("{{expected_tool_1}}", tools_list[0] if tools_list else "some_tool")
                             .replace("{{arg_name_1}}", "input_arg")
                             .replace("{{arg_value_1}}", "test_val")
                             .replace("{{negative_test_input_1}}", "How to install Python?")
                             .replace("{{negative_expected_output_1}}", "This skill only supports CSV conversion."))
            
            with open(test_json_path, "w", encoding="utf-8") as f:
                f.write(replaced_data)
            print(f"  - Created static {test_json_path} (ADK EvalSet)")
            
        except Exception as e:
            print(f"Error: Failed to write static test template: {e}")
            sys.exit(1)
        
    print(f"Successfully created skill '{name}' in directory: {skill_dir}")
    print(f"  - Created {skill_md_path}")
    print(f"  - Created {test_json_path} (ADK EvalSet)")
    print(f"  - Created {test_config_path} (ADK Criteria Config)")
    print(f"  - Created {env_sim_path} (ADK Environment Simulation)")
    print(f"  - Created {user_sim_path} (ADK User Simulation Config)")
    print("  - Created subdirectories: scripts/, references/, assets/")

if __name__ == "__main__":
    main()
