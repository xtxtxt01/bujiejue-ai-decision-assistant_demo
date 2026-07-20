"""
社区案例服务 — 决策案例的查询、互动、用户贡献。
"""
import json
from datetime import datetime
from database import get_db


# 合法的纠结类型（用于参数校验）
VALID_CASE_TYPES = {"career", "relationship", "lifestyle", "finance", "education"}


def get_cases(case_type: str = "all", limit: int = 50, offset: int = 0) -> list[dict]:
    """
    获取案例列表（仅返回未删除的案例）。

    Args:
        case_type: 筛选类型，"all" 或具体类型
        limit: 返回数量上限
        offset: 分页偏移

    Returns:
        案例字典列表
    """
    conn = get_db()
    if case_type and case_type != "all":
        rows = conn.execute(
            """SELECT * FROM decision_cases
               WHERE is_deleted = 0 AND case_type = ?
               ORDER BY is_featured DESC, created_at DESC
               LIMIT ? OFFSET ?""",
            (case_type, limit, offset)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT * FROM decision_cases
               WHERE is_deleted = 0
               ORDER BY is_featured DESC, created_at DESC
               LIMIT ? OFFSET ?""",
            (limit, offset)
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def count_cases(case_type: str = "all") -> int:
    """统计案例数量（仅未删除）"""
    conn = get_db()
    if case_type and case_type != "all":
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM decision_cases WHERE is_deleted = 0 AND case_type = ?",
            (case_type,)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM decision_cases WHERE is_deleted = 0"
        ).fetchone()
    conn.close()
    return row["cnt"]


def add_empathy(case_id: int) -> int | None:
    """
    增加"我也是"共鸣数，返回新的计数。

    Returns:
        新的共鸣数，如果案例不存在则返回 None
    """
    conn = get_db()
    cursor = conn.execute(
        "UPDATE decision_cases SET empathy_count = empathy_count + 1 WHERE id = ? AND is_deleted = 0",
        (case_id,)
    )
    if cursor.rowcount == 0:
        conn.close()
        return None
    conn.commit()
    row = conn.execute(
        "SELECT empathy_count FROM decision_cases WHERE id = ?",
        (case_id,)
    ).fetchone()
    conn.close()
    return row["empathy_count"] if row else None


def add_view(case_id: int) -> bool:
    """增加浏览数，返回是否成功"""
    conn = get_db()
    cursor = conn.execute(
        "UPDATE decision_cases SET view_count = view_count + 1 WHERE id = ? AND is_deleted = 0",
        (case_id,)
    )
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def get_recommendations_for_card(card_id: str, limit: int = 3) -> list[dict]:
    """
    【纠结驱动】为某张纠结卡片推荐相似的社区案例。

    核心理念：从用户的具体纠结出发找参考，画像只做辅助加权。
    - 主导：卡片核心矛盾/关注点/标题 与 案例的关键词重叠
    - 辅助：用户决策风格、人生阶段匹配

    匹配流程：
    1. 读卡片，取 dilemma_type 作为案例类型过滤
    2. 纠结关键词来源：core_conflict 优先；为空时用 LLM 从对话兜底提取；
       再不行用 title
    3. 同类候选集（排除用户自己分享的案例）按打分排序
    4. 无同类型案例则返回空

    Args:
        card_id: 纠结卡片ID
        limit: 返回数量

    Returns:
        推荐案例列表（每条附带 _score 供调试）
    """
    conn = get_db()
    card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if not card:
        conn.close()
        return []
    card = dict(card)

    dilemma_type = (card.get("dilemma_type") or "").strip()
    if not dilemma_type:
        conn.close()
        return []

    # 读用户画像（辅助加权）
    user = conn.execute(
        "SELECT decision_style, life_stage FROM users WHERE uid = ?",
        (card["uid"],)
    ).fetchone()
    # 同类型候选案例
    rows = conn.execute(
        "SELECT * FROM decision_cases WHERE is_deleted = 0 AND case_type = ?",
        (dilemma_type,)
    ).fetchall()
    conn.close()

    candidates = [dict(r) for r in rows if r["source_card_id"] != card_id]
    if not candidates:
        return []

    # 纠结关键词：core_conflict 优先，为空时 LLM 兜底，再不行用 title
    conflict_text = card.get("core_conflict") or ""
    if not conflict_text:
        conflict_text = _extract_conflict_via_llm(card_id) or card.get("title") or ""

    card_tokens = (
        _tokens(conflict_text)
        | _tokens(card.get("main_concern"))
        | _tokens(card.get("title"))
    )

    # 画像辅助字段
    user_styles = set()
    user_stage = ""
    if user:
        user = dict(user)
        user_styles = set((user.get("decision_style") or "").split("_"))
        user_stage = user.get("life_stage") or ""

    def score(c: dict) -> float:
        s = 0.0
        # 纠结匹配（主导，权重 2）
        s += 2 * len(card_tokens & _tokens(c.get("core_conflict")))
        s += 2 * len(card_tokens & _tokens(c.get("tags")))
        # 画像加权（辅助）
        if user_styles and c.get("decision_style") in user_styles:
            s += 1
        if user_stage and c.get("life_stage") == user_stage:
            s += 0.5
        return s

    candidates.sort(key=lambda c: (score(c), c.get("retrospect_score", 0)), reverse=True)

    result = []
    for c in candidates[:limit]:
        c["_score"] = score(c)
        result.append(c)
    return result


def _extract_conflict_via_llm(card_id: str) -> str:
    """
    卡片还没聊出 core_conflict 时，用 LLM 从对话里提取一句核心矛盾。
    失败返回空字符串（调用方会降级用 title）。
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE card_id = ? ORDER BY created_at ASC LIMIT 12",
        (card_id,)
    ).fetchall()
    conn.close()

    if not rows:
        return ""

    conversation = "\n".join(f"{r['role']}: {r['content']}" for r in rows)
    prompt = (
        "下面是一段用户的纠结对话。请用一句话（15字内）概括用户的核心矛盾，"
        "格式如\"成长 vs 稳定\"。只返回这句话，不要其他内容。\n\n"
        f"{conversation}"
    )
    try:
        from clients.llm_client import call_llm
        result = call_llm([{"role": "user", "content": prompt}])
        return (result or "").strip()[:30]
    except Exception as e:
        print(f"[Case] _extract_conflict_via_llm failed: {e}")
        return ""


