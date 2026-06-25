---
name: {{skill_name}}
description: |
  {{description_summary}}
  Use when the user asks to {{trigger_actions}}.
  Do NOT use for {{anti_trigger_actions}}.
version: 1.0.0
license: MIT
allowed-tools:
  - {{allowed_tools}}
metadata:
  author: {{author}}
---

# {{title}}

## When to use
- {{when_to_use_scenario_1}}
- {{when_to_use_scenario_2}}

## When NOT to use
- {{when_not_to_use_scenario_1}}
- {{when_not_to_use_scenario_2}}

## Workflow
1. {{workflow_step_1}}
2. {{workflow_step_2}}
3. See `references/advanced.md` for {{edge_case_handling}}.

## Examples
- Input: "{{example_input_1}}"
  Output: "{{example_output_1}}"

## Output format
- {{output_format_requirements}}

## Anti-patterns to avoid
- {{anti_pattern_1}}
