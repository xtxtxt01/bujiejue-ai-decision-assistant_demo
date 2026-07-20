"""
导入预置案例到数据库

用途：为社区MVP提供初始内容
案例数量：20个
执行方式：python -m backend.scripts.seed_cases
"""

import sqlite3
import sys
import os
from typing import List, Dict

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


# 预置案例数据
CASES: List[Dict] = [
    # ==================== 工作类案例（8个） ====================
    {
        "case_type": "career",
        "title": "跳槽 vs 留下：成长空间的抉择",
        "background": "互联网3年 | 薪资+30% | 新公司加班更多",
        "core_conflict": "成长空间 vs 稳定性",
        "duration_days": 21,
        "final_choice": "选择跳槽",
        "turning_point": "想通了\"适应期的不舒服\"和\"一直待着不成长\"哪个更让我后悔",
        "retrospect": "不后悔。前3个月确实累，但学到了很多新东西。现在回头看，如果当时没跳，现在肯定后悔。",
        "retrospect_score": 8,
        "retrospect_months": 3,
        "decision_style": "rational",
        "life_stage": "early_career",
        "tags": "跳槽,成长,薪资,加班",
        "is_featured": 1
    },
    {
        "case_type": "career",
        "title": "大厂 offer vs 生活质量",
        "background": "工作5年 | 拿到大厂offer | 但通勤时间翻倍（单程2小时）",
        "core_conflict": "职业发展 vs 生活质量",
        "duration_days": 14,
        "final_choice": "拒绝offer，留在原公司",
        "turning_point": "算了笔账：每天4小时通勤 = 每年1000小时 = 相当于全职工作6个月",
        "retrospect": "很满意。后来原公司给了晋升机会，证明不跳也有发展。而且每天多出4小时，生活质量提升太多了。",
        "retrospect_score": 9,
        "retrospect_months": 6,
        "decision_style": "rational",
        "life_stage": "mid_career",
        "tags": "跳槽,通勤,工作生活平衡,大厂",
        "is_featured": 1
    },
    {
        "case_type": "career",
        "title": "30岁转行做产品经理",
        "background": "传统行业7年 | 想转互联网 | 薪资要降30%",
        "core_conflict": "转行机会 vs 稳定收入",
        "duration_days": 45,
        "final_choice": "转行，接受降薪",
        "turning_point": "意识到再不转，以后更难。30岁是最后的窗口期。",
        "retrospect": "前半年确实很焦虑，新领域啥都不会。但现在已经适应了，虽然还在追赶，但至少进入了这个赛道。",
        "retrospect_score": 7,
        "retrospect_months": 12,
        "decision_style": "intuitive",
        "life_stage": "mid_career",
        "tags": "转行,降薪,年龄焦虑,产品经理"
    },
    {
        "case_type": "career",
        "title": "加入创业公司还是留在大厂",
        "background": "大厂工作3年 | 朋友邀请加入创业 | 有期权但不稳定",
        "core_conflict": "博一把 vs 求稳定",
        "duration_days": 30,
        "final_choice": "没去，留在大厂",
        "turning_point": "问自己：如果创业失败了，我能承受吗？答案是不能，家里还有房贷。",
        "retrospect": "朋友的公司后来倒闭了，庆幸当时没去。但也有点遗憾，错过了一次冒险的机会。",
        "retrospect_score": 7,
        "retrospect_months": 6,
        "decision_style": "avoidant",
        "life_stage": "early_career",
        "tags": "创业,风险,稳定,大厂"
    },
    {
        "case_type": "career",
        "title": "降薪30%换一份不加班的工作",
        "background": "互联网6年 | 常年996 | 身体出现问题",
        "core_conflict": "健康 vs 收入",
        "duration_days": 18,
        "final_choice": "接受降薪，换了轻松的工作",
        "turning_point": "体检报告出来那天，几个指标都不正常。突然觉得钱再多也没命花不值得。",
        "retrospect": "太值了。虽然收入少了，但下班能准时，周末能休息，身体也恢复了。生活质量提升不是一点半点。",
        "retrospect_score": 9,
        "retrospect_months": 6,
        "decision_style": "spontaneous",
        "life_stage": "mid_career",
        "tags": "降薪,996,健康,工作生活平衡"
    },
    {
        "case_type": "career",
        "title": "25岁考公务员还是继续做互联网",
        "background": "互联网2年 | 家人催考公 | 但互联网薪资高3倍",
        "core_conflict": "稳定 vs 收入",
        "duration_days": 60,
        "final_choice": "继续做互联网，没考公",
        "turning_point": "看到几个考上公务员的同学，生活确实稳定但也确实清闲。问自己：我真的想要那样的生活吗？",
        "retrospect": "不后悔，现在互联网工作虽然累，但成长快、收入高。至少先赚几年钱，以后想考还来得及。",
        "retrospect_score": 8,
        "retrospect_months": 12,
        "decision_style": "dependent",
        "life_stage": "early_career",
        "tags": "考公,互联网,稳定,收入"
    },
    {
        "case_type": "career",
        "title": "晋升机会 vs 更感兴趣的组",
        "background": "大厂工作4年 | 本组有晋升名额 | 但对另一个组业务更感兴趣",
        "core_conflict": "晋升 vs 兴趣",
        "duration_days": 10,
        "final_choice": "留下争取晋升",
        "turning_point": "HR说转组后晋升要重新排队，至少再等一年。想了想，还是晋升更实际。",
        "retrospect": "有点后悔。晋升是拿到了，但每天做不感兴趣的事情很痛苦。应该选兴趣的。",
        "retrospect_score": 5,
        "retrospect_months": 6,
        "decision_style": "rational",
        "life_stage": "mid_career",
        "tags": "晋升,转组,兴趣"
    },
    {
        "case_type": "career",
        "title": "大厂稳定 vs 成长型公司快速晋升",
        "background": "应届生 | 同时拿到大厂和中厂offer | 大厂钱多但螺丝钉 vs 中厂钱少但能快速成长",
        "core_conflict": "平台 vs 成长",
        "duration_days": 7,
        "final_choice": "选了中厂",
        "turning_point": "师兄说：年轻的时候最重要的是成长，不是钱。大厂随时能去，但快速成长的机会窗口期很短。",
        "retrospect": "很庆幸选了这个。一年时间从实习生到小组长，学到的东西是大厂螺丝钉5年都学不到的。",
        "retrospect_score": 9,
        "retrospect_months": 12,
        "decision_style": "dependent",
        "life_stage": "student",
        "tags": "应届,大厂,成长,职业规划"
    },
    # ==================== 感情类案例（4个） ====================
    {
        "case_type": "relationship",
        "title": "异地恋还是分手",
        "background": "恋爱3年 | 对方去外地工作 | 一年见不了几次面",
        "core_conflict": "坚持异地 vs 放手",
        "duration_days": 30,
        "final_choice": "选择分手",
        "turning_point": "连续3个月见不到面，每次视频都在吵架。意识到异地把两个人都折磨得不像自己了。",
        "retrospect": "分手后反而轻松了。现在各自都有了新生活，偶尔还能聊聊天。可能不合适的不是人，是时机。",
        "retrospect_score": 7,
        "retrospect_months": 6,
        "decision_style": "intuitive",
        "life_stage": "early_career",
        "tags": "异地恋,分手,长距离"
    },
    {
        "case_type": "relationship",
        "title": "30岁了要不要结婚",
        "background": "恋爱2年 | 对方条件不错 | 但总觉得少了点什么",
        "core_conflict": "年龄焦虑 vs 感觉不到位",
        "duration_days": 90,
        "final_choice": "结婚了",
        "turning_point": "父母一直催，身边朋友都结了。想着条件合适就行，感情可以慢慢培养。",
        "retrospect": "后悔了。结婚后发现三观不合，吵架越来越多。现在在考虑离婚。当初不应该因为年龄而妥协。",
        "retrospect_score": 3,
        "retrospect_months": 12,
        "decision_style": "dependent",
        "life_stage": "mid_career",
        "tags": "结婚,年龄焦虑,三观",
        "is_featured": 1
    },
    {
        "case_type": "relationship",
        "title": "要不要生孩子",
        "background": "结婚3年 | 事业上升期 | 双方父母催生",
        "core_conflict": "事业 vs 生育",
        "duration_days": 180,
        "final_choice": "决定生",
        "turning_point": "看到同事生完孩子回来，虽然累但很幸福。意识到有些事情错过了就不会再有机会。",
        "retrospect": "很累，但不后悔。孩子确实占用了大量时间，事业也确实受影响。但看着孩子长大，觉得这一切都值得。",
        "retrospect_score": 8,
        "retrospect_months": 18,
        "decision_style": "intuitive",
        "life_stage": "mid_career",
        "tags": "生育,事业,家庭"
    },
    {
        "case_type": "relationship",
        "title": "对方出轨了，要不要原谅",
        "background": "恋爱5年 | 对方承认错误 | 但信任已经破裂",
        "core_conflict": "原谅 vs 分手",
        "duration_days": 15,
        "final_choice": "分手了",
        "turning_point": "朋友说：原谅容易，但忘记很难。你能保证以后不会因为这件事吵架吗？我想了想，做不到。",
        "retrospect": "做对了。分手后虽然痛苦，但慢慢走出来了。如果原谅了，每次吵架都会翻旧账，那才是真正的折磨。",
        "retrospect_score": 8,
        "retrospect_months": 6,
        "decision_style": "dependent",
        "life_stage": "early_career",
        "tags": "出轨,分手,信任"
    },
    # ==================== 生活类案例（4个） ====================
    {
        "case_type": "lifestyle",
        "title": "掏空六个钱包买房还是继续租房",
        "background": "工作5年 | 有一点积蓄 | 但买房要掏空六个钱包 + 30年贷款",
        "core_conflict": "资产 vs 自由",
        "duration_days": 60,
        "final_choice": "买了",
        "turning_point": "房东突然说要收回房子，搬家时那种漂泊感让我下定决心买房。",
        "retrospect": "还款压力确实大，每个月一半工资还房贷。但有了自己的家，心里踏实很多。",
        "retrospect_score": 7,
        "retrospect_months": 12,
        "decision_style": "avoidant",
        "life_stage": "mid_career",
        "tags": "买房,租房,房贷"
    },
    {
        "case_type": "lifestyle",
        "title": "工作2年后要不要出国读研",
        "background": "互联网工作2年 | 存了30万 | 想申请美国硕士",
        "core_conflict": "投资未来 vs 当下收入",
        "duration_days": 90,
        "final_choice": "没去，继续工作",
        "turning_point": "算了笔账：2年学费+生活费至少100万，回来后年龄也大了，不一定能回本。",
        "retrospect": "不后悔，但也有遗憾。现在工作稳定收入不错，但偶尔还是会想如果出国了会怎样。",
        "retrospect_score": 6,
        "retrospect_months": 24,
        "decision_style": "rational",
        "life_stage": "early_career",
        "tags": "留学,工作,投资"
    },
    {
        "case_type": "lifestyle",
        "title": "留在北京还是回老家",
        "background": "北京工作5年 | 老家有关系能安排工作 | 但北京发展机会更多",
        "core_conflict": "机会 vs 归属感",
        "duration_days": 45,
        "final_choice": "回老家了",
        "turning_point": "父母身体不好，自己也累了。意识到北京再好也不是家。",
        "retrospect": "很满意。虽然收入少了一半，但生活节奏慢了，压力小了，每天能陪父母吃饭，这种幸福感是钱买不到的。",
        "retrospect_score": 9,
        "retrospect_months": 12,
        "decision_style": "intuitive",
        "life_stage": "mid_career",
        "tags": "北漂,回老家,生活方式"
    },
    {
        "case_type": "lifestyle",
        "title": "一个人住要不要养猫",
        "background": "独居 | 工作忙 | 但很想有个陪伴",
        "core_conflict": "陪伴 vs 责任",
        "duration_days": 7,
        "final_choice": "养了",
        "turning_point": "去朋友家看到她的猫，回家后空荡荡的房子更让人觉得孤独。",
        "retrospect": "太值了！虽然每天要铲屎、喂食，周末不能随便出去玩，但回家有个小生命等着你的感觉真的很治愈。",
        "retrospect_score": 10,
        "retrospect_months": 6,
        "decision_style": "spontaneous",
        "life_stage": "early_career",
        "tags": "养宠物,独居,陪伴"
    },
    # ==================== 消费类案例（2个） ====================
    {
        "case_type": "finance",
        "title": "要不要买车",
        "background": "工作3年 | 有积蓄 | 但买车要花20万 + 每年养车费3万",
        "core_conflict": "便利 vs 成本",
        "duration_days": 30,
        "final_choice": "没买，继续打车",
        "turning_point": "算了笔账：一年打车+地铁最多1.5万，买车一年养车费就要3万，还不算20万本金。",
        "retrospect": "做对了。发现打车+地铁完全够用，周末偶尔租个车自驾游也很方便。省下来的钱投资收益比车贬值划算多了。",
        "retrospect_score": 8,
        "retrospect_months": 12,
        "decision_style": "rational",
        "life_stage": "early_career",
        "tags": "买车,打车,成本,投资"
    },
    {
        "case_type": "finance",
        "title": "换手机：买iPhone还是国产旗舰",
        "background": "手机该换了 | iPhone贵一倍 | 但用得久 vs 国产便宜但更新快",
        "core_conflict": "品牌 vs 性价比",
        "duration_days": 7,
        "final_choice": "买了国产旗舰",
        "turning_point": "试用了朋友的国产旗舰，发现体验已经很好了，没必要为品牌多花一倍的钱。",
        "retrospect": "很满意。用了半年各方面都很好，省下的钱还能干别的。以后也会继续买国产。",
        "retrospect_score": 8,
        "retrospect_months": 6,
        "decision_style": "rational",
        "life_stage": "early_career",
        "tags": "手机,iPhone,性价比,品牌"
    },
    # ==================== 学业类案例（2个） ====================
    {
        "case_type": "education",
        "title": "大四考研还是直接工作",
        "background": "本科双非 | 想考985研究生 | 但不确定能考上",
        "core_conflict": "学历 vs 经验",
        "duration_days": 60,
        "final_choice": "选择考研",
        "turning_point": "看到学长因为学历被大厂卡在简历关，意识到学历真的很重要。",
        "retrospect": "一战没考上，二战考上了。虽然浪费了2年时间，但现在拿到的offer比本科直接工作的同学好太多，值得。",
        "retrospect_score": 8,
        "retrospect_months": 36,
        "decision_style": "rational",
        "life_stage": "student",
        "tags": "考研,学历,就业"
    },
    {
        "case_type": "education",
        "title": "保研本校还是考外校985",
        "background": "211本科 | 可以保研本校 | 但想冲985",
        "core_conflict": "稳妥 vs 更好平台",
        "duration_days": 30,
        "final_choice": "保研本校",
        "turning_point": "外校考试太不确定了，万一考不上连保研资格都没了，风险太大。",
        "retrospect": "有点后悔。虽然顺利读研了，但总觉得如果当时拼一把，也许能上更好的学校。现在找工作还是被学校牌子限制了。",
        "retrospect_score": 5,
        "retrospect_months": 24,
        "decision_style": "avoidant",
        "life_stage": "student",
        "tags": "保研,考研,985,风险"
    },
]


