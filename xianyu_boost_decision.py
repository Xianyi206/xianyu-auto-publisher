"""
投流决策模块 - 闲鱼帖子智能投流决策

输入帖子JSON → 规则判断 + AI决策 → 输出投流建议JSON

决策规则（规则优先，不匹配才调AI）：
  1. 浏览/曝光 < 5% → action="skip"
  2. 浏览/曝光 > 10% 且有咨询 → action="boost"
  3. 发布超过7天 → action="delist"
  4. 以上都不满足 → 调用 AI API 做语义决策

用法:
    from xianyu_boost_decision import decide_boost
    result = decide_boost(post_json)
"""

import os
import json
from datetime import datetime, timezone, timedelta
from openai import OpenAI

# ============================================================
# 环境变量配置（兼容多种命名）
# ============================================================
AI_API_KEY = (
    os.environ.get("AI_API_KEY", "")
    or os.environ.get("DEEPSEEK_API_KEY", "")
    or os.environ.get("OPENAI_API_KEY", "")
)
AI_API_BASE_URL = os.environ.get("AI_API_BASE_URL", "https://api.deepseek.com/v1")
AI_MODEL = os.environ.get("AI_MODEL", "deepseek-chat")

# 中国时区
TZ_CHINA = timezone(timedelta(hours=8))

# ============================================================
# 决策参数
# ============================================================
VIEW_RATIO_SKIP_THRESHOLD = 0.05    # <5% → skip
VIEW_RATIO_BOOST_THRESHOLD = 0.10   # >10% + 有咨询 → boost
MAX_POST_AGE_DAYS = 7               # 超过7天 → delist


def parse_post(post):
    """
    解析帖子输入，支持 dict 或 JSON 字符串。

    Args:
        post: dict 或 JSON 字符串

    Returns:
        dict: 解析后的帖子数据

    Raises:
        ValueError: 如果缺少必要字段
    """
    if isinstance(post, str):
        post = json.loads(post)

    required_fields = ["post_id", "exposure", "views", "inquiries", "published_at"]
    missing = [f for f in required_fields if f not in post]
    if missing:
        raise ValueError(f"缺少必要字段: {', '.join(missing)}")

    return post


def calc_view_ratio(post):
    """计算浏览/曝光比率"""
    exposure = post.get("exposure", 0)
    views = post.get("views", 0)
    if exposure <= 0:
        return 0.0
    return views / exposure


def calc_days_since_published(post):
    """计算帖子发布至今的天数"""
    published_at = post.get("published_at", "")
    try:
        pub_time = datetime.fromisoformat(published_at)
        # 如果字符串没有时区信息，假设为中国时区
        if pub_time.tzinfo is None:
            pub_time = pub_time.replace(tzinfo=TZ_CHINA)
        now = datetime.now(TZ_CHINA)
        delta = now - pub_time
        return delta.total_seconds() / 86400.0  # 转换为天数
    except (ValueError, TypeError):
        return 0.0


def apply_rules(post):
    """
    应用规则层判断。

    Returns:
        dict 或 None: 如果规则命中返回决策结果，否则返回 None（需要AI决策）
    """
    view_ratio = calc_view_ratio(post)
    days_since_pub = calc_days_since_published(post)
    inquiries = post.get("inquiries", 0)
    post_id = post.get("post_id", "unknown")
    title = post.get("title", "")

    # 规则1: 浏览/曝光 < 5% → skip
    if view_ratio < VIEW_RATIO_SKIP_THRESHOLD:
        return {
            "action": "skip",
            "reason": f"浏览曝光比仅{view_ratio:.1%}，低于5%阈值，帖子曝光效率低建议跳过投流",
            "budget": 0,
            "time": "",
            "boost": ""
        }

    # 规则2: 浏览/曝光 > 10% 且有咨询 → boost
    if view_ratio > VIEW_RATIO_BOOST_THRESHOLD and inquiries > 0:
        return {
            "action": "boost",
            "reason": f"浏览曝光比{view_ratio:.1%}超过10%且有{inquiries}条咨询，高转化潜力建议投流加速",
            "budget": 50,
            "time": "18:00-22:00",
            "boost": f"建议对帖子{post_id}「{title}」在晚高峰18:00-22:00投放50元，重点突出价格优势和咨询入口"
        }

    # 规则3: 发布超过7天 → delist
    if days_since_pub > MAX_POST_AGE_DAYS:
        return {
            "action": "delist",
            "reason": f"帖子已发布{days_since_pub:.0f}天超过7天，建议下架重新发布以获得新流量",
            "budget": 0,
            "time": "",
            "boost": ""
        }

    # 规则未命中，需要AI决策
    return None


