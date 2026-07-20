from fastapi import APIRouter, HTTPException, Query
from services.case_service import (
    get_cases, count_cases, add_empathy, add_view,
    get_recommendations_for_card, VALID_CASE_TYPES
)


router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("")
def list_cases(
    type: str = Query("all"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """获取案例列表（按类型筛选）"""
    # 校验类型参数
    if type != "all" and type not in VALID_CASE_TYPES:
        raise HTTPException(status_code=400, detail="无效的案例类型")

    cases = get_cases(case_type=type, limit=limit, offset=offset)
    total = count_cases(case_type=type)

    return {
        "cases": cases,
        "total": total,
        "has_more": offset + len(cases) < total,
    }


@router.get("/recommendations")
def card_recommendations(
    card_id: str = Query(...),
    limit: int = Query(3, ge=1, le=10),
):
    """【纠结驱动】为某张纠结卡片推荐相似案例"""
    cases = get_recommendations_for_card(card_id, limit=limit)
    return {"cases": cases}


@router.post("/{case_id}/empathy")
def empathy(case_id: int):
    """点击"我也是"，增加共鸣数"""
    new_count = add_empathy(case_id)
    if new_count is None:
        raise HTTPException(status_code=404, detail="案例不存在")
    return {"empathy_count": new_count}


@router.post("/{case_id}/view")
def view(case_id: int):
    """增加浏览数（进入详情时调用）"""
    success = add_view(case_id)
    if not success:
        raise HTTPException(status_code=404, detail="案例不存在")
    return {"message": "ok"}