# ============ 用户贡献 + AI 脱敏 ============

def _calc_duration_days(created_at: str, closed_at: str) -> int:
    """计算从创建到关闭的天数，至少为 1"""
    if not created_at or not closed_at:
        return 1
    try:
        start = datetime.fromisoformat(created_at)
        end = datetime.fromisoformat(closed_at)
        return max((end - start).days, 1)
    except (ValueError, TypeError):
        return 1


def _fallback_preview(card: dict) -> dict:
    """LLM 脱敏失败时的降级预览（基于卡片已有字段，不含对话细节）"""
    return {
        "title": card.get("title") or "我的一次决策",
        "background": "（请补充背景，已隐藏敏感信息）",
        "core_conflict": card.get("core_conflict") or "",
        "final_choice": card.get("decision_result") or "已做决定",
        "turning_point": "（请补充你想通的关键点）",
        "tags": "",
    }


def build_case_preview(card_id: str, retrospect_score: int, retrospect_text: str) -> dict | None:
    """
    生成脱敏后的案例预览（不入库）。

    读取卡片 + 对话 + 用户画像，调用 LLM 脱敏成结构化案例。
    LLM 失败时降级为基于卡片字段的简单预览。

    Returns:
        预览 dict（含 case_type/duration_days/decision_style/life_stage/
        retrospect_score/retrospect/retrospect_months 等完整字段），
        卡片不存在则返回 None
    """
    from clients.llm_client import call_llm_json
    from prompts.templates import CASE_DESENSITIZE

    conn = get_db()
    card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if not card:
        conn.close()
        return None
    card = dict(card)

    # 读对话（控制长度，最多取最近 30 条避免 prompt 过长）
    msg_rows = conn.execute(
        "SELECT role, content FROM messages WHERE card_id = ? ORDER BY created_at ASC",
        (card_id,)
    ).fetchall()
    # 读用户画像（决策风格、人生阶段用于匹配维度）
    user = conn.execute(
        "SELECT decision_style, life_stage FROM users WHERE uid = ?",
        (card["uid"],)
    ).fetchone()
    conn.close()

    messages = [dict(m) for m in msg_rows][-30:]
    conversation = "\n".join(f"{m['role']}: {m['content']}" for m in messages)

    # 调 LLM 脱敏
    desensitized = None
    try:
        prompt = CASE_DESENSITIZE.format(
            title=card.get("title", ""),
            core_conflict=card.get("core_conflict", ""),
            trigger_event=card.get("trigger_event", ""),
            decision_result=card.get("decision_result", ""),
            conversation=conversation,
            score=retrospect_score,
            retrospect=retrospect_text,
        )
        raw = call_llm_json([{"role": "user", "content": prompt}])
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        desensitized = json.loads(raw)
    except Exception as e:
        print(f"[Case] 脱敏失败，降级处理: {e}")

    if not desensitized or "core_conflict" not in desensitized:
        desensitized = _fallback_preview(card)

    # 决策风格：组合型取主风格
    style = (user["decision_style"] if user else "") or ""
    if "_" in style:
        style = style.split("_")[0]

    # 合并非 LLM 字段
    preview = {
        "case_type": card.get("dilemma_type") or "career",
        "title": desensitized.get("title", ""),
        "background": desensitized.get("background", ""),
        "core_conflict": desensitized.get("core_conflict", ""),
        "duration_days": _calc_duration_days(card.get("created_at"), card.get("closed_at")),
        "final_choice": desensitized.get("final_choice", ""),
        "turning_point": desensitized.get("turning_point", ""),
        "retrospect": retrospect_text,
        "retrospect_score": retrospect_score,
        "retrospect_months": 3,
        "decision_style": style,
        "life_stage": (user["life_stage"] if user else "") or "",
        "tags": desensitized.get("tags", ""),
    }
    return preview


