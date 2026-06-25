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
{{node_definitions}}
# --- NODE DEFINITIONS END ---

# --- WORKFLOW GRAPH START ---
# scaffold_workflow.pyによって有向エッジとWorkflowオブジェクトが定義されます。
{{workflow_graph}}
# --- WORKFLOW GRAPH END ---

app = App(
    name="{{workflow_name_underscore}}_app",
    root_agent=root_agent
)

async def run_main():
    parser = argparse.ArgumentParser(description="Run {{workflow_name}} workflow.")
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
