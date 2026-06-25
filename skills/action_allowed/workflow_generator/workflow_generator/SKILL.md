---
name: workflow-generator
description: |
  複数の個別スキルをDAG（有向非巡回グラフ）で接続し、状態のデカップリング（一時JSONファイル）を用いて
  複雑な処理を行う ADK v2.3.0 準拠の連携ワークフローを自動的に構築します。
  新しいワークフローフォルダを指定された配置場所（デフォルトは ./workflows/read_only、または引数や設定JSONの output_dir で指定されたパス）配下に作成し、YAMLフロントマッターを含む SKILL.md、
  DAG接続スクリプト（run_workflow.py）、テストケース（[workflow_name].test.json）、
  評価Criteria（test_config.json）、環境シミュレーション構成（env_simulation_config.json）を生成します。
  すでに存在するスキルやワークフローを変更・削除する場合は使用しないでください。
version: 1.0.0
license: MIT
allowed-tools:
  - write_to_file
  - run_command
adk-version: 2.3.0
require-latest-adk-validation: true
---

# Workflow Generator

ユーザーの要求する複雑なタスクに対応する「複数のスキルを接続したワークフロー（DAG）」の雛形を、Google ADK v2.3.0 基準で自動作成します。ノード間（スキル間）の状態データの受け渡しには一時JSONファイル（URIポインタ）を使用し、コンテキストウィンドウの汚染（Context Rot）を防止します。

## When to use
- ユーザーから複数の個別スキルを連結したワークフローの作成を依頼されたとき。
- 単一のプロンプトや単一のエージェントでは処理しきれない、複数のフェーズからなる複雑な手順をDAG（有向非巡回グラフ）として構造化したいとき。

## When NOT to use
- 単一の単純なスキルを新規に作成するとき（`skill-generator` を使用してください）。
- 既存のスキルやワークフローのコードを変更・修正するとき。

## Workflow

### 1. 要件定義とDAG設計
ユーザーの要望から以下の情報を定義します。
- **ワークフロー名**: ケバブケース（例: `data-processing-workflow`）。
- **ディレクトリ名**: スネークケース（例: `data_processing_workflow`）。
- **ノード定義**: ワークフローを構成する各ステップ（ノード）の名前、タイプ（`agent` または `function`）、および処理内容。
  - 各ノードは前のノードから渡された一時JSONファイルのパス（または生の文字列入力）を受け取り、処理結果を別の一時JSONファイルに書き出し、そのパスを返します。
- **有向エッジ（Edges）**: ノード間の接続経路（例: `("START", "node_a", "node_b")`）。

### 2. ノードの実装コード定義
Functionノードの場合、一時ファイルポインタを読み取り、処理後に新しい一時ファイルを書き出すPythonコードを定義します。
```python
def my_node(node_input: str) -> Event:
    # 1. 状態データの読み込み
    data = read_node_input(node_input)
    
    # 2. 処理ロジックの実行
    # (例: データの変換、フィルタリング、外部API呼び出しなど)
    result = {"my_key": data.get("some_key", "") + "_processed"}
    
    # 3. 新しい一時JSONファイルに状態を書き出す
    out_path = write_node_output(result, "my_node")
    
    # 4. 次のノードへのポインタとしてファイルパスを返す
    return Event(output=out_path)
```

### 3. テストケースの設計
ワークフローの機能検証に必要なテストケース（`test_cases`）を定義します。
- `test_input_1`: ワークフローへの初期入力。
- `expected_output_1`: 期待される最終出力。
- `expected_tool_1`: 実行に使用するツール（通常 `run_command`）。
- `arg_name_1`: `CommandLine`
- `arg_value_1`: `python workflows/draft_only/[workflow_dir]/scripts/run_workflow.py --input [test_input]`

### 4. 設定ファイルの書き出し
PowerShell のエスケープ問題を回避するため、定義した内容を一時的なJSONファイルに UTF-8 で保存します。
- 保存先パス: `skills/action_allowed/workflow_generator/scripts/temp_workflow_config.json`
- 記述するJSON構造:
  ```json
  {
    "name": "csv-parser-workflow",
    "description": "...",
    "allowed_tools": ["view_file", "write_to_file", "run_command"],
    "nodes": [
      {
        "name": "node_name",
        "type": "function",
        "code": "..."
      }
    ],
    "edges": [
      ["START", "node_name"]
    ],
    "instructions": "...",
    "test_cases": {
      "test_input_1": "...",
      "expected_output_1": "...",
      "expected_tool_1": "run_command",
      "arg_name_1": "CommandLine",
      "arg_value_1": "python workflows/draft_only/csv_parser_workflow/scripts/run_workflow.py --input ...",
      "negative_test_input_1": "...",
      "negative_expected_output_1": "..."
    }
  }
  ```

### 5. スクリプトの実行によるワークフロー生成
`run_command` ツールを使用し、設定ファイルを指定して `scaffold_workflow.py` を実行します。
- コマンド例:
  ```powershell
  python skills/action_allowed/workflow_generator/scripts/scaffold_workflow.py --config skills/action_allowed/workflow_generator/scripts/temp_workflow_config.json
  ```

### 6. 後処理と報告
1. 生成が成功したことを確認したら、一時ファイル（`skills/action_allowed/workflow_generator/scripts/temp_workflow_config.json`）を削除します。
2. 作成されたディレクトリ構造およびファイルの絶対パスを Markdown リンクでユーザーに報告します。
