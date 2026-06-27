"""
投流决策模块测试 - 4种场景验证

场景1: 浏览/曝光=3%        → action="skip"   (规则层，不调AI)
场景2: 浏览/曝光=15%，有咨询 → action="boost"  (规则层)
场景3: 发布超过7天         → action="delist" (规则层)
场景4: 浏览/曝光=8%，有少量咨询 → 调AI决策
"""

import json
import sys
import os
from datetime import datetime, timezone, timedelta

# 确保可以导入同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from xianyu_boost_decision import decide_boost, apply_rules, calc_view_ratio, calc_days_since_published

TZ_CHINA = timezone(timedelta(hours=8))

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


def test_scenario_1_skip():
    """场景1: 浏览/曝光=3% → action='skip' (规则层，不调AI)"""
    print("\n=== 场景1: 低浏览曝光比 → skip ===")
    post = {
        "post_id": "10001",
        "title": "测试商品低曝光",
        "exposure": 1000,
        "views": 30,
        "inquiries": 0,
        "published_at": datetime.now(TZ_CHINA).isoformat(),
        "category": "AI写作工具",
        "price": "9.9元"
    }

    # 验证计算
    ratio = calc_view_ratio(post)
    check("浏览曝光比=3%", abs(ratio - 0.03) < 0.001, f"实际: {ratio:.4f}")

    # 验证规则层命中
    rule_result = apply_rules(post)
    check("规则层命中(非None)", rule_result is not None)
    check("action=skip", rule_result["action"] == "skip", f"实际: {rule_result['action']}")
    check("budget=0", rule_result["budget"] == 0)

    # 验证完整流程
    result = decide_boost(post)
    check("完整流程action=skip", result["action"] == "skip", f"实际: {result['action']}")
    print(f"  输出: {json.dumps(result, ensure_ascii=False)}")


def test_scenario_2_boost():
    """场景2: 浏览/曝光=15%，有咨询 → action='boost' (规则层)"""
    print("\n=== 场景2: 高浏览曝光比+有咨询 → boost ===")
    post = {
        "post_id": "10002",
        "title": "热销商品高转化",
        "exposure": 1000,
        "views": 150,
        "inquiries": 3,
        "published_at": datetime.now(TZ_CHINA).isoformat(),
        "category": "AI写作工具",
        "price": "9.9元"
    }

    # 验证计算
    ratio = calc_view_ratio(post)
    check("浏览曝光比=15%", abs(ratio - 0.15) < 0.001, f"实际: {ratio:.4f}")

    # 验证规则层命中
    rule_result = apply_rules(post)
    check("规则层命中(非None)", rule_result is not None)
    check("action=boost", rule_result["action"] == "boost", f"实际: {rule_result['action']}")
    check("budget=50", rule_result["budget"] == 50)
    check("time=18:00-22:00", rule_result["time"] == "18:00-22:00")

    # 验证完整流程
    result = decide_boost(post)
    check("完整流程action=boost", result["action"] == "boost", f"实际: {result['action']}")
    print(f"  输出: {json.dumps(result, ensure_ascii=False)}")


def test_scenario_3_delist():
    """场景3: 发布超过7天 → action='delist' (规则层)"""
    print("\n=== 场景3: 发布超7天 → delist ===")
    old_date = datetime.now(TZ_CHINA) - timedelta(days=10)
    post = {
        "post_id": "10003",
        "title": "老旧帖子",
        "exposure": 500,
        "views": 40,
        "inquiries": 1,
        "published_at": old_date.isoformat(),
        "category": "AI写作工具",
        "price": "9.9元"
    }

    # 验证天数计算
    days = calc_days_since_published(post)
    check("发布天数≈10天", 9.5 < days < 10.5, f"实际: {days:.1f}天")

    # 验证规则层命中
    rule_result = apply_rules(post)
    check("规则层命中(非None)", rule_result is not None)
    check("action=delist", rule_result["action"] == "delist", f"实际: {rule_result['action']}")
    check("budget=0", rule_result["budget"] == 0)

    # 验证完整流程
    result = decide_boost(post)
    check("完整流程action=delist", result["action"] == "delist", f"实际: {result['action']}")
    print(f"  输出: {json.dumps(result, ensure_ascii=False)}")


