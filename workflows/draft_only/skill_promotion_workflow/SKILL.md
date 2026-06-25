---
name: skill-promotion-workflow
description: |
  スキルの現在のTierを特定し、evaluate_skill でテストを実行し、合格していれば manage_library で昇格（promote）させる自動連携ワークフローです。
version: 1.0.0
license: MIT
allowed-tools:
  - view_file
  - write_to_file
  - run_command
adk-version: 2.3.0
require-latest-adk-validation: true
---

## When to use
特定のスキルの品質を評価し、合格した場合に自動で上のTierに昇格させたい場合に使用します。

## When NOT to use
手動で昇格・降格を行う場合や、ワークフローを昇格させる場合は使用しないでください。