def publish_case(card_id: str, case_data: dict) -> int | None:
    """
    将用户编辑确认后的案例写入社区，并回写 cards.shared_case_id 防重复。

    Returns:
        新案例 id；若卡片不存在或已分享则返回 None
    """
    conn = get_db()
    card = conn.execute("SELECT shared_case_id FROM cards WHERE id = ?", (card_id,)).fetchone()
    if not card:
        conn.close()
        return None
    if card["shared_case_id"]:
        conn.close()
        return None  # 已分享过，防重复

    # 校验类型，兜底为 career
    case_type = case_data.get("case_type")
    if case_type not in VALID_CASE_TYPES:
        case_type = "career"

    # 校验满意度范围
    try:
        score = int(case_data.get("retrospect_score", 5))
    except (ValueError, TypeError):
        score = 5
    score = max(1, min(10, score))

    duration = case_data.get("duration_days", 1)
    try:
        duration = max(1, int(duration))
    except (ValueError, TypeError):
        duration = 1

    cursor = conn.execute(
        """INSERT INTO decision_cases (
            case_type, title, background, core_conflict, duration_days,
            final_choice, turning_point, retrospect, retrospect_score,
            retrospect_months, decision_style, life_stage, tags,
            is_user_contributed, source_card_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
        (
            case_type,
            case_data.get("title", ""),
            case_data.get("background", ""),
            case_data.get("core_conflict", ""),
            duration,
            case_data.get("final_choice", ""),
            case_data.get("turning_point", ""),
            case_data.get("retrospect", ""),
            score,
            case_data.get("retrospect_months", 3),
            case_data.get("decision_style", ""),
            case_data.get("life_stage", ""),
            case_data.get("tags", ""),
            card_id,
        )
    )
    new_id = cursor.lastrowid
    # 回写卡片防重复
    conn.execute(
        "UPDATE cards SET shared_case_id = ? WHERE id = ?",
        (new_id, card_id)
    )
    conn.commit()
    conn.close()
    return new_id


# ============ 对话中案例引入（功能④） ============

# 中文停用词（避免用无意义词做关键词匹配）
_STOPWORDS = {"vs", "和", "还是", "的", "了", "与", "或", "是", "在", "我", "你", "他"}


def _tokens(text: str) -> set[str]:
    """把核心矛盾切成关键词集合：先按分隔符切，再补 2-gram，过滤停用词"""
    if not text:
        return set()
    import re
    # 按非中英数字符切分
    parts = [p for p in re.split(r"[\s,，。.|/、]+", str(text)) if p]
    toks = set()
    for p in parts:
        if p in _STOPWORDS:
            continue
        if len(p) <= 6:
            toks.add(p)
        # 对长词补 2-gram，提升中文重叠命中率
        for i in range(len(p) - 1):
            bigram = p[i:i+2]
            if bigram not in _STOPWORDS:
                toks.add(bigram)
    return toks


def find_related_case(card: dict, exclude_card_id: str = None) -> dict | None:
    """
    为当前纠结卡片找一条最相关的社区案例。

    匹配逻辑：
    1. 同 case_type（dilemma_type）优先
    2. 在同类中按 core_conflict 关键词重叠度排序，取最高
    3. 排除用户自己分享的案例（source_card_id == 当前卡片）
    4. 重叠度为 0 时，降级取该类型满意度最高的一条

    Returns:
        最相关案例 dict，无任何同类案例则返回 None
    """
    dilemma_type = (card.get("dilemma_type") or "").strip()
    if not dilemma_type:
        return None

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM decision_cases WHERE is_deleted = 0 AND case_type = ?",
        (dilemma_type,)
    ).fetchall()
    conn.close()

    candidates = [dict(r) for r in rows]
    # 排除自己分享的
    if exclude_card_id:
        candidates = [c for c in candidates if c.get("source_card_id") != exclude_card_id]
    if not candidates:
        return None

    card_tokens = _tokens(card.get("core_conflict", "")) | _tokens(card.get("title", ""))

    def overlap(c: dict) -> int:
        return len(card_tokens & _tokens(c.get("core_conflict", "")))

    # 按 (关键词重叠, 满意度) 降序
    candidates.sort(key=lambda c: (overlap(c), c.get("retrospect_score", 0)), reverse=True)
    return candidates[0]
