from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List

from clients.memory_client import query_memories, delete_memories, upsert_core_memory, get_user_profile_memory
from services.user_service import get_user

router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.get("")
def list_memories(uid: str = Query(...), type: str = Query("episode"), limit: int = Query(20)):
    memories = query_memories(uid, type, limit)

    # core 类型：如果远程记忆为空，从本地数据库生成档案
    if type == "core" and not memories:
        memories = _build_local_core_profile(uid)

    return {"memories": memories, "type": type}


def _build_local_core_profile(uid: str) -> list[dict]:
    """从本地 users 表构建核心档案条目，作为 Memosyne 不可用时的 fallback"""
    user = get_user(uid)
    if not user:
        return []

    style_map = {
        "rational": "理性分析型", "intuitive": "直觉感知型",
        "dependent": "参考借鉴型", "avoidant": "审慎观望型",
        "spontaneous": "果断行动型",
    }
    max_map = {
        "maximizer": "追求最优型", "satisficer": "务实满意型", "mixed": "灵活权衡型",
    }
    stage_map = {
        "student": "在读学生", "early_career": "刚入职场（0-3年）",
        "mid_career": "职场中期（3-10年）", "senior": "资深职场人/管理层",
        "freelance": "自由职业/创业中", "transition": "正在转型/找方向",
        "gap_year": "间隔期/休息调整中", "homemaker": "全职在家", "other": "其他",
    }
    dilemma_map = {
        "career": "工作与职业发展", "relationship": "感情与人际关系",
        "lifestyle": "生活方式选择", "finance": "消费与财务决策",
        "growth": "个人成长与方向", "education": "学业与升学",
    }

    items = []
    if user.get("decision_style"):
        ds = user["decision_style"]
        if ds in style_map:
            label = style_map[ds]
        elif "_" in ds:
            parts = ds.split("_")
            label = " + ".join(style_map.get(p, p) for p in parts)
        else:
            label = ds
        items.append({"content": f"决策风格：{label}", "tags": ["profile", "decision_style"]})
    if user.get("maximizer_tendency"):
        label = max_map.get(user["maximizer_tendency"], user["maximizer_tendency"])
        items.append({"content": f"决策倾向：{label}", "tags": ["profile", "maximizer"]})
    if user.get("mbti") and user["mbti"] != "unknown":
        items.append({"content": f"MBTI：{user['mbti']}", "tags": ["profile", "personality"]})
    if user.get("life_stage"):
        label = stage_map.get(user["life_stage"], user["life_stage"])
        items.append({"content": f"人生阶段：{label}", "tags": ["profile", "life_stage"]})
    if user.get("frequent_dilemma_types"):
        types_str = user["frequent_dilemma_types"]
        labels = [dilemma_map.get(t.strip(), t.strip()) for t in types_str.split(",") if t.strip()]
        items.append({"content": f"关注领域：{'、'.join(labels)}", "tags": ["profile", "dilemma_types"]})
    if user.get("values_ranking"):
        vals = user["values_ranking"].replace(">", "、")
        items.append({"content": f"价值观排序：{vals}", "tags": ["profile", "values"]})
    if user.get("self_intro"):
        items.append({"content": f"自我介绍：{user['self_intro']}", "tags": ["profile", "self_intro"]})

    return items


class DeleteRequest(BaseModel):
    uid: str
    type: str
    memory_ids: List[str]


@router.delete("")
def delete_memory(req: DeleteRequest):
    ok = delete_memories(req.uid, req.type, req.memory_ids)
    if not ok:
        raise HTTPException(status_code=500, detail="删除失败")
    return {"ok": True}


class UpdateCoreRequest(BaseModel):
    uid: str
    items: List[dict]


@router.put("/core")
def update_core_memory(req: UpdateCoreRequest):
    # 1. 尝试写入远程 Memosyne（可能失败但不影响本地）
    upsert_core_memory(req.uid, req.items)

    # 2. 同步更新本地 users 表（保证AI回复能读到最新档案）
    _sync_core_to_local_db(req.uid, req.items)

    return {"ok": True}


def _sync_core_to_local_db(uid: str, items: list[dict]):
    """将编辑后的core记忆同步到本地users表"""
    from services.user_service import update_user

    updates = {}
    for item in items:
        content = item.get("content", "")
        tags = item.get("tags", [])

        if "decision_style" in tags:
            # "决策风格：审慎观望型" → 提取值
            val = _extract_value(content, "决策风格")
            if val:
                updates["decision_style"] = _reverse_style_map(val)
        elif "maximizer" in tags:
            val = _extract_value(content, "决策倾向")
            if val:
                updates["maximizer_tendency"] = _reverse_maximizer_map(val)
        elif "personality" in tags:
            val = _extract_value(content, "MBTI")
            if val:
                updates["mbti"] = val.upper().strip()
        elif "life_stage" in tags:
            val = _extract_value(content, "人生阶段")
            if val:
                updates["life_stage"] = _reverse_stage_map(val)
        elif "values" in tags:
            val = _extract_value(content, "价值观排序")
            if val:
                updates["values_ranking"] = val
        elif "self_intro" in tags:
            val = _extract_value(content, "自我介绍")
            if val:
                updates["self_intro"] = val

    if updates:
        update_user(uid, **updates)


def _extract_value(content: str, prefix: str) -> str:
    """从 '前缀：值' 格式中提取值"""
    if "：" in content:
        parts = content.split("：", 1)
        if parts[0].strip() == prefix:
            return parts[1].strip()
    if ":" in content:
        parts = content.split(":", 1)
        if parts[0].strip() == prefix:
            return parts[1].strip()
    return ""


def _reverse_style_map(label: str) -> str:
    """中文标签 → 数据库字段值"""
    mapping = {
        "理性分析型": "rational",
        "直觉感知型": "intuitive",
        "参考借鉴型": "dependent",
        "审慎观望型": "avoidant",
        "果断行动型": "spontaneous",
    }
    return mapping.get(label, label)


def _reverse_maximizer_map(label: str) -> str:
    mapping = {
        "追求最优型": "maximizer",
        "务实满意型": "satisficer",
        "灵活权衡型": "mixed",
    }
    return mapping.get(label, label)


def _reverse_stage_map(label: str) -> str:
    mapping = {
        "在读学生": "student",
        "刚入职场（0-3年）": "early_career",
        "职场中期（3-10年）": "mid_career",
        "资深职场人/管理层": "senior",
        "自由职业/创业中": "freelance",
        "正在转型/找方向": "transition",
        "间隔期/休息调整中": "gap_year",
        "全职在家": "homemaker",
        "其他": "other",
    }
    return mapping.get(label, label)
