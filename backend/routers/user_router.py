from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.user_service import create_user, get_user, update_user


router = APIRouter(prefix="/api/user", tags=["user"])


class RegisterRequest(BaseModel):
    nickname: str
    mbti: str = ""
    decision_style: str = ""
    values_ranking: list[str] = []
    life_stage: str = ""
    frequent_dilemma_types: list[str] = []
    interests: list[str] = []
    self_intro: str = ""  # 用户首次登录自我介绍（可选）


class UpdateRequest(BaseModel):
    mbti: str | None = None
    decision_style: str | None = None
    values_ranking: list[str] | None = None
    life_stage: str | None = None
    frequent_dilemma_types: list[str] | None = None
    interests: list[str] | None = None


@router.post("/register")
def register(req: RegisterRequest):
    uid = create_user(
        nickname=req.nickname,
        mbti=req.mbti,
        decision_style=req.decision_style,
        values_ranking=req.values_ranking,
        life_stage=req.life_stage,
        frequent_dilemma_types=req.frequent_dilemma_types,
        interests=req.interests,
        self_intro=req.self_intro,
    )
    return {"uid": uid, "message": "建档成功"}


@router.get("/{uid}/profile")
def profile(uid: str):
    user = get_user(uid)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/{uid}/profile")
def update_profile(uid: str, req: UpdateRequest):
    user = get_user(uid)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    update_user(uid, **req.model_dump(exclude_none=True))
    return {"message": "更新成功"}
