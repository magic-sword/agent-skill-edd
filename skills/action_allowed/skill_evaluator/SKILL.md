---
name: skill-evaluator
description: |
  エージェント用スキルの評価を実行します。
  静的コード検証（YAMLフロントマッター、本文語数）、テストケース数（Unit-Test 3件以上、Golden 20件以上、Positive/Negativeトリガー比率）、
  およびGemini APIを利用したトリガー安定性の検証（LLM-as-Judge）と手動プロセスチェックリストの評価を行います。
version: 1.0.0
license: MIT
allowed-tools:
  - run_command
adk-version: 2.3.0
require-latest-adk-validation: true
---

# Skill Evaluator

スキルライブラリの各スキルが、指定されたTier（`draft_only`, `read_only`, `action_allowed`）の基準（Evaluation ToolkitおよびTriggerチェック）を満たしているかを検証します。

## When to use
- スキルの品質チェックを行いたいとき。
- スキルを上のTierに昇格させる前段階で、事前評価を実行したいとき。

## When NOT to use
- スキルの新規生成（Scaffold）を行うとき（`skill-generator` を使用）。
- スキルの物理的なTierディレクトリ間の移動や整理を行うとき（`skill-manager` を使用）。

## Workflow

### 1. 評価の実行
評価対象のスキル名と、目指すターゲットTier（デフォルトは `draft_only`）を指定して評価スクリプトを実行します。
- **実行コマンド**:
  ```powershell
  python skills/action_allowed/skill_evaluator/scripts/evaluate_skill.py --skill <skill-name> --target-tier <target-tier>
  ```
  ※ `target-tier` には `draft_only`, `read_only`, `action_allowed` のいずれかを指定します。

### 2. 実行時対話への対応
ターゲットTierが `read_only` または `action_allowed` の場合、実行時に対話式チェック（Human Review承認の有無など）が表示されます。その際は人間に質問し、回答を入力してください。

### 3. 結果の整理と報告
スクリプトが出力した `=== Evaluation Summary ===` の結果を基に、以下の内容をユーザーに報告します。
- 静的検証（文字数、YAML、テストケース件数、Positive/Negative割合）の合否
- LLM-as-Judge（言い換え安定性）の合否
- 手動プロセスの合否
- 修正すべき懸念点（ISSUES）がある場合はその一覧