def test_scenario_4_ai_decide():
    """场景4: 浏览/曝光=8%，有少量咨询 → 调AI决策"""
    print("\n=== 场景4: 中等数据 → AI决策 ===")
    post = {
        "post_id": "10004",
        "title": "ChatGPT会员月卡转让",
        "exposure": 1000,
        "views": 80,
        "inquiries": 1,
        "published_at": datetime.now(TZ_CHINA).isoformat(),
        "category": "AI写作工具",
        "price": "9.9元"
    }

    # 验证计算
    ratio = calc_view_ratio(post)
    check("浏览曝光比=8%", abs(ratio - 0.08) < 0.001, f"实际: {ratio:.4f}")

    # 验证规则层未命中
    rule_result = apply_rules(post)
    check("规则层未命中(返回None)", rule_result is None, f"实际: {rule_result}")

    # 验证完整流程（会调AI）
    result = decide_boost(post)
    check("返回结果非空", result is not None)
    check("包含action字段", "action" in result)
    check("action在有效值中", result["action"] in ("boost", "watch", "skip"),
          f"实际: {result['action']}")
    print(f"  AI决策输出: {json.dumps(result, ensure_ascii=False)}")

    # 场景4b: 无API Key时的降级行为
    print("\n  --- 无API Key降级测试 ---")
    import xianyu_boost_decision as bd
    old_key = bd.AI_API_KEY
    bd.AI_API_KEY = ""
    result_no_key = bd.ai_decide(post)
    check("无Key时action=watch", result_no_key["action"] == "watch",
          f"实际: {result_no_key['action']}")
    print(f"  降级输出: {json.dumps(result_no_key, ensure_ascii=False)}")
    bd.AI_API_KEY = old_key


def test_edge_cases():
    """边界情况测试"""
    print("\n=== 边界测试 ===")

    # 边界: 刚好5%浏览曝光比 + 无咨询 → 不满足skip也不满足boost → AI决策
    post = {
        "post_id": "20001",
        "title": "边界5%",
        "exposure": 1000,
        "views": 50,
        "inquiries": 0,
        "published_at": datetime.now(TZ_CHINA).isoformat(),
        "category": "AI写作工具",
        "price": "9.9元"
    }
    ratio = calc_view_ratio(post)
    check("刚好5%→不小于5%阈值", ratio >= 0.05, f"实际: {ratio:.4f}")
    rule_result = apply_rules(post)
    check("5%+无咨询→规则层未命中", rule_result is None, f"实际: {rule_result}")

    # 边界: 刚好10%浏览曝光比，无咨询 → 不满足boost规则(>10%才触发)
    post2 = {
        "post_id": "20002",
        "title": "边界10%无咨询",
        "exposure": 1000,
        "views": 100,
        "inquiries": 0,
        "published_at": datetime.now(TZ_CHINA).isoformat(),
        "category": "AI写作工具",
        "price": "9.9元"
    }
    ratio2 = calc_view_ratio(post2)
    check("刚好10%→不大于10%阈值", abs(ratio2 - 0.10) < 0.001)
    rule_result2 = apply_rules(post2)
    check("10%+无咨询→规则层未命中", rule_result2 is None, f"实际: {rule_result2}")

    # 边界: exposure=0
    post3 = {
        "post_id": "20003",
        "title": "零曝光",
        "exposure": 0,
        "views": 0,
        "inquiries": 0,
        "published_at": datetime.now(TZ_CHINA).isoformat(),
        "category": "测试",
        "price": "0元"
    }
    ratio3 = calc_view_ratio(post3)
    check("exposure=0时ratio=0", ratio3 == 0.0, f"实际: {ratio3}")

    # parse_post 异常
    import xianyu_boost_decision as bd
    try:
        bd.parse_post({"post_id": "x"})
        check("缺少字段应抛异常", False, "未抛异常")
    except ValueError as e:
        check("缺少字段抛ValueError", True, str(e))


def main():
    global PASS, FAIL
    print("=" * 60)
    print("投流决策模块测试")
    print("=" * 60)

    test_scenario_1_skip()
    test_scenario_2_boost()
    test_scenario_3_delist()
    test_scenario_4_ai_decide()
    test_edge_cases()

    total = PASS + FAIL
    print(f"\n{'=' * 60}")
    print(f"结果: {PASS}/{total} 通过, {FAIL}/{total} 失败")
    print(f"{'=' * 60}")

    return FAIL == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