def ai_decide(post):
    """
    调用 AI API 做语义决策。

    Args:
        post: 帖子 dict

    Returns:
        dict: AI 决策结果
    """
    if not AI_API_KEY:
        # 无 API Key 时返回保守决策
        return {
            "action": "watch",
            "reason": "AI API Key未配置，默认观望观察数据变化",
            "budget": 0,
            "time": "",
            "boost": ""
        }

    view_ratio = calc_view_ratio(post)
    days_since_pub = calc_days_since_published(post)
    inquiries = post.get("inquiries", 0)
    title = post.get("title", "")
    category = post.get("category", "")
    price = post.get("price", "")

    client = OpenAI(
        api_key=AI_API_KEY,
        base_url=AI_API_BASE_URL,
    )

    system_prompt = (
        "你是一个闲鱼投流决策专家。根据帖子数据，判断是否应该投流推广。\n\n"
        "决策选项：\n"
        "- boost: 建议投流（数据不错，值得推广）\n"
        "- watch: 先观望（数据一般，再观察一两天）\n"
        "- skip: 跳过（数据差，不值得投流）\n\n"
        "输出格式：严格输出JSON，不要加任何前缀说明。\n"
        '{"action": "boost|watch|skip", "reason": "一句话中文理由", '
        '"budget": 建议金额(0-100整数), "time": "建议时段(如18:00-22:00或空)", '
        '"boost": "投流参数建议(或空)"}'
    )

    user_prompt = (
        f"帖子数据：\n"
        f"- 标题：{title}\n"
        f"- 品类：{category}\n"
        f"- 价格：{price}\n"
        f"- 曝光：{post.get('exposure', 0)}\n"
        f"- 浏览：{post.get('views', 0)}\n"
        f"- 浏览曝光比：{view_ratio:.1%}\n"
        f"- 咨询数：{inquiries}\n"
        f"- 已发布天数：{days_since_pub:.1f}天\n\n"
        f"请根据以上数据做出投流决策。"
    )

    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=300,
        )

        text = response.choices[0].message.content.strip()

        # 尝试解析 JSON（可能被 markdown 代码块包裹）
        if text.startswith("```"):
            # 去掉 ```json ... ``` 包裹
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        result = json.loads(text)

        # 确保必要字段存在
        result.setdefault("action", "watch")
        result.setdefault("reason", "AI决策结果")
        result.setdefault("budget", 0)
        result.setdefault("time", "")
        result.setdefault("boost", "")
        return result

    except Exception as e:
        # AI 调用失败，返回观望
        return {
            "action": "watch",
            "reason": f"AI决策调用失败({str(e)[:50]})，建议人工判断",
            "budget": 0,
            "time": "",
            "boost": ""
        }


def decide_boost(post):
    """
    对帖子做出投流决策。

    决策流程：
      1. 规则层优先判断（skip/boost/delist）
      2. 规则未命中 → AI 语义决策

    Args:
        post: dict 或 JSON 字符串，包含 post_id, title, exposure,
              views, inquiries, published_at, category, price 等字段

    Returns:
        dict: 决策结果
            {
                "action": "boost|watch|skip|delist",
                "reason": "中文一句话理由",
                "budget": 50,
                "time": "18:00-22:00",
                "boost": "投流参数建议"
            }
    """
    post = parse_post(post)

    # 第一步：规则层判断
    rule_result = apply_rules(post)
    if rule_result is not None:
        return rule_result

    # 第二步：AI 语义决策
    return ai_decide(post)


# ============================================================
# 命令行入口
# ============================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python xianyu_boost_decision.py <post_json>")
        print("示例: python xianyu_boost_decision.py '{\"post_id\":\"12345\",...}'")
        sys.exit(1)

    post_input = sys.argv[1]
    result = decide_boost(post_input)
    print(json.dumps(result, ensure_ascii=False, indent=2))
