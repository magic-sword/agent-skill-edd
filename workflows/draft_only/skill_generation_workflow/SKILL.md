---
name: skill-generation-workflow
description: |
  get_library_config から最低Tierのパスを取得し、skill_generator を用いてその場所へ新しいスキルを自動生成する連携ワークフローです。
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
スキル管理スキルから最低Tierのパスを取得し、スキルを自動生成したい場合に使用します。

## When NOT to use
手動で特定のフォルダに直接スキルを作成する場合や、ワークフローを生成する場合は使用しないでください。
