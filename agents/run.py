import os
import sys
import json
import argparse
import asyncio
import importlib.util

from google.adk import Agent
from google.adk.apps import App
from google.adk.runners import InMemoryRunner

# 状態デカップリング用のヘルパー関数
def read_node_output_file(file_path: str) -> dict:
    """
    指定されたパスがJSONファイルであれば、中身を読み込んで辞書として返します。
    """
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] 結果ファイル {file_path} の読み込みに失敗しました: {e}")
    return {"result": str(file_path)}

def load_agent_module(agent_path: str):
    """
    指定されたファイルパスからエージェントモジュールを動的にインポートします。
    """
    module_name = "dynamic_agent_module"
    spec = importlib.util.spec_from_file_location(module_name, agent_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"エージェントスクリプトが見つかりませんでした: {agent_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

async def run_main():
    parser = argparse.ArgumentParser(description="Google ADK エージェントを実行する共通エントリーポイント。")
    parser.add_argument(
        "--agent-script", "--workflow", "--agent",
        dest="agent_script",
        required=True, 
        help="実行するエージェント定義スクリプトのパス (例: ./agents/draft_only/skill_promotion_agent/agent.py)"
    )
    parser.add_argument(
        "--input", 
        required=True, 
        help="エージェントへの入力（タスク内容など）"
    )
    parser.add_argument(
        "--min-tier", 
        default="read_only", 
        choices=["read_only", "draft_only", "action_allowed"],
        help="許可する最小のTierレベル (デフォルト: read_only)"
    )
    parser.add_argument(
        "--skill-manager-path", 
        default=os.getenv("SKILL_MANAGER_PATH", "./skills/action_allowed/skill_manager"), 
        help="skill_manager ディレクトリのパス"
    )
    parser.add_argument(
        "--output", 
        default="output.json", 
        help="実行結果を書き出す出力ファイルパス"
    )
    args = parser.parse_args()

    # 1. エージェントスクリプトのロード
    module = load_agent_module(args.agent_script)
    
    # 必要スキルのリストとファクトリ関数を取得
    required_skills = getattr(module, "REQUIRED_SKILLS", [])
    create_agent = getattr(module, "create_agent", None)
    if create_agent is None:
        raise AttributeError(f"エージェントスクリプト {args.agent_script} に 'create_agent' 関数が定義されていません。")

    # 2. skill_manager からのツール解決
    # パスが可変なため、動的に sys.path に追加して loader.py をインポート
    loader_dir = os.path.abspath(os.path.join(args.skill_manager_path, "scripts"))
    if loader_dir not in sys.path:
        sys.path.insert(0, loader_dir)
        
    try:
        from loader import get_library_toolset_for_workflow
    except ImportError as e:
        raise ImportError(f"skill_manager の loader.py のインポートに失敗しました。パスを確認してください: {loader_dir}. エラー: {e}")

    # 必要最小限のツールセットを構築
    toolset = get_library_toolset_for_workflow(required_names=required_skills, min_tier=args.min_tier)

    # 3. サブエージェント（WorkflowまたはAgent）の構築
    # 解決された SkillToolset をリスト形式 [toolset] で渡します。
    sub_agent = create_agent(tools=[toolset])

    # 4. App および Runner の構築
    app = App(
        name="agent_execution_app",
        root_agent=sub_agent
    )
    runner = InMemoryRunner(app=app)

    print(f"--- 実行開始: {sub_agent.name} ---")
    try:
        result = await runner.run_debug(args.input)
        print("サブエージェントが正常に完了しました。")
        print(f"実行結果オブジェクト/パス: {result}")
        
        # 結果が一時ファイルパスであれば、中身を読み取って出力ファイルに保存する
        output_data = {}
        if isinstance(result, str) and os.path.exists(result):
            output_data = read_node_output_file(result)
        else:
            output_data = {"result": str(result)}
            
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"結果を出力ファイルに保存しました: {args.output}")
            
    except Exception as e:
        print(f"サブエージェントの実行中にエラーが発生しました: {e}")
        raise e

if __name__ == "__main__":
    asyncio.run(run_main())