def seed_cases(db_path: str = None) -> int:
    """
    导入预置案例到数据库

    Args:
        db_path: 数据库路径，默认使用 config 中的路径

    Returns:
        成功导入的案例数量
    """
    from config import DB_PATH
    if db_path is None:
        db_path = DB_PATH

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='decision_cases'
        """)
        if not cursor.fetchone():
            print("[错误] decision_cases 表不存在，请先运行 init_db")
            return 0

        # 检查是否已有数据（避免重复导入）
        cursor.execute("SELECT COUNT(*) FROM decision_cases")
        existing = cursor.fetchone()[0]
        if existing > 0:
            print(f"[提示] 数据库中已有 {existing} 条案例")
            answer = input("是否清空后重新导入？(y/N): ").strip().lower()
            if answer == 'y':
                cursor.execute("DELETE FROM decision_cases")
                print("已清空现有案例")
            else:
                print("取消导入")
                return 0

        # 批量插入案例
        inserted = 0
        for case in CASES:
            cursor.execute("""
                INSERT INTO decision_cases (
                    case_type, title, background, core_conflict, duration_days,
                    final_choice, turning_point, retrospect, retrospect_score,
                    retrospect_months, decision_style, life_stage, tags, is_featured
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case["case_type"],
                case["title"],
                case["background"],
                case["core_conflict"],
                case["duration_days"],
                case["final_choice"],
                case["turning_point"],
                case["retrospect"],
                case["retrospect_score"],
                case.get("retrospect_months", 3),
                case.get("decision_style", ""),
                case.get("life_stage", ""),
                case.get("tags", ""),
                case.get("is_featured", 0)
            ))
            inserted += 1

        conn.commit()
        print(f"[成功] 导入 {inserted} 个预置案例")

        # 统计分布
        cursor.execute("""
            SELECT case_type, COUNT(*) FROM decision_cases
            GROUP BY case_type
        """)
        print("\n案例类型分布：")
        for case_type, count in cursor.fetchall():
            print(f"  {case_type}: {count} 个")

        return inserted

    except Exception as e:
        conn.rollback()
        print(f"[失败] 导入失败: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed_cases()
