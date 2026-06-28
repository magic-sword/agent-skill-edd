---
name: workflow-promotion-workflow
description: |
  ワークフローの評価を実行し、合格した場合は上位Tierへ自動昇格させます。
version: 1.0.0
license: MIT
allowed-tools:
  - run_command
adk-version: 2.3.0
require-latest-adk-validation: true
---

## When to use
- ワークフローを自動で評価し、合格した場合に上位Tierへ昇格させたいとき。

## When NOT to use
- スキルの評価・昇格を行いたいとき（`skill-promotion-workflow` を使用してください）。

## Workflow
1. 昇格対象のワークフロー名を引数 `--input` に指定して実行します。
```powershell
python workflows/read_only/workflow_promotion_workflow/scripts/run_workflow.py --input <workflow-name> --output output.json
```
2. 実行後、`output.json` を確認し、昇格結果を報告します。
