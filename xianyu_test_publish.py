"""
本地发布测试 — 一键走通：选图→处理→扫码登录→发布→免登验证

用法:
    python xianyu_test_publish.py
"""
import os, sys, time, subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
TEST_SRC = Path.home() / ".hermes" / "tmp" / "xianyu_test" / "source"
CONFIG_BACKUP = PROJECT_DIR / "config.yaml.bak"

def step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")

# ============ Step 1: 临时修改 config 指向测试数据 ============
step("Step 1/5: 配置测试环境")

import yaml
with open(PROJECT_DIR / "config.yaml", 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

# 备份
import shutil
shutil.copy(PROJECT_DIR / "config.yaml", CONFIG_BACKUP)

# 修改为测试路径
cfg['paths']['z_root'] = str(TEST_SRC)
cfg['paths']['out_dir'] = str(Path.home() / ".hermes" / "tmp" / "xianyu_publish")
# 产品目录映射到测试目录名
test_dirs = sorted([d.name for d in TEST_SRC.iterdir() if d.is_dir()])
product_dirs = [d for d in test_dirs if d != "4 EY500-16"][:4]
person_dirs = ["4 EY500-16"]

cfg['selection']['primary_product_dirs'] = product_dirs
cfg['selection']['backup_product_dirs'] = []
cfg['selection']['person_dirs'] = person_dirs

with open(PROJECT_DIR / "config.yaml", 'w', encoding='utf-8') as f:
    yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)

print(f"   z_root → {cfg['paths']['z_root']}")
print(f"   products → {cfg['selection']['primary_product_dirs']}")
print(f"   persons  → {cfg['selection']['person_dirs']}")

# ============ Step 2: 图片处理 ============
step("Step 2/5: 图片预处理")
result = subprocess.run(
    [sys.executable, str(PROJECT_DIR / "xianyu_process_images.py")],
    cwd=str(PROJECT_DIR)
)
if result.returncode != 0:
    print("❌ 图片处理失败")
    shutil.copy(CONFIG_BACKUP, PROJECT_DIR / "config.yaml")
    sys.exit(1)

# 检查输出
out_dir = Path.home() / ".hermes" / "tmp" / "xianyu_publish"
imgs = sorted(out_dir.glob("*.jpg"))
print(f"\n✅ 生成 {len(imgs)} 张图片:")
for img in imgs:
    print(f"   {img.name}")

# ============ Step 3: 首次发布（扫码登录） ============
step("Step 3/5: 首次发布 — 扫码登录")
print("即将打开浏览器，请在闲鱼页面扫码登录，登录后按 Enter 继续...")
print("（脚本会自动检测登录状态）")
print()
input("准备好后按 Enter 开始 → ")

result = subprocess.run(
    [sys.executable, str(PROJECT_DIR / "xianyu_publish_v21.py")],
    cwd=str(PROJECT_DIR)
)

if result.returncode != 0:
    print("⚠️ 发布未完全成功，但登录状态已保存")

# ============ Step 4: 免登重启验证 ============
step("Step 4/5: 免登重启验证")
print("重新启动发布流程 — 如果登录状态持久化成功，应该跳过登录步骤")
print()
input("按 Enter 开始验证 → ")

result = subprocess.run(
    [sys.executable, str(PROJECT_DIR / "xianyu_publish_v21.py")],
    cwd=str(PROJECT_DIR)
)

if result.returncode == 0:
    print("\n✅ 免登验证通过！登录态持久化成功")
else:
    print("\n⚠️ 免登验证未完全通过，检查日志")

# ============ Step 5: 恢复配置 ============
step("Step 5/5: 恢复配置")
shutil.copy(CONFIG_BACKUP, PROJECT_DIR / "config.yaml")
os.remove(CONFIG_BACKUP)
print("✅ config.yaml 已恢复")

print(f"\n{'='*60}")
print("  测试完成")
print(f"{'='*60}")
print(f"\n持久化目录: ~/.hermes/xianyu_browser_profile")
print(f"输出图片: {out_dir}")
print(f"日志: ~/.hermes/logs/xianyu_v21.log")
