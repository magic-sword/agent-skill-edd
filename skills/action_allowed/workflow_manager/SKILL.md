---
name: workflow-manager
description: |
  ワークフローライブラリ内のすべてのワークフローを管理します。
  各ワークフローのTier（Draft-Only, Read-Only, Action-Allowed）の移動（昇格・降格）、
  およびすべてのワークフローを一覧表示することが可能です。
version: 1.0.0
license: MIT
allowed-tools:
  - run_command
adk-version: 2.3.0
require-latest-adk-validation: true
---

# Workflow Manager

ワークフローライブラリの各ディレクトリ（`draft_only/`, `read_only/`, `action_allowed/`）間の移動、および管理を行います。

## When to use
- ワークフローのTierを昇格（例: `draft_only` から `read_only` や `action_allowed`）または降格させたいとき。
- ワークフローライブラリの全体的な状態（どのTierに何のワークフローが属しているか）を一覧で確認したいとき。

## When NOT to use
- 新しいワークフローを生成（Scaffold）するとき。その場合は `workflow-generator` メタスキルを使用してください。

## Workflow

### 1. アクションの選択
実行したい操作（一覧表示、昇格、降格）に応じて、対応するスクリプトコマンドを実行します。

* **ワークフローの一覧表示**:
  ```powershell
  python skills/action_allowed/workflow_manager/scripts/manage_workflows.py list
  ```

* **ワークフローの昇格 (Promote)**:
  `--workflow` に対象のワークフロー名（kebab-case またはディレクトリ名）を指定します。
  `--to` でターゲットとする上位Tierを指定可能です（省略した場合は1段階昇格します）。
  ```powershell
  python skills/action_allowed/workflow_manager/scripts/manage_workflows.py promote --workflow <workflow-name> [--to <target-tier>]
  ```

* **ワークフローの降格 (Demote)**:
  `--workflow` に対象のワークフロー名を指定し、`--to` でターゲットとする下位Tierを必ず指定します。
  ```powershell
  python skills/action_allowed/workflow_manager/scripts/manage_workflows.py demote --workflow <workflow-name> --to <target-tier>
  ```

### 2. 後処理と報告
コマンドの実行結果（例: 「Successfully moved workflow...」）を確認し、変更内容をユーザーに報告します。
