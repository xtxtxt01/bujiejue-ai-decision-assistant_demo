"""
用户服务 — 建档和档案管理。
"""
import uuid
from datetime import datetime
from database import get_db
from clients.memory_client import upsert_core_memory


def create_user(uid: str = None, username: str = None, password_hash: str = None,
                nickname: str = "", mbti: str = "", decision_style: str = "",
                maximizer_tendency: str = "",
                values_ranking: list[str] = [], life_stage: str = "",
                frequent_dilemma_types: list[str] = [],
                interests: list[str] = [],
                self_intro: str = "", theme: str = "default") -> str:
    """创建用户，返回 uid"""
    if not uid:
        uid = str(uuid.uuid4())[:8]

    conn = get_db()
    conn.execute(
        """INSERT INTO users (uid, username, password_hash, nickname, mbti, decision_style,
           maximizer_tendency, values_ranking, life_stage, frequent_dilemma_types,
           self_intro, theme, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (uid, username, password_hash, nickname, mbti, decision_style,
         maximizer_tendency,
         ">".join(values_ranking),
         life_stage,
         ",".join(frequent_dilemma_types),
         self_intro,
         theme,
         datetime.now().isoformat(),
         datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    _store_profile_as_core_memory(uid, mbti, decision_style, maximizer_tendency,
                                  values_ranking, life_stage, frequent_dilemma_types, self_intro)
    return uid


def _store_profile_as_core_memory(uid: str, mbti: str, decision_style: str,
                                   maximizer_tendency: str,
                                   values_ranking: list[str], life_stage: str,
                                   frequent_dilemma_types: list[str], self_intro: str):
    """将注册信息写入 Memosyne core 记忆，失败不影响注册流程"""
    style_map = {
        "rational": "理性分析型",
        "intuitive": "直觉感知型",
        "dependent": "参考借鉴型",
        "avoidant": "审慎观望型",
        "spontaneous": "果断行动型",
    }
    maximizer_map = {
        "maximizer": "追求最优型",
        "satisficer": "务实满意型",
        "mixed": "灵活权衡型",
    }
    life_stage_map = {
        "student": "在读学生",
        "early_career": "刚入职场（0-3年）",
        "mid_career": "职场中期（3-10年）",
        "senior": "资深职场人/管理层",
        "freelance": "自由职业/创业中",
        "transition": "正在转型/找方向",
        "gap_year": "间隔期/休息调整中",
        "homemaker": "全职在家",
        "other": "其他",
    }
    dilemma_map = {
        "career": "工作与职业发展",
        "relationship": "感情与人际关系",
        "lifestyle": "生活方式选择",
        "finance": "消费与财务决策",
        "growth": "个人成长与方向",
        "education": "学业与升学",
    }

    core_items = []
    if mbti and mbti != "unknown":
        core_items.append({"content": f"MBTI类型：{mbti}", "tags": ["profile", "personality"]})
    if decision_style:
        label = style_map.get(decision_style, decision_style)
        core_items.append({"content": f"决策风格：{label}", "tags": ["profile", "decision_style"]})
    if maximizer_tendency:
        label = maximizer_map.get(maximizer_tendency, maximizer_tendency)
        core_items.append({"content": f"最大化倾向：{label}", "tags": ["profile", "maximizer"]})
    if values_ranking:
        core_items.append({"content": f"价值观排序：{'、'.join(values_ranking)}", "tags": ["profile", "values"]})
    if life_stage:
        label = life_stage_map.get(life_stage, life_stage)
        core_items.append({"content": f"人生阶段：{label}", "tags": ["profile", "life_stage"]})
    if frequent_dilemma_types:
        labels = [dilemma_map.get(t, t) for t in frequent_dilemma_types]
        core_items.append({"content": f"常见纠结类型：{'、'.join(labels)}", "tags": ["profile", "dilemma_types"]})
    if self_intro:
        core_items.append({"content": f"用户自我介绍：{self_intro}", "tags": ["profile", "self_intro"]})

    if core_items:
        try:
            upsert_core_memory(uid, core_items)
        except Exception as e:
            print(f"[Memory] Failed to store core memory for uid={uid}: {e}")


def get_user(uid: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE uid = ?", (uid,)).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def update_user(uid: str, **kwargs) -> bool:
    allowed_columns = {
        "username", "password_hash", "nickname", "mbti", "decision_style",
        "maximizer_tendency", "values_ranking", "life_stage",
        "frequent_dilemma_types", "self_intro", "theme",
    }
    conn = get_db()
    sets = []
    values = []
    for key, val in kwargs.items():
        if key not in allowed_columns:
            continue
        if val is not None:
            if isinstance(val, list):
                val = ",".join(val) if key != "values_ranking" else ">".join(val)
            elif key == "values_ranking" and isinstance(val, str):
                val = _normalize_values_ranking(val)
            sets.append(f"{key} = ?")
            values.append(val)
    if not sets:
        conn.close()
        return False
    sets.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(uid)
    conn.execute(f"UPDATE users SET {', '.join(sets)} WHERE uid = ?", values)
    conn.commit()
    conn.close()
    return True


def _normalize_values_ranking(value: str) -> str:
    """统一价值观排序的存储分隔符，兼容编辑页返回的中文顿号/逗号。"""
    import re

    parts = [p.strip() for p in re.split(r"[>、,，]+", value) if p.strip()]
    return ">".join(parts)
