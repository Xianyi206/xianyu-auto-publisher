"""
测试 AI 文案生成模块

依次测试 3 个品类，每个品类生成 3 段文案并打印。
验证不同温度和调用间文案确实不同。
"""

import sys
import os

# 确保可以 import ai_text
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_text import generate_xianyu_description, generate_multiple

# 测试配置
TEST_CASES = [
    {
        "category": "AI写作工具",
        "product_name": "ChatGPT Plus 会员月卡",
        "price": "9.9元",
        "location": "苏州",
    },
    {
        "category": "AI视频生成",
        "product_name": "可灵AI视频生成会员",
        "price": "15元",
        "location": "上海",
    },
    {
        "category": "AI PPT制作",
        "product_name": "Gamma AI PPT会员账号",
        "price": "8.8元",
        "location": "北京",
    },
]


def main():
    print("=" * 60)
    print("AI 闲鱼文案生成测试")
    print("=" * 60)

    total_texts = []
    all_passed = True

    for case in TEST_CASES:
        category = case["category"]
        product = case["product_name"]
        price = case["price"]
        location = case["location"]

        print(f"\n{'─' * 60}")
        print(f"品类: {category}")
        print(f"商品: {product} | 价格: {price} | 所在地: {location}")
        print(f"{'─' * 60}")

        texts = []  # 当前品类的文案集合
        failed = False

        for i in range(3):
            temp = [0.7, 0.9, 1.1][i]
            try:
                text = generate_xianyu_description(
                    category, product, price, location,
                    temperature=temp,
                )
                texts.append(text)
                print(f"\n  [{i+1}/3] temperature={temp}")
                print(f"  文案: {text}")
                print(f"  字数: {len(text)}字")
            except Exception as e:
                print(f"\n  [{i+1}/3] temperature={temp} ❌ 失败: {e}")
                failed = True
                all_passed = False

        if not failed and len(texts) == 3:
            # 验证3段文案互不相同
            unique = len(set(texts))
            if unique == 3:
                print(f"\n  ✅ 3段文案全部不同（共{len(set(t for t in texts))}种）")
            elif unique == 2:
                print(f"\n  ⚠️ 仅有{unique}种不同文案（有重复）")
                all_passed = False
            else:
                print(f"\n  ❌ 3段文案完全相同!")
                all_passed = False

            total_texts.extend(texts)
        else:
            print(f"\n  ❌ 品类 {category} 测试未完成")

    # 汇总
    print(f"\n{'=' * 60}")
    print(f"测试汇总")
    print(f"{'=' * 60}")
    print(f"品类数: {len(TEST_CASES)}")
    print(f"生成文案总数: {len(total_texts)}")
    print(f"全部通过: {'✅ 是' if all_passed else '❌ 否'}")
    print(f"{'=' * 60}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
