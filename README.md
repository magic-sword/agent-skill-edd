# Agent Skill & Workflow EDD Library

Google ADK v2.3.0 規格に準拠した **Agent Skills（エージェントスキル）** および **有向非巡回グラフ（DAG）ベースの連携ワークフロー** を構築・評価・管理するためのライブラリです。

評価駆動開発（EDD: Evaluation-Driven Development）手法に基づき、エージェントの最終出力（E2E品質）だけでなく、実行時のツール呼び出しシーケンス（Tool Trajectory / 実行軌跡）を静的・動的に検証できる堅牢なライフサイクル管理システムを提供します。

---

## 🚀 主な機能とコンポーネント

### 1. スキル・ライブラリ (Skills Library)
個別のアクションや処理ロジックを担当する自律モジュールです。現在はすべて実用段階の `action_allowed` Tier に配置されています。

* **[skill_generator](file:///d:/kaggle/antigravity/agent-skill-edd/skills/action_allowed/skill_generator)**:
  指定されたパスへ ADK v2.3.0 準拠のスキル雛形（`SKILL.md`、テストセット、シミュレーション設定など）を自動作成します。
* **[skill_manager](file:///d:/kaggle/antigravity/agent-skill-edd/skills/action_allowed/skill_manager)**:
  スキルライブラリ内のスキルの昇格（`promote`）、降格（`demote`）、および一覧表示（`list`）を管理します。
* **[skill_evaluator](file:///d:/kaggle/antigravity/agent-skill-edd/skills/action_allowed/skill_evaluator)**:
  テスト数や対話要件など、Tier レベルに応じた複数パターンの品質基準（UnitTest, GoldenDataset, LlmAsJudge, Adversarial, Canary）を判定する評価エンジンです。

### 2. ワークフロー・ライブラリ (Workflows Library)
複数の個別スキルを DAG（有向非巡回グラフ）で接続し、状態ファイルを介して連携処理を行う上位モジュールです。現在はすべて評価プロセスを経て `draft_only` Tier に配置されています。

* **[workflow_generator](file:///d:/kaggle/antigravity/agent-skill-edd/skills/action_allowed/workflow_generator)**:
  一時ファイルを用いた状態のデカップリング設計で、複数のスキルを接続した連携ワークフローを自動生成します。
* **[workflow_manager](file:///d:/kaggle/antigravity/agent-skill-edd/skills/action_allowed/workflow_manager)**:
  ワークフローライブラリ内のワークフローの昇格・降格・一覧表示を管理します。
* **[workflow_evaluator](file:///d:/kaggle/antigravity/agent-skill-edd/skills/action_allowed/workflow_evaluator)**:
  AST（抽象構文木）解析により `run_agent.py` の実装コードから実行軌跡を静的に抽出し、許容される軌跡（EXACT / IN_ORDER / ANY_ORDER）と E2E 品質を検証します。

### 3. 連携エージェント (Orchestration Agents)
メタ操作を自動化するためのDAG定義済み連携エージェントです。
* **[skill_generation_agent](file:///workspace/agents/draft_only/skill_generation_agent)**:
  ライブラリの最低 Tier のパスを動的に取得し、その場所へ新しいスキルを自動生成します。
* **[skill_promotion_agent](file:///workspace/agents/draft_only/skill_promotion_agent)**:
  指定されたスキルの評価テストを実行し、合格した場合に上位 Tier へ自動昇格させます。
* **[agent_promotion_agent](file:///workspace/agents/draft_only/agent_promotion_agent)**:
  指定されたエージェントの軌跡および E2E 品質を自動評価し、合格した場合に上位 Tier へ自動昇格させます。

---

## 📈 Tier 概念とライフサイクル管理

品質管理の観点から、スキルおよびワークフローは以下の 3 つの Tier に分かれて管理され、評価エンジンの合格によってのみ上位 Tier へと遷移（昇格）します。

$$\mathbf{read\_only\ (初期/最低) \longrightarrow draft\_only\ (中間) \longrightarrow action\_allowed\ (最高)}$$

### Tier ごとの品質検証基準

| Tier | 対象 | 要求される評価パターン | 軌跡検証モード (ワークフロー) |
| :--- | :--- | :--- | :--- |
| **read_only** | 初期配置 / 最低 | UnitTest, LlmAsJudge | `ANY_ORDER` (順序制限なし部分一致) も許容 |
| **draft_only** | 中間レベル | UnitTest, GoldenDataset, LlmAsJudge | `IN_ORDER` / `EXACT` (厳しい順序一致) を要求 |
| **action_allowed** | 実行許可 / 最高 | UnitTest, GoldenDataset, LlmAsJudge, Adversarial, Canary | `IN_ORDER` / `EXACT` (厳しい順序一致) を要求 |

*※ GoldenDataset はテストケース20件以上、Adversarial/Canary は対話型環境（Human Review）での合格などを必要とします。自動テスト環境下では、一時的な環境変数（`MOCK_GOLDEN_DATASET=y` や `MOCK_HUMAN_REVIEW=y`）を付与することで検証をバイパス可能です。*

---

## 🛠️ 基本的な使用方法

### スキルの評価と昇格
`skill_evaluator` を使用して対象スキルを評価します。
```powershell
# スキルの品質評価を実行
python skills/action_allowed/skill_evaluator/scripts/evaluate_skill.py --skill skill_generator --target-tier draft_only

# 合格したスキルを昇格
python skills/action_allowed/skill_manager/scripts/manage_library.py promote --skill skill_generator --to draft_only
```

### ワークフローの評価と昇格
`workflow_evaluator` を使用して対象ワークフローの AST 実行軌跡と E2E 品質を評価します。
```powershell
# ワークフローの評価を実行
python skills/action_allowed/workflow_evaluator/scripts/evaluate_workflow.py --workflow skill_promotion_agent --target-tier draft_only

# 合格したワークフローを昇格
python skills/action_allowed/workflow_manager/scripts/manage_workflows.py promote --workflow skill_promotion_agent --to draft_only
```

### 自動昇格ワークフローの実行
連携ワークフローを用いて、評価から昇格までを一括で自動化します。
```powershell
# ワークフロー自動昇格連携エージェントを実行
python agents/run.py --workflow agents/draft_only/agent_promotion_agent/scripts/run_agent.py --input skill_generation_agent --output output.json
```
