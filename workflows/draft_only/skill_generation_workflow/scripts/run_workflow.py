import os
import json
import argparse
import asyncio
from google.adk import Workflow, Event, Agent
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from pydantic import BaseModel

# 状態デカップリング用のヘルパー関数
def read_node_input(node_input: str) -> dict:
    """
    入力がファイルパスである場合は、JSONとして読み込み辞書を返します。
    ファイルパスでない、または読み込みに失敗した場合は、文字列を含めた辞書を返します。
    """
    if not node_input:
        return {}
    if os.path.exists(node_input):
        try:
            with open(node_input, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] Failed to read temporary file {node_input}: {e}")
    
    # フォールバック: 生の入力文字列を辞書化して返す
    return {"raw_input": node_input}

def write_node_output(data: dict, step_name: str) -> str:
    """
    出力データを一時JSONファイルに書き出し、その絶対パスを返します。
    """
    os.makedirs("./temp_workflow_data", exist_ok=True)
    temp_filepath = os.path.abspath(f"./temp_workflow_data/temp_{step_name}.json")
    with open(temp_filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return temp_filepath

# --- NODE DEFINITIONS START ---
# scaffold_workflow.pyによって生成された各ノードのコードが以下に挿入されます。
def get_target_tier(node_input: str) -> Event:
    import json
    import subprocess
    cmd = ["python", "skills/action_allowed/skill_manager/scripts/get_library_config.py", "--type", "skills"]
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to get library config: {res.stderr}")
    config = json.loads(res.stdout)
    tiers = config.get("tiers", [])
    lowest_tier = tiers[0] if tiers else "draft_only"
    target_path = config.get("paths", {}).get(lowest_tier, "./skills/draft_only")
    print(f"[get_target_tier] Lowest Tier: {lowest_tier}, Path: {target_path}")
    user_data = read_node_input(node_input)
    output_data = {
        "user_request": user_data.get("raw_input") if "raw_input" in user_data else node_input,
        "target_tier": lowest_tier,
        "target_path": target_path
    }
    out_path = write_node_output(output_data, "get_target_tier")
    return Event(output=out_path)

def generate_skill(node_input: str) -> Event:
    import json
    import subprocess
    import os
    data = read_node_input(node_input)
    target_path = data.get("target_path", "./skills/draft_only")
    user_request = data.get("user_request", "")
    print(f"[generate_skill] User request: {user_request}")
    skill_name = "test-generated-skill"
    if "name:" in user_request:
        import re
        match = re.search(r"name:\s*([a-z0-9\-]+)", user_request)
        if match:
            skill_name = match.group(1)
    temp_config = {
        "name": skill_name,
        "description": f"Automatically generated skill based on: {user_request}",
        "allowed_tools": ["view_file", "write_to_file"],
        "instructions": "## When to use\n- Automatically generated usage workflow."
    }
    temp_config_path = os.path.abspath("./temp_generated_skill_config.json")
    with open(temp_config_path, "w", encoding='utf-8') as f:
        json.dump(temp_config, f, indent=2)
    cmd = [
        "python", "skills/action_allowed/skill_generator/scripts/scaffold.py",
        "--config", temp_config_path,
        "--output-dir", target_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if os.path.exists(temp_config_path):
        os.remove(temp_config_path)
    if res.returncode != 0:
        raise RuntimeError(f"scaffold.py failed: {res.stderr}\nStdout: {res.stdout}")
    print(f"[generate_skill] Successfully generated skill '{skill_name}' at {target_path}")
    out_path = write_node_output({"status": "success", "generated_skill": skill_name, "path": target_path}, "generate_skill")
    return Event(output=out_path)
# --- NODE DEFINITIONS END ---

# --- WORKFLOW GRAPH START ---
# scaffold_workflow.pyによって有向エッジとWorkflowオブジェクトが定義されます。

root_agent = Workflow(
    name="skill_generation_workflow",
    edges=[
        ("START", get_target_tier, generate_skill)
    ]
)

# --- WORKFLOW GRAPH END ---

app = App(
    name="skill_generation_workflow_app",
    root_agent=root_agent
)

async def run_main():
    parser = argparse.ArgumentParser(description="Run skill-generation-workflow workflow.")
    parser.add_argument("--input", required=True, help="Input raw text or path to input JSON file")
    parser.add_argument("--output", default="output.json", help="Output file path for the workflow results")
    args = parser.parse_args()
    
    runner = InMemoryRunner(app=app)
    
    try:
        # ワークフローの実行
        result = await runner.run_debug(args.input)
        print("Workflow completed successfully.")
        print(f"Final output pointer/result: {result}")
        
        # 最終結果が一時ファイルパスであれば、中身を読み取って出力ファイルに保存する
        output_data = {}
        if isinstance(result, str) and os.path.exists(result):
            output_data = read_node_input(result)
        else:
            output_data = {"result": str(result)}
            
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Results written to: {args.output}")
            
    except Exception as e:
        print(f"Error during workflow execution: {e}")
        raise e

if __name__ == "__main__":
    asyncio.run(run_main())
