from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from services.card_service import create_card, get_card, get_user_cards, close_card, reopen_card, get_user_insights
from services.case_service import build_case_preview, publish_case
from services.chat_service import chat, save_message, get_card_messages, generate_insight


router = APIRouter(prefix="/api/cards", tags=["cards"])


class CreateCardRequest(BaseModel):
    uid: str
    dilemma_type: str
    initial_input: str
    trigger_event: str = ""
    feared_outcome: str = ""


class ChatRequest(BaseModel):
    uid: str
    message: str


class CloseCardRequest(BaseModel):
    uid: str
    status: str  # "decided" or "shelved"
    decision_result: str = ""
    decision_reason: str = ""


class SharePreviewRequest(BaseModel):
    retrospect_score: int
    retrospect_text: str


class ShareConfirmRequest(BaseModel):
    case_data: dict


@router.post("")
def create(req: CreateCardRequest, background_tasks: BackgroundTasks):
    parts = []
    if req.initial_input:
        parts.append(req.initial_input)
    if req.trigger_event:
        parts.append(f"触发事件：{req.trigger_event}")
    if req.feared_outcome:
        parts.append(f"最担心的后果：{req.feared_outcome}")
    structured_input = "\n".join(parts)

    card_id = create_card(uid=req.uid, dilemma_type=req.dilemma_type, initial_input=structured_input)
    result = chat(uid=req.uid, card_id=card_id, user_message=structured_input, background_tasks=background_tasks)
    return {
        "card_id": card_id,
        "assistant_message": result["assistant_message"],
        "progress_hint": result.get("progress_hint"),
        "stage": result["stage"],
    }


@router.get("")
def list_cards(uid: str):
    cards = get_user_cards(uid)
    return {"cards": cards}


@router.get("/insights")
def list_insights(uid: str):
    """获取用户所有已生成 Insight 的卡片（Insight Gallery）"""
    insights = get_user_insights(uid)
    return {"insights": insights}


@router.get("/{card_id}")
def detail(card_id: str):
    card = get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")
    messages = get_card_messages(card_id)
    return {"card": card, "messages": messages}


@router.post("/{card_id}/chat")
def chat_in_card(card_id: str, req: ChatRequest, background_tasks: BackgroundTasks):
    card = get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")
    result = chat(uid=req.uid, card_id=card_id, user_message=req.message, background_tasks=background_tasks)
    return {
        "assistant_message": result["assistant_message"],
        "progress_hint": result.get("progress_hint"),
        "stage": result.get("stage"),
        "card_updated": result.get("card_updated", False),
        "card_info": result.get("card_info"),
        "card_closed": result.get("card_closed", False),
        "value_conflict_hint": result.get("value_conflict_hint"),
        "related_case": result.get("related_case"),
    }


@router.put("/{card_id}/close")
def close(card_id: str, req: CloseCardRequest, background_tasks: BackgroundTasks):
    card = get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")
    success = close_card(card_id, status=req.status,
                         decision_result=req.decision_result,
                         decision_reason=req.decision_reason)
    if not success:
        raise HTTPException(status_code=400, detail="状态必须为 decided 或 shelved")

    # 关闭卡片后，后台任务生成 Insight
    background_tasks.add_task(generate_insight, card_id)

    return {"message": "卡片已关闭"}


@router.put("/{card_id}/reopen")
def reopen(card_id: str):
    card = get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")
    if card["status"] == "active":
        raise HTTPException(status_code=400, detail="卡片已经是活跃状态")
    reopen_card(card_id)
    return {"message": "卡片已重新打开"}


@router.post("/{card_id}/share/preview")
def share_preview(card_id: str, req: SharePreviewRequest):
    """生成脱敏后的案例预览（不入库）"""
    card = get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")
    if card.get("shared_case_id"):
        raise HTTPException(status_code=400, detail="该卡片已分享过")
    score = max(1, min(10, req.retrospect_score))
    preview = build_case_preview(card_id, score, req.retrospect_text)
    if preview is None:
        raise HTTPException(status_code=404, detail="卡片不存在")
    return {"preview": preview}


@router.post("/{card_id}/share/confirm")
def share_confirm(card_id: str, req: ShareConfirmRequest):
    """确认发布案例到社区"""
    card = get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")
    case_id = publish_case(card_id, req.case_data)
    if case_id is None:
        raise HTTPException(status_code=400, detail="发布失败（卡片不存在或已分享）")
    return {"case_id": case_id, "message": "已分享到社区"}
