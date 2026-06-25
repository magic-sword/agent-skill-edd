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
def find_target_workflow(node_input: str) -> Event:
    import os
    import sys
    import json
    user_data = read_node_input(node_input)
    workflow_name = user_data.get("raw_input") if "raw_input" in user_data else node_input
    workflow_name = workflow_name.strip()
    tiers = ["read_only", "draft_only", "action_allowed"]
    base_dir = "./workflows"
    found_tier = None
    found_dir_name = None
    found_path = None
    normalized_names = {
        workflow_name.replace("_", "-"),
        workflow_name.replace("-", "_")
    }
    for tier in tiers:
        tier_dir = os.path.join(base_dir, tier)
        if not os.path.exists(tier_dir):
            continue
        for item in os.listdir(tier_dir):
            item_path = os.path.join(tier_dir, item)
            if os.path.isdir(item_path):
                if item in normalized_names:
                    found_tier = tier
                    found_dir_name = item
                    found_path = item_path
                    break
        if found_path:
            break
    if not found_path:
        raise RuntimeError(f"Workflow '{workflow_name}' not found in library.")
    print(f"[find_target_workflow] Workflow: {workflow_name}, Current Tier: {found_tier}, Path: {found_path}")
    output_data = {
        "workflow_name": workflow_name,
        "current_tier": found_tier,
        "workflow_path": found_path
    }
    out_path = write_node_output(output_data, "find_target_workflow")
    return Event(output=out_path)

def evaluate_target_workflow(node_input: str) -> Event:
    import json
    import subprocess
    import os
    data = read_node_input(node_input)
    workflow_name = data.get("workflow_name")
    current_tier = data.get("current_tier")
    tiers = ["read_only", "draft_only", "action_allowed"]
    current_idx = tiers.index(current_tier)
    if current_idx >= len(tiers) - 1:
        raise RuntimeError(f"Workflow '{workflow_name}' is already at the highest Tier: '{current_tier}'")
    target_tier = tiers[current_idx + 1]
    print(f"[evaluate_target_workflow] Evaluating workflow '{workflow_name}' for target tier: {target_tier}")
    
    # Dynamically find workflow_evaluator path
    evaluator_path = None
    for t in tiers:
        p = os.path.join("skills", t, "workflow_evaluator", "scripts", "evaluate_workflow.py")
        if os.path.exists(p):
            evaluator_path = p
            break
    if not evaluator_path:
        raise RuntimeError("workflow_evaluator script (evaluate_workflow.py) not found in library.")
        
    cmd = [
        "python", evaluator_path,
        "--workflow", workflow_name,
        "--target-tier", target_tier
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    success = res.returncode == 0
    print(f"[evaluate_target_workflow] Evaluation return code: {res.returncode}")
    print(res.stdout)
    if not success:
        print(f"[evaluate_target_workflow] Evaluation failed: {res.stderr}")
    output_data = {
        "workflow_name": workflow_name,
        "current_tier": current_tier,
        "target_tier": target_tier,
        "evaluation_success": success,
        "stdout": res.stdout,
        "stderr": res.stderr
    }
    out_path = write_node_output(output_data, "evaluate_target_workflow")
    return Event(output=out_path)

def promote_target_workflow(node_input: str) -> Event:
    import json
    import subprocess
    import os
    data = read_node_input(node_input)
    workflow_name = data.get("workflow_name")
    target_tier = data.get("target_tier")
    evaluation_success = data.get("evaluation_success", False)
    if not evaluation_success:
        print(f"[promote_target_workflow] Workflow '{workflow_name}' did not pass evaluation. Promotion aborted.")
        output_data = {
            "status": "failed",
            "reason": "Evaluation did not pass.",
            "workflow": workflow_name
        }
    else:
        print(f"[promote_target_workflow] Promoting workflow '{workflow_name}' to {target_tier}")
        
        # Dynamically find workflow_manager path
        tiers = ["read_only", "draft_only", "action_allowed"]
        manager_path = None
        for t in tiers:
            p = os.path.join("skills", t, "workflow_manager", "scripts", "manage_workflows.py")
            if os.path.exists(p):
                manager_path = p
                break
        if not manager_path:
            raise RuntimeError("workflow_manager script (manage_workflows.py) not found in library.")
            
        cmd = [
            "python", manager_path,
            "promote",
            "--workflow", workflow_name,
            "--to", target_tier
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to promote workflow: {res.stderr}")
        print(f"[promote_target_workflow] Successfully promoted workflow '{workflow_name}' to {target_tier}")
        output_data = {
            "status": "success",
            "workflow": workflow_name,
            "promoted_to": target_tier
        }
    out_path = write_node_output(output_data, "promote_target_workflow")
    return Event(output=out_path)
# --- NODE DEFINITIONS END ---

# --- WORKFLOW GRAPH START ---
# scaffold_workflow.pyによって有向エッジとWorkflowオブジェクトが定義されます。

root_agent = Workflow(
    name="workflow_promotion_workflow",
    edges=[
        ("START", find_target_workflow, evaluate_target_workflow, promote_target_workflow)
    ]
)

# --- WORKFLOW GRAPH END ---

app = App(
    name="workflow_promotion_workflow_app",
    root_agent=root_agent
)

async def run_main():
    parser = argparse.ArgumentParser(description="Run workflow-promotion-workflow workflow.")
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
