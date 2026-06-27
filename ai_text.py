"""
AI文案生成模块 - 为闲鱼商品生成真人风格文案

用法:
    from ai_text import generate_xianyu_description
    text = generate_xianyu_description("AI写作工具", "ChatGPT会员月卡", "9.9元", "苏州")
"""

import os
from openai import OpenAI

# 环境变量配置（兼容多种命名）
AI_API_KEY = (
    os.environ.get("AI_API_KEY", "")
    or os.environ.get("DEEPSEEK_API_KEY", "")
    or os.environ.get("OPENAI_API_KEY", "")
)
AI_API_BASE_URL = os.environ.get("AI_API_BASE_URL", "https://api.deepseek.com/v1")
AI_MODEL = os.environ.get("AI_MODEL", "deepseek-chat")

# 品类对应的闲鱼场景描述（用于 prompt 上下文）
CATEGORY_SCENARIOS = {
    "AI写作工具": "AI写作/文案生成工具，适合学生写论文、职场人写报告、自媒体写文章",
    "AI视频生成": "AI视频生成工具，一键生成短视频、宣传片、创意视频素材",
    "AI PPT制作": "AI PPT/幻灯片一键生成工具，输入主题自动出完整演示文稿",
}


def generate_xianyu_description(category, product_name, price, location, temperature=0.9):
    """
    调用AI API生成闲鱼风格的真人商品文案。

    Args:
        category: 品类（"AI写作工具" / "AI视频生成" / "AI PPT制作"）
        product_name: 商品名称
        price: 价格字符串，如 "9.9元"
        location: 所在地，如 "苏州"
        temperature: 随机性参数（0.7-1.2，越高越随机）

    Returns:
        str: 生成的文案
    """
    scenario = CATEGORY_SCENARIOS.get(category, category)

    if not AI_API_KEY:
        raise ValueError(
            "API Key 未设置。请设置以下任一环境变量：\n"
            "  export AI_API_KEY=your-deepseek-api-key\n"
            "  或 DEEPSEEK_API_KEY、OPENAI_API_KEY"
        )

    client = OpenAI(
        api_key=AI_API_KEY,
        base_url=AI_API_BASE_URL,
    )

    system_prompt = (
        "你是一个闲鱼资深卖家，专门转卖自己用不上的闲置物品。"
        "请为以下商品生成一段闲鱼商品描述。\n\n"
        "要求：\n"
        "1. 口语化，像真人出闲置，不像商家广告。用词随意自然，像在跟朋友聊天\n"
        "2. 200字以内，简洁有重点\n"
        "3. 不要用任何 emoji 表情符号\n"
        "4. 必须包含以下要素：用途场景 + 产品状态 + 交易方式 + 联系引导\n"
        "5. 结尾带 3 个 #话题标签\n"
        "6. 语气像真实个人卖家，可以说\"自己买的用了两次\"\"转给有需要的人\"这类话"
    )

    user_prompt = (
        f"品类：{category}（{scenario}）\n"
        f"商品名：{product_name}\n"
        f"价格：{price}\n"
        f"所在地：{location}\n\n"
        "直接输出文案内容，不要加任何前缀说明。"
    )

    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=400,
    )

    text = response.choices[0].message.content.strip()
    return text


def generate_multiple(category, product_name, price, location, count=3):
    """
    为同一品类生成多段不同的文案。

    通过不同 temperature 值控制随机性，确保每段文案不同。

    Args:
        category: 品类
        product_name: 商品名称
        price: 价格
        location: 所在地
        count: 生成数量（默认3，最多5）

    Returns:
        list[str]: 文案列表
    """
    temperatures = [0.7, 0.9, 1.1, 1.2, 1.3][:count]
    results = []
    for t in temperatures:
        text = generate_xianyu_description(
            category, product_name, price, location,
            temperature=t,
        )
        results.append(text)
    return results
