import os
import sys
import argparse
import json
import re

def parse_args():
    parser = argparse.ArgumentParser(description="Scaffold a new DAG Workflow compliant with ADK v2.3.0.")
    parser.add_argument("--config", required=True, help="Path to a JSON configuration file containing workflow specifications")
    parser.add_argument("--output-dir", default="./workflows/read_only", help="Parent directory where the workflow will be created")
    return parser.parse_args()

def validate_kebab_case(name):
    return re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', name) is not None

def main():
    args = parse_args()
    
    # Load configuration
    if not os.path.exists(args.config):
        print(f"Error: Config file '{args.config}' not found.")
        sys.exit(1)
        
    try:
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error: Failed to parse config JSON: {e}")
        sys.exit(1)
        
    name = config.get("name")
    description = config.get("description")
    allowed_tools = config.get("allowed_tools", [])
    nodes = config.get("nodes", [])
    edges = config.get("edges", [])
    instructions = config.get("instructions", "")
    test_cases = config.get("test_cases", {})
    
    if not name or not description or not instructions:
        print("Error: Missing required config fields: 'name', 'description', 'instructions'")
        sys.exit(1)
        
    if not validate_kebab_case(name):
        print(f"Error: Workflow name '{name}' must be in kebab-case.")
        sys.exit(1)
        
    dir_name = name.replace("-", "_")
    workflow_dir = os.path.abspath(os.path.join(args.output_dir, dir_name))
    
    if os.path.exists(workflow_dir):
        print(f"Error: Target directory '{workflow_dir}' already exists.")
        sys.exit(1)
        
    # Create directory structure
    os.makedirs(workflow_dir, exist_ok=True)
    os.makedirs(os.path.join(workflow_dir, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(workflow_dir, "references"), exist_ok=True)
    os.makedirs(os.path.join(workflow_dir, "assets"), exist_ok=True)
    
    # 1. Write SKILL.md
    tools_str = "\n".join([f"  - {t}" for t in allowed_tools])
    allowed_tools_yaml = f"allowed-tools:\n{tools_str}" if tools_str else "allowed-tools: []"
    
    skill_md_content = f"""---
name: {name}
description: |
  {description.strip()}
version: 1.0.0
license: MIT
{allowed_tools_yaml}
adk-version: 2.3.0
require-latest-adk-validation: true
---

{instructions.strip()}
"""
    with open(os.path.join(workflow_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(skill_md_content)
        
    # 2. Write test_config.json
    test_config = {
        "criteria": {
            "tool_trajectory_avg_score": 1.0,
            "response_match_score": 0.8
        }
    }
    with open(os.path.join(workflow_dir, "test_config.json"), "w", encoding="utf-8") as f:
        json.dump(test_config, f, indent=2)
        
    # 3. Write env_simulation_config.json
    env_sim_config = {
        "tool_simulation_configs": []
    }
    with open(os.path.join(workflow_dir, "env_simulation_config.json"), "w", encoding="utf-8") as f:
        json.dump(env_sim_config, f, indent=2)
        
    # 4. Generate run_workflow.py from template
    assets_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(assets_dir, "assets", "workflow_template.py")
    
    if not os.path.exists(template_path):
        print(f"Error: Template workflow_template.py not found at {template_path}")
        sys.exit(1)
        
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
        
    # Build node definitions code
    node_defs_code = []
    for node in nodes:
        node_name = node.get("name")
        node_type = node.get("type", "function")
        node_code = node.get("code", "")
        
        if node_type == "agent":
            # If it's an Agent node, build an Agent configuration block
            instruction = node.get("instruction", "")
            model = node.get("model", "gemini-flash-latest")
            agent_code = f"""
{node_name} = Agent(
    name="{node_name}",
    model="{model}",
    instruction=\"\"\"{instruction}\"\"\"
)
"""
            node_defs_code.append(agent_code)
        else:
            # Default is Function node (code provided in config)
            node_defs_code.append(node_code)
            
    node_definitions = "\n\n".join(node_defs_code)
    
    # Build workflow graph edges code
    edges_lines = []
    for edge in edges:
        # Convert edge list to tuple string representation, e.g. ["START", "node1", "node2"] -> '("START", node1, node2)'
        # Remove quotes from node names so they refer to actual variables in Python, except for "START"
        formatted_nodes = []
        for n in edge:
            if n == "START":
                formatted_nodes.append('"START"')
            else:
                formatted_nodes.append(n)
        edges_lines.append(f"        ({', '.join(formatted_nodes)})")
        
    edges_code = ",\n".join(edges_lines)
    
    workflow_graph_code = f"""
root_agent = Workflow(
    name="{dir_name}",
    edges=[
{edges_code}
    ]
)
"""
    
    # Substitute into template
    run_workflow_content = (template_content
                            .replace("{{node_definitions}}", node_definitions)
                            .replace("{{workflow_graph}}", workflow_graph_code)
                            .replace("{{workflow_name_underscore}}", dir_name)
                            .replace("{{workflow_name}}", name))
                            
    run_workflow_path = os.path.join(workflow_dir, "scripts", "run_workflow.py")
    with open(run_workflow_path, "w", encoding="utf-8") as f:
        f.write(run_workflow_content)
        
    # 5. Write [workflow_name].test.json
    test_template_path = os.path.join(assets_dir, "assets", "workflow_test_set_template.json")
    if not os.path.exists(test_template_path):
        print(f"Error: Test set template not found at {test_template_path}")
        sys.exit(1)
        
    with open(test_template_path, "r", encoding="utf-8") as f:
        test_template = f.read()
        
    # Calculate relative output path dynamically for command execution in test template
    rel_output_path = os.path.relpath(workflow_dir, os.getcwd()).replace("\\", "/")

    # Replace placeholders in test template
    replaced_test = (test_template
                     .replace("{{workflow_name_underscore}}", dir_name)
                     .replace("{{workflow_name}}", name)
                     .replace("{{test_input_1}}", test_cases.get("test_input_1", "run-workflow"))
                     .replace("{{expected_output_1}}", test_cases.get("expected_output_1", "Workflow executed successfully."))
                     .replace("{{expected_tool_1}}", test_cases.get("expected_tool_1", "run_command"))
                     .replace("{{arg_name_1}}", test_cases.get("arg_name_1", "CommandLine"))
                     .replace("{{arg_value_1}}", test_cases.get("arg_value_1", f"python {rel_output_path}/scripts/run_workflow.py --input test"))
                     .replace("{{negative_test_input_1}}", test_cases.get("negative_test_input_1", "How to cook ramen?"))
                     .replace("{{negative_expected_output_1}}", test_cases.get("negative_expected_output_1", "This workflow does not support general questions.")))
                     
    test_json_path = os.path.join(workflow_dir, f"{dir_name}.test.json")
    with open(test_json_path, "w", encoding="utf-8") as f:
        f.write(replaced_test)
        
    print(f"Successfully scaffolded workflow '{name}' in: {workflow_dir}")
    print(f"  - Created SKILL.md")
    print(f"  - Created test_config.json")
    print(f"  - Created env_simulation_config.json")
    print(f"  - Created scripts/run_workflow.py")
    print(f"  - Created {dir_name}.test.json")

if __name__ == "__main__":
    main()
