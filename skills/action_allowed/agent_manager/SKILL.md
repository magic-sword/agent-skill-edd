---
name: agent_manager
description: |
  エージェントライブラリ内のすべてのエージェントを管理します。
  各エージェントのTier（Draft-Only, Read-Only, Action-Allowed）の移動（昇格・降格）、
  およびすべてのエージェントを一覧表示することが可能です。
version: 1.0.0
license: MIT
allowed-tools: "run_command"
adk-version: 2.3.0
require-latest-adk-validation: true
---

# Agent Manager

エージェントライブラリの各ディレクトリ（`draft_only/`, `read_only/`, `action_allowed/`）間の移動、および管理を行います。

## When to use
- エージェントのTierを昇格（例: `draft_only` から `read_only` や `action_allowed`）または降格させたいとき。
- エージェントライブラリの全体的な状態（どのTierに何のエージェントが属しているか）を一覧で確認したいとき。

## When NOT to use
- 新しいエージェントを生成（Scaffold）するとき。その場合は `agent-generator` メタスキルを使用してください。

## Workflow

### 1. アクションの選択
実行したい操作（一覧表示、昇格、降格）に応じて、対応するスクリプトコマンドを実行します。

* **エージェントの一覧表示**:
  ```powershell
  python skills/action_allowed/agent_manager/scripts/manage_agents.py list
  ```

* **エージェントの昇格 (Promote)**:
  `--workflow` に対象のエージェント名（kebab-case またはディレクトリ名）を指定します。
  `--to` でターゲットとする上位Tierを指定可能です（省略した場合は1段階昇格します）。
  ```powershell
  python skills/action_allowed/agent_manager/scripts/manage_agents.py promote --workflow <agent-name> [--to <target-tier>]
  ```

* **エージェントの降格 (Demote)**:
  `--workflow` に対象のエージェント名を指定し、`--to` でターゲットとする下位Tierを必ず指定します。
  ```powershell
  python skills/action_allowed/agent_manager/scripts/manage_agents.py demote --workflow <agent-name> --to <target-tier>
  ```

### 2. 後処理と報告
コマンドの実行結果（例: 「Successfully moved agent...」）を確認し、変更内容をユーザーに報告します。

