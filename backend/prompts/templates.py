"""
Prompt 文件加载工具
"""
import os

PROMPTS_DIR = os.path.dirname(__file__)


def load_prompt(filename: str) -> str:
    """从 prompts/ 目录加载 prompt 文件内容"""
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# 加载所有 prompt 模板
BASE_ROLE = load_prompt("base_role.txt")
STAGE_CLARIFYING = load_prompt("stage_clarifying.txt")
STAGE_EXPLORING = load_prompt("stage_exploring.txt")
STAGE_ADVISING = load_prompt("stage_advising.txt")
STAGE_CLOSING = load_prompt("stage_closing.txt")
CARD_EXTRACT = load_prompt("card_extract.txt")
MEMORY_SUMMARY = load_prompt("memory_summary.txt")
CHECK_READY_FOR_ADVICE = load_prompt("check_ready_for_advice.txt")
INSIGHT_EXTRACT = load_prompt("insight_extract.txt")
CASE_DESENSITIZE = load_prompt("case_desensitize.txt")
VALUE_CONFLICT_CHECK = load_prompt("value_conflict_check.txt")

