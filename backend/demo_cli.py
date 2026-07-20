"""
交互式命令行 Demo — 体验完整的决策对话流程。

使用方式：
    cd backend
    python demo_cli.py
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db
from services.user_service import create_user, get_user
from services.card_service import create_card, get_card, get_user_cards, close_card
from services.chat_service import chat


def print_card(card: dict):
    status_icon = {"active": "🔄", "decided": "✅", "shelved": "⏸️"}.get(card["status"], "❓")
    print(f"\n┌─────────────────────────────────────┐")
    print(f"│ {status_icon} {card['title'] or '(未命名)'}".ljust(38) + "│")
    if card["core_conflict"]:
        print(f"│ 矛盾：{card['core_conflict']}".ljust(36) + "│")
    if card["trigger_event"]:
        print(f"│ 触发：{card['trigger_event']}".ljust(36) + "│")
    print(f"│ 状态：{card['status']}".ljust(38) + "│")
    print(f"└─────────────────────────────────────┘")


def onboarding():
    """首次建档流程"""
    print("\n" + "="*40)
    print("  欢迎使用「不纠结」AI决策助手")
    print("  让我先了解一下你")
    print("="*40)

    nickname = input("\n你的昵称：").strip() or "用户"

    print("\n你的MBTI类型（不知道可以跳过）：")
    mbti = input(">> ").strip().upper() or ""

    print("\n你的决策风格是？")
    print("  1. 回避型（倾向拖延、维持现状）")
    print("  2. 冲动型（容易一时冲动做决定）")
    print("  3. 理性型（喜欢收集信息分析）")
    print("  4. 依赖型（倾向听别人意见）")
    style_choice = input("选择 1-4：").strip()
    style_map = {"1": "avoidant", "2": "impulsive", "3": "rational", "4": "dependent"}
    decision_style = style_map.get(style_choice, "rational")

    print("\n你最在意什么？按优先级排序（输入数字，如 132）：")
    print("  1. 成长  2. 稳定  3. 收入")
    order = input(">> ").strip() or "123"
    values_list = {"1": "成长", "2": "稳定", "3": "收入"}
    values_ranking = [values_list.get(c, "") for c in order if c in values_list]
    if not values_ranking:
        values_ranking = ["成长", "稳定", "收入"]

    print("\n简单描述下你当前的人生阶段：")
    life_stage = input(">> ").strip() or "职场人"

    print("\n你常纠结的领域（可多选，用空格分隔）：")
    print("  1.职业  2.关系  3.人生方向  4.消费  5.日常")
    types_input = input(">> ").strip() or "1"
    type_map = {"1": "career", "2": "relationship", "3": "life_direction", "4": "consumption", "5": "daily"}
    frequent_types = [type_map.get(t, "") for t in types_input.split() if t in type_map]
    if not frequent_types:
        frequent_types = ["career"]

    uid = create_user(
        nickname=nickname,
        mbti=mbti,
        decision_style=decision_style,
        values_ranking=values_ranking,
        life_stage=life_stage,
        frequent_dilemma_types=frequent_types,
        interests=[]
    )
    print(f"\n✓ 建档完成！你的ID: {uid}")
    return uid


def new_dilemma(uid: str):
    """创建新纠结"""
    print("\n你在纠结什么类型的事？")
    print("  1.职业  2.关系  3.人生方向  4.消费  5.日常")
    t = input("选择 1-5：").strip() or "1"
    type_map = {"1": "career", "2": "relationship", "3": "life_direction", "4": "consumption", "5": "daily"}
    dilemma_type = type_map.get(t, "career")

    print("\n说说你在纠结什么（想到什么说什么）：")
    initial_input = input(">> ").strip()
    if not initial_input:
        print("你什么都没说...下次再来吧")
        return None

    card_id = create_card(uid=uid, dilemma_type=dilemma_type, initial_input=initial_input)

    print("\n正在思考...")
    result = chat(uid=uid, card_id=card_id, user_message=initial_input)
    print(f"\n🤖 不纠结：{result['assistant_message']}")

    if result.get("card_info"):
        print_card(get_card(card_id))

    return card_id


def continue_chat(uid: str, card_id: str):
    """在卡片内继续对话"""
    while True:
        user_input = input("\n你：").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "退出", "q"):
            break
        if user_input in ("关闭", "结束", "close"):
            reason = input("做了什么决定？（直接回车跳过）：").strip()
            close_card(card_id, status="decided" if reason else "shelved",
                       decision_result=reason, decision_reason="")
            print("✓ 卡片已关闭")
            break

        print("\n正在思考...")
        result = chat(uid=uid, card_id=card_id, user_message=user_input)
        print(f"\n🤖 不纠结：{result['assistant_message']}")

        if result.get("card_updated") and result.get("card_info"):
            print("\n[卡片已更新]")
            print_card(get_card(card_id))

        if result["stage"] == "closing":
            print("\n（看起来你做了决定，输入「关闭」可以结束这个纠结）")


def main():
    init_db()

    print("\n" + "="*40)
    print("    「不纠结」AI个性化决策助手 Demo")
    print("="*40)

    # 检查是否有已有用户
    uid = None
    existing_uid = input("\n输入你的用户ID（没有的话直接回车创建新用户）：").strip()
    if existing_uid:
        user = get_user(existing_uid)
        if user:
            print(f"欢迎回来，{user['nickname']}！")
            uid = existing_uid
        else:
            print("ID不存在，帮你创建新用户")

    if not uid:
        uid = onboarding()

    # 主循环
    while True:
        print("\n" + "-"*30)
        print("  1. 新建纠结")
        print("  2. 查看我的纠结")
        print("  3. 继续某个纠结的对话")
        print("  4. 退出")
        choice = input("\n选择 1-4：").strip()

        if choice == "1":
            card_id = new_dilemma(uid)
            if card_id:
                print("\n（继续聊这个纠结，输入 quit 返回主菜单）")
                continue_chat(uid, card_id)

        elif choice == "2":
            cards = get_user_cards(uid)
            if not cards:
                print("\n还没有纠结，去创建一个吧")
            else:
                for card in cards:
                    print_card(card)

        elif choice == "3":
            cards = get_user_cards(uid)
            if not cards:
                print("\n还没有纠结")
                continue
            print("\n选择一个纠结继续：")
            for i, card in enumerate(cards):
                title = card["title"] or card["dilemma_type"]
                print(f"  {i+1}. [{card['status']}] {title}")
            idx = input("输入编号：").strip()
            try:
                card = cards[int(idx) - 1]
                continue_chat(uid, card["id"])
            except (ValueError, IndexError):
                print("无效选择")

        elif choice == "4":
            print(f"\n再见！你的ID是 {uid}，下次可以直接用它登录。")
            break


if __name__ == "__main__":
    main()
