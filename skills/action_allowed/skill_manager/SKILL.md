---
name: skill-manager
description: |
  エージェント用スキルライブラリの管理、および各スキルのTier（Read-Only, Draft-Only, Action-Allowed）の変更（昇格・降格）を行います。
  ライブラリ内のすべてのスキルをTierごとに一覧表示することも可能です。
version: 1.0.0
license: MIT
allowed-tools:
  - run_command
---

# Skill Manager

スキルライブラリの各ディレクトリ（`draft_only/`, `read_only/`, `action_allowed/`）間の移動、および管理を行います。

## When to use
- スキルのTierを昇格（例: `draft_only` から `read_only` や `action_allowed`）または降格させたいとき。
- スキルライブラリの全体的な状態（どのTierに何のスキルが属しているか）を一覧で確認したいとき。

## When NOT to use
- 新しいスキルを生成（Scaffold）するとき。その場合は `skill-generator` メタスキルを使用してください。

## Workflow

### 1. スキルライブラリの一覧表示
ライブラリ内のすべてのスキルと、そのTierおよび現在の説明文を一覧表示します。
- **実行コマンド**:
  ```powershell
  python skills/action_allowed/skill_manager/scripts/manage_library.py list
  ```

### 2. スキルの昇格 (Promotion)
指定したスキルを現在よりも上のTierに移動します。
- ターゲットTierを自動で1段階上げる場合の**実行コマンド**:
  ```powershell
  python skills/action_allowed/skill_manager/scripts/manage_library.py promote --skill <skill-name>
  ```
- 昇格先のTierを明示的に指定する場合の**実行コマンド**:
  ```powershell
  python skills/action_allowed/skill_manager/scripts/manage_library.py promote --skill <skill-name> --to <target-tier>
  ```
  ※ `target-tier` は `read_only` または `action_allowed` を指定します。

### 3. スキルの降格 (Demotion)
指定したスキルを現在よりも下のTierに移動します。
- **実行コマンド**:
  ```powershell
  python skills/action_allowed/skill_manager/scripts/manage_library.py demote --skill <skill-name> --to <target-tier>
  ```
  ※ `target-tier` は `draft_only` または `read_only` を指定します。

### 4. 実行後の報告
コマンドの実行結果（どのフォルダからどのフォルダに移動したか）をユーザーに報告します。
