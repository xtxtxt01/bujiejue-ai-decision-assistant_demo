"""
卡片服务 — 纠结卡片的 CRUD 和状态管理。
"""
import uuid
from datetime import datetime
from database import get_db


def create_card(uid: str, dilemma_type: str, initial_input: str) -> str:
    """创建纠结卡片，返回 card_id"""
    card_id = str(uuid.uuid4())[:8]
    conn = get_db()
    conn.execute(
        """INSERT INTO cards (id, uid, dilemma_type, status, created_at, updated_at)
           VALUES (?, ?, ?, 'active', ?, ?)""",
        (card_id, uid, dilemma_type, datetime.now().isoformat(), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return card_id


def get_card(card_id: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def get_user_cards(uid: str) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM cards WHERE uid = ? ORDER BY updated_at DESC",
        (uid,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_user_insights(uid: str) -> list[dict]:
    """
    获取用户所有已生成 Insight 的卡片（用于 Insight Gallery 展示）。
    只返回已关闭且 insight 非空的卡片，按关闭时间倒序。
    """
    import json

    conn = get_db()
    rows = conn.execute(
        """SELECT id, title, dilemma_type, status, insight,
                  created_at, closed_at, updated_at
           FROM cards
           WHERE uid = ? AND insight IS NOT NULL AND insight != ''
           ORDER BY COALESCE(closed_at, updated_at) DESC""",
        (uid,)
    ).fetchall()
    conn.close()

    results = []
    for row in rows:
        card = dict(row)
        # 解析 insight JSON 字符串
        try:
            card["insight"] = json.loads(card["insight"])
        except (json.JSONDecodeError, TypeError):
            continue  # insight 格式损坏则跳过

        # 计算纠结时长（天数）
        card["duration_days"] = _calc_duration_days(card.get("created_at"), card.get("closed_at"))
        results.append(card)

    return results


def _calc_duration_days(created_at: str, closed_at: str) -> int:
    """计算从创建到关闭的天数，至少为 1"""
    if not created_at or not closed_at:
        return 1
    try:
        start = datetime.fromisoformat(created_at)
        end = datetime.fromisoformat(closed_at)
        days = (end - start).days
        return max(days, 1)
    except (ValueError, TypeError):
        return 1


def close_card(card_id: str, status: str, decision_result: str = "", decision_reason: str = "") -> bool:
    """关闭卡片。status: 'decided' 或 'shelved'"""
    if status not in ("decided", "shelved"):
        return False

    conn = get_db()

    # 获取用户ID
    card = conn.execute("SELECT uid FROM cards WHERE id = ?", (card_id,)).fetchone()
    if not card:
        conn.close()
        return False

    # 更新卡片状态
    conn.execute(
        """UPDATE cards SET status = ?, decision_result = ?, decision_reason = ?,
           closed_at = ?, updated_at = ? WHERE id = ?""",
        (status, decision_result, decision_reason,
         datetime.now().isoformat(), datetime.now().isoformat(), card_id)
    )
    conn.commit()
    conn.close()

    # 卡片关闭时提取全量对话记忆
    # API 会自动增量更新，只对新增内容进行提取
    try:
        all_messages = _get_all_card_messages(card_id)
        if all_messages:
            from clients.memory_client import extract_and_store_memories
            extract_and_store_memories(card['uid'], card_id, all_messages)
            print(f"[Memory] Extracted complete conversation on card close ({len(all_messages)} messages)")
    except Exception as e:
        print(f"[Memory] Failed to extract on card close: {e}")

    return True


def _get_all_card_messages(card_id: str) -> list[dict]:
    """获取卡片的所有消息（用于关闭时全量提取）"""
    conn = get_db()
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE card_id = ? ORDER BY created_at ASC",
        (card_id,)
    ).fetchall()
    conn.close()
    return [{"role": row["role"], "content": row["content"]} for row in rows]


def reopen_card(card_id: str) -> bool:
    """重新打开已关闭的卡片，将状态改回 active"""
    conn = get_db()
    conn.execute(
        """UPDATE cards SET status = 'active', closed_at = NULL, updated_at = ?
           WHERE id = ?""",
        (datetime.now().isoformat(), card_id)
    )
    conn.commit()
    conn.close()
    return True
