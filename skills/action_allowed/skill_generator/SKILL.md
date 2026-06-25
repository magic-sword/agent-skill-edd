---
name: skill-generator
description: |
  ユーザーの要望に基づいて、新しいエージェント用の「Skill」を自動的に構築します。
  新しいスキルフォルダを指定された配置場所（デフォルトは ./skills/read_only、または引数や設定JSONの output_dir で指定されたパス）配下に作成し、
  YAMLフロントマッターを含む SKILL.md、
  Google ADK v2.3.0 準拠のテストケース（[skill_name].test.json）、評価Criteria（test_config.json）、
  環境シミュレーション構成（env_simulation_config.json）、および標準のフォルダ構造を生成します。
  すでに存在するスキルを変更・削除する場合は使用しないでください。
version: 1.0.0
license: MIT
allowed-tools:
  - write_to_file
  - run_command
adk-version: 2.3.0
require-latest-adk-validation: true
---

# Skill Generator

ユーザーの要求するタスクに応じた「新しいスキル」の雛形（Scaffold）を、Google ADK v2.3.0 基準で自動作成します。AIによるテストケース自動生成（User Simulation）を活用した評価駆動開発（EDD）プロセスを採用しています。

## When to use
- ユーザーから新しいスキルの作成を依頼されたとき。
- エージェントが繰り返し実行する複雑なワークフローを、コンテキスト節約のために別スキルとして切り出したいとき。

## When NOT to use
- 既存のスキルの中身を変更・修正・更新するとき。
- グローバル設定ファイル（`AGENTS.md` など）を変更するとき。

## Workflow

### 1. 要件定義と命名の決定
ユーザーの要望から以下の情報を抽出・決定します。
- **スキル名**: ケバブケース（例: `pdf-processing`, `bigquery-ingestion`）。動名詞（-ing）から始める名前を推奨します。
- **ディレクトリ名**: スネークケース（例: `pdf_processing`, `bigquery_ingestion`）。
- **説明（Description）**: トリガー条件、何をするか、いつ使うべきか、そして「いつ使うべきではないか（反トリガー）」を明確にします。
- **使用可能ツール**: スキルが実行するのに必要最小限のツール一覧。

### 2. 評価駆動開発（EDD）の設計
生成されるテストケース（`*.test.json`）のAI自動生成のために、ユーザーシミュレータパラメータ（シミュレーションのゴール、制約など）を準備します。これらは `scaffold.py` 内部で自動的に `user_simulation_config.json` として反映されます。

### 3. SKILL.md の指示（L2）ドラフト
新しいスキルの `SKILL.md` に含める具体的な手順や指示（L2）をドラフトします。
指示には「何を（What）」「どうやるか（How）」を明確なステップに分けて記述します。

### 4. 設定ファイルの書き出し
PowerShell のエスケープ問題を防ぐため、ドラフトした内容を一度以下の一時的なJSONファイルに UTF-8 で保存します。
- 保存先パス: `skills/action_allowed/skill_generator/scripts/temp_config.json`
- 記述するJSON構造:
  ```json
  {
    "name": "csv-converter",
    "description": "Converts JSON to CSV...",
    "allowed_tools": ["view_file", "write_to_file"],
    "instructions": "## When to use\n..."
  }
  ```

### 5. スクリプトの実行によるフォルダ生成
`run_command` ツールを使用し、作成した設定ファイルを引数に指定して `scaffold.py` を実行します。
- コマンド例:
  ```powershell
  python skills/action_allowed/skill_generator/scripts/scaffold.py --config skills/action_allowed/skill_generator/scripts/temp_config.json
  ```
  ※ スクリプトは内部で自動的に `adk eval_set generate_eval_cases` を実行し、AIによるテストケース自動生成を試みます。失敗した場合は静的テンプレートテストへ自動フォールバックします。

### 6. 後処理と報告
1. 生成が成功したことを確認したら、一時ファイル（`skills/action_allowed/skill_generator/scripts/temp_config.json`）を削除します。
2. 作成されたディレクトリ構造およびファイルの絶対パスを Markdown リンク（例: [SKILL.md](file:///d:/kaggle/antigravity/agent-skill-edd/skills/draft_only/csv_converter/SKILL.md)）でユーザーに報告します。
