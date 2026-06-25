import os
from google.adk.skills import load_skill_from_dir
from google.adk.tools import skill_toolset

TIERS = ["draft_only", "read_only", "action_allowed"]

def load_skills_from_library(max_tier="action_allowed", base_dir="./skills"):
    """
    指定された max_tier 以下のすべてのスキルをロードしてリストで返します。
    
    Args:
        max_tier (str): ロードする最大のTierレベル ('draft_only', 'read_only', 'action_allowed')
        base_dir (str): スキルライブラリのベースディレクトリ
        
    Returns:
        list: ロードされたSkillオブジェクトのリスト
    """
    skills = []
    if max_tier not in TIERS:
        raise ValueError(f"Invalid max_tier '{max_tier}'. Choose from {TIERS}")
        
    # 指定された max_tier 以下のTierのリストを取得
    allowed_tiers = TIERS[:TIERS.index(max_tier) + 1]
    
    for tier in allowed_tiers:
        tier_dir = os.path.join(base_dir, tier)
        if not os.path.exists(tier_dir):
            continue
        # サブディレクトリを探索してスキルをロード
        for item in os.listdir(tier_dir):
            item_path = os.path.join(tier_dir, item)
            if os.path.isdir(item_path):
                skill_md_path = os.path.join(item_path, "SKILL.md")
                if os.path.exists(skill_md_path):
                    try:
                        skill = load_skill_from_dir(item_path)
                        skills.append(skill)
                    except Exception as e:
                        print(f"Warning: Failed to load skill from '{item_path}': {e}")
    return skills

def get_library_toolset(max_tier="action_allowed", additional_tools=None, base_dir="./skills"):
    """
    指定された max_tier 以下のスキルと、追加のツール群を統合した SkillToolset を作成します。
    エージェント起動時にこれを tools に指定します。
    
    Args:
        max_tier (str): ロードする最大のTierレベル
        additional_tools (list): スキルとは別に追加するカスタム関数のリスト
        base_dir (str): スキルライブラリのベースディレクトリ
        
    Returns:
        SkillToolset: エージェントに渡すためのツールセットオブジェクト
    """
    skills = load_skills_from_library(max_tier, base_dir)
    return skill_toolset.SkillToolset(
        skills=skills,
        additional_tools=additional_tools or []
    )
