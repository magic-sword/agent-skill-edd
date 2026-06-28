import os
# snake_case のスキル名を許可するために ADK の feature flag を設定
os.environ["ADK_ENABLE_SNAKE_CASE_SKILL_NAME"] = "True"

from google.adk.skills import load_skill_from_dir
from google.adk.tools import skill_toolset

TIERS = ["read_only", "draft_only", "action_allowed"]

def load_skills_from_library(min_tier="read_only", base_dir="./skills"):
    """
    指定された min_tier 以上のすべてのスキルをロードしてリストで返します。
    
    Args:
        min_tier (str): ロードする最小のTierレベル ('read_only', 'draft_only', 'action_allowed')
        base_dir (str): スキルライブラリのベースディレクトリ
        
    Returns:
        list: ロードされたSkillオブジェクトのリスト
    """
    skills = []
    if min_tier not in TIERS:
        raise ValueError(f"Invalid min_tier '{min_tier}'. Choose from {TIERS}")
        
    # 指定された min_tier 以上のTierのリストを取得
    allowed_tiers = TIERS[TIERS.index(min_tier):]
    
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

def load_required_skills_from_library(required_names, min_tier="read_only", base_dir="./skills"):
    """
    指定された min_tier 以上のすべてのスキルから、required_names（識別名のリスト）に一致するスキルのみをロードして返します。
    
    Args:
        required_names (list[str]): ロードするスキルの固有識別名（フォルダ名または name）のリスト
        min_tier (str): ロードする最小のTierレベル
        base_dir (str): スキルライブラリのベースディレクトリ
        
    Returns:
        list: ロードされたSkillオブジェクトのリスト
    """
    skills = []
    if min_tier not in TIERS:
        raise ValueError(f"Invalid min_tier '{min_tier}'. Choose from {TIERS}")
        
    allowed_tiers = TIERS[TIERS.index(min_tier):]
    normalized_required = {name.replace("_", "-") for name in required_names}
    
    for tier in allowed_tiers:
        tier_dir = os.path.join(base_dir, tier)
        if not os.path.exists(tier_dir):
            continue
        for item in os.listdir(tier_dir):
            item_path = os.path.join(tier_dir, item)
            if os.path.isdir(item_path):
                normalized_item = item.replace("_", "-")
                
                skill_md_path = os.path.join(item_path, "SKILL.md")
                if os.path.exists(skill_md_path):
                    try:
                        skill = None
                        if normalized_item in normalized_required:
                            skill = load_skill_from_dir(item_path)
                        else:
                            temp_skill = load_skill_from_dir(item_path)
                            if temp_skill.name.replace("_", "-") in normalized_required:
                                skill = temp_skill
                        
                        if skill:
                            skills.append(skill)
                    except Exception as e:
                        print(f"Warning: Failed to load skill from '{item_path}': {e}")
    return skills

def get_library_toolset(min_tier="read_only", additional_tools=None, base_dir="./skills"):
    """
    指定された min_tier 以上のスキルと、追加のツール群を統合した SkillToolset を作成します。
    エージェント起動時にこれを tools に指定します。
    
    Args:
        min_tier (str): ロードする最小のTierレベル
        additional_tools (list): スキルとは別に追加するカスタム関数のリスト
        base_dir (str): スキルライブラリのベースディレクトリ
        
    Returns:
        SkillToolset: エージェントに渡すためのツールセットオブジェクト
    """
    skills = load_skills_from_library(min_tier, base_dir)
    return skill_toolset.SkillToolset(
        skills=skills,
        additional_tools=additional_tools or []
    )

def get_library_toolset_for_workflow(required_names, min_tier="read_only", additional_tools=None, base_dir="./skills"):
    """
    指定された min_tier 以上のスキル群から必要なものを取得し、追加のツール群と統合した SkillToolset を作成します。
    
    Args:
        required_names (list[str]): 必要なスキルの固有識別名のリスト
        min_tier (str): ロードする最小のTierレベル
        additional_tools (list): スキルとは別に追加するカスタム関数のリスト
        base_dir (str): スキルライブラリのベースディレクトリ
        
    Returns:
        SkillToolset: エージェントに渡すためのツールセットオブジェクト
    """
    skills = load_required_skills_from_library(required_names, min_tier, base_dir)
    return skill_toolset.SkillToolset(
        skills=skills,
        additional_tools=additional_tools or []
    )
