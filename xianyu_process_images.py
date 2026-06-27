"""
闲鱼图片预处理 v7 — Z盘自主选图 + 超时重试
2026-05-23 更新：价格改9.9元/天、5张中必须1张真人坐轮椅

用法：
  /c/Users/xxx13/AppData/Local/Programs/Python/Python312/python.exe ^
    ~/.hermes/skills/multi-platform-uploader/xianyu-post/scripts/xianyu_process_images.py
"""
import os, random, sys, subprocess, time, yaml
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

# === 加载配置 ===
def load_config(config_path=None):
    """加载配置文件，自动展开路径中的 ~ 和相对路径"""
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    else:
        config_path = Path(config_path)
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    # 递归展开路径：对包含路径分隔符或 ~ 的字符串值做 expanduser
    def _expand(obj):
        if isinstance(obj, dict):
            return {k: _expand(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_expand(v) for v in obj]
        elif isinstance(obj, str):
            if '\\' in obj or '/' in obj or obj.startswith('~'):
                return os.path.expanduser(obj)
            return obj
        return obj
    return _expand(cfg)

config = load_config()

# === 配置（从 config.yaml 读取） ===
Z_ROOT = Path(config['paths']['z_root'])
OUT_DIR = Path(config['paths']['out_dir'])
TARGET_W = config['image']['target_width']
TARGET_H = config['image']['target_height']
FONT_PATH = config['paths']['font_path']
FONT_SIZE = config['image']['font_size']
TEXT_COLOR = tuple(config['image']['text_color'])
SHADOW_COLOR = tuple(config['image']['shadow_color'])
SHADOW_OFFSET = config['image']['shadow_offset']
JITTER_X = config['image']['jitter_x']
JITTER_Y = config['image']['jitter_y']
TEXT_Y = config['image']['text_y']

sel = config['selection']
# 主力产品线（优先各选1张）
PRIMARY_PRODUCT_DIRS = [(d, "product") for d in sel['primary_product_dirs']]
# 备用产品线（主力不足时补选，同目录可出2张）
BACKUP_PRODUCT_DIRS = [(d, "product") for d in sel['backup_product_dirs']]
# 真人图优先从 EY500-16 取（女人坐轮椅），备选宣传图片
PERSON_DIRS = [(d, "person") for d in sel['person_dirs']]
# 优先使用的真人图
PREFERRED_PERSON_IMAGES = sel['preferred_person_images']
PRODUCT_COUNT = sel['product_count']
PERSON_COUNT = sel['person_count']

retry = config['retry']
MAX_RETRIES = retry['max_retries']

def pick_images(root, dirs_info, needed, preferred=None):
    """从多个目录各选1张可用图片，排除(已发)/(已用)，优先使用preferred文件"""
    selected = []
    for dir_name, tag in dirs_info:
        if len(selected) >= needed:
            break
        d = root / dir_name
        if not d.exists():
            print(f"  ⚠️ 目录不存在: {dir_name}")
            continue
        # 优先选指定文件
        picked_preferred = False
        if preferred and tag == "person":
            for pref_name in preferred:
                pref = d / pref_name
                if pref.exists() and '(已发)' not in pref.stem and '(已用)' not in pref.stem:
                    selected.append((pref, tag))
                    print(f"  ✅ {dir_name}: {pref.name} (首选)")
                    picked_preferred = True
                    break
            if picked_preferred:
                continue  # 已从preferred选到
        # 常规选图
        candidates = []
        for ext in ('*.jpg', '*.JPG', '*.jpeg', '*.JPEG', '*.png', '*.PNG', '*.webp', '*.bmp'):
            for f in d.glob(ext):
                if '(已发)' not in f.stem and '(已用)' not in f.stem:
                    candidates.append(f)
        if candidates:
            candidates.sort()
            pick = candidates[0]
            selected.append((pick, tag))
            print(f"  ✅ {dir_name}: {pick.name}")
        else:
            print(f"  ⚠️ {dir_name}: 无可用图片")
    return selected

print("🔍 Z盘选图...")

# === Z盘可用性检查（含超时重试，3次，5s/10s/15s递增延迟）===
def check_z_drive(timeout=15):
    """Quick probe: use subprocess with timeout to avoid blocking on disconnected network drives"""
    try:
        subprocess.run(
            ['cmd', '/c', 'dir', str(Z_ROOT), '>nul', '2>&1'],
            timeout=timeout, check=False
        )
        return True
    except subprocess.TimeoutExpired:
        return False

for attempt in range(1, MAX_RETRIES + 1):
    if check_z_drive(timeout=retry['timeout']):
        break
    if attempt < MAX_RETRIES:
        wait = retry['base_delay'] * attempt  # 5s, 10s, 15s
        print(f"  ⏳ Z盘暂不可用，{wait}秒后重试 ({attempt}/{MAX_RETRIES})...")
        time.sleep(wait)
else:
    print(f"❌ Z盘不可用（重试{MAX_RETRIES}次后仍失败）: {Z_ROOT}")
    sys.exit(1)

if not Z_ROOT.exists():
    print(f"❌ Z盘路径不存在: {Z_ROOT}")
    sys.exit(1)

total_needed = PRODUCT_COUNT + PERSON_COUNT

# 选产品图：主力优先，不足时从备用补选（同目录可出2张）
products = pick_images(Z_ROOT, PRIMARY_PRODUCT_DIRS, PRODUCT_COUNT)
if len(products) < PRODUCT_COUNT:
    shortage = PRODUCT_COUNT - len(products)
    print(f"  🔄 主力不足（缺{shortage}张），从备用目录补选...")
    backups = pick_images(Z_ROOT, BACKUP_PRODUCT_DIRS, shortage)
    products += backups
    if len(products) < PRODUCT_COUNT:
        print(f"  ⚠️ 备用后仍缺{PRODUCT_COUNT-len(products)}张，尝试从所有目录遍历...")
        # 最终兜底：从所有子目录遍历排除已选
        existing_srcs = {str(p[0]) for p in products}
        for subdir in sorted(Z_ROOT.iterdir()):
            if not subdir.is_dir() or len(products) >= PRODUCT_COUNT:
                break
            for ext in ('*.jpg', '*.JPG', '*.jpeg', '*.JPEG', '*.png', '*.PNG'):
                for f in sorted(subdir.glob(ext)):
                    if len(products) >= PRODUCT_COUNT:
                        break
                    if str(f) in existing_srcs:
                        continue
                    if '(已发)' not in f.stem and '(已用)' not in f.stem:
                        products.append((f, "product"))
                        print(f"  ✅ {subdir.name}: {f.name} (兜底)")
                        break
# 选真人坐轮椅（优先 IMG_0382.jpg）
persons = pick_images(Z_ROOT, PERSON_DIRS, PERSON_COUNT, preferred=PREFERRED_PERSON_IMAGES)

all_picks = products + persons
if len(all_picks) < total_needed:
    print(f"\n❌ 只选到 {len(all_picks)} 张，需要{total_needed}张！产品={len(products)} 真人={len(persons)}")
    sys.exit(1)

print(f"\n🎯 选定 {len(all_picks)} 张（{len(products)}产品 + {len(persons)}真人），开始预处理...")

# === 清空输出 ===
os.makedirs(OUT_DIR, exist_ok=True)
for f in OUT_DIR.glob("*.*"):
    f.unlink()

# === 处理每张 ===
for i, (src, tag) in enumerate(all_picks):
    try:
        img = Image.open(src)
        img.verify()  # 验证图片完整性
        img = Image.open(src)  # verify后需重新open
    except Exception as e:
        print(f"  ❌ [{i+1}] {src.name} 损坏，跳过: {e}")
        continue
    img = ImageOps.exif_transpose(img)  # 🔴 必须

    # 居中裁切
    ratio = TARGET_W / TARGET_H
    iw, ih = img.size
    if iw/ih > ratio:
        nw = int(ih * ratio)
        img = img.crop(((iw-nw)//2, 0, (iw-nw)//2+nw, ih))
    else:
        nh = int(iw / ratio)
        img = img.crop((0, (ih-nh)//2, iw, (ih-nh)//2+nh))
    img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)

    # 首图配"出租"（产品图，非真人图）
    if i == 0:
        font = ImageFont.truetype(FONT_PATH, size=FONT_SIZE)
        txt_layer = Image.new('RGBA', (TARGET_W, TARGET_H), (0,0,0,0))
        draw = ImageDraw.Draw(txt_layer)

        chars = "出租"
        total_w = sum(
            draw.textbbox((0,0), ch, font=font)[2] - draw.textbbox((0,0), ch, font=font)[0]
            for ch in chars
        )
        x_pos = (TARGET_W - total_w) // 2

        random.seed(42)
        for ch in chars:
            cw = draw.textbbox((0,0), ch, font=font)[2] - draw.textbbox((0,0), ch, font=font)[0]
            cx = x_pos + random.randint(-JITTER_X, JITTER_X)
            cy = TEXT_Y + random.randint(-JITTER_Y, JITTER_Y)
            draw.text((cx+SHADOW_OFFSET, cy+SHADOW_OFFSET), ch, font=font, fill=SHADOW_COLOR)
            draw.text((cx, cy), ch, font=font, fill=TEXT_COLOR)
            x_pos += cw

        img = Image.alpha_composite(img.convert('RGBA'), txt_layer).convert('RGB')

    tag_label = "🛒" if tag == "product" else "👤"
    out = OUT_DIR / f"xianyu_{i+1:02d}_{tag}.jpg"
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    img.save(out, quality=95)
    print(f"  [{i+1}] {tag_label} {src.name} → {out.name}")

print(f"\n✅ 完成！输出: {OUT_DIR}")
print(f"   共{total_needed}张（{PRODUCT_COUNT}产品 + {PERSON_COUNT}真人坐轮椅），首图已配\"出租\"")
print(f"\n📋 原图列表（发布后需标记(已发)）：")
for src, tag in all_picks:
    print(f"   {src}")
