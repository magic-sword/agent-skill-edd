---
name: workflow-evaluator
description: |
  ワークフローライブラリ内のワークフローの品質および挙動の評価を実行します。
  静的コード検証（SKILL.md構造、フロントマッター）、テストケース数（Unit-Test 3件以上、Positive/Negativeトリガー比率）、
  および ADK v2.3.0 準拠のエンドツーエンド（E2E）出力品質と Tool Trajectory（実行軌跡）の整合性を検証します。
  軌跡検証では EXACT, IN_ORDER, ANY_ORDER の各評価モードに対応しており、特に action_allowed ティアの
  ワークフローでは ANY_ORDER による曖昧な評価を禁止する整合性チェックを含みます。
version: 1.0.0
license: MIT
allowed-tools:
  - run_command
adk-version: 2.3.0
require-latest-adk-validation: true
---

# Workflow Evaluator

ワークフローライブラリの各ワークフローが、指定されたTierの基準および ADK v2.3.0 の E2E・Tool Trajectory 要件を満たしているかを検証します。

## When to use
- ワークフローの品質チェックを行いたいとき。
- ワークフローを上のTierに昇格させる前段階で、事前評価を実行したいとき。

## When NOT to use
- ワークフローの新規生成（Scaffold）を行うとき（`workflow-generator` を使用）。
- ワークフローの物理的なTier移動や整理を行うとき（`workflow-manager` を使用）。

## Workflow

### 1. 評価の実行
評価対象のワークフロー名と、目指すターゲットTier（デフォルトは `draft_only`）を指定して評価スクリプトを実行します。

* **実行コマンド**:
  ```powershell
  python skills/action_allowed/workflow_evaluator/scripts/evaluate_workflow.py --workflow <workflow-name> --target-tier <target-tier>
  ```
  ※ `target-tier` には `draft_only`, `read_only`, `action_allowed` のいずれかを指定します。

### 2. 評価結果の確認
スクリプトが出力したサマリー結果を確認し、不合格の項目（ISSUES）がある場合は修正を行います。
特に、`action_allowed` ティアへの昇格を目指す場合、`test_config.json` 内の `criteria.trajectory_scoring_mode` が `IN_ORDER` または `EXACT` に設定されており、かつ実装コード内の軌跡接続（`edges`）とツールコール（`write_node_output` 等）が合致している必要があります。

### 3. 結果の整理と報告
以下の内容を整理してユーザーに報告します。
- 静的検証（文字数、YAML、テストケース件数、Positive/Negative割合）の合否
- E2E 最終出力形式および軌跡検証の合否
- 修正すべき懸念点（ISSUES）がある場合はその一覧
