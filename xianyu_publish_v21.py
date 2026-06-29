"""
闲鱼发布 V21 — 真人模拟反检测版
- 所有间隔随机化（120-180秒总耗时）
- 拟人打字 + 鼠标移动
- 价格 9.9元/天
- 5张图（4产品+1真人坐轮椅），首图已配"出租"

用法：
  1. 先跑 xianyu_process_images.py 处理图片
  2. 再跑本脚本发布
  /c/Users/xxx13/AppData/Local/Programs/Python/Python312/python.exe ^
    ~/.hermes/skills/multi-platform-uploader/xianyu-post/scripts/xianyu_publish_v21.py
"""
import os, sys, time, json, random, yaml
from pathlib import Path

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

LOG = config['paths']['log_file']
os.makedirs(os.path.dirname(LOG), exist_ok=True)

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    print(msg, flush=True)

# ============ 反检测工具函数 ============

def human_wait(page, min_ms=300, max_ms=2000):
    """随机等待"""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)
    return delay

def human_type(page, text):
    """拟人打字：不等速、偶尔卡顿、换行停顿"""
    total = 0
    for ch in text:
        delay = random.randint(60, 120)
        if random.random() < 0.05:
            delay += random.randint(200, 500)
        page.keyboard.type(ch, delay=delay)
        total += delay
    return total

def human_move(page, x, y):
    """鼠标从随机位置非直线滑到目标"""
    sx = random.randint(100, 1100)
    sy = random.randint(100, 700)
    page.mouse.move(sx, sy)
    human_wait(page, 80, 250)
    steps = random.randint(2, 3)
    for i in range(1, steps+1):
        mx = sx + (x-sx)*i//steps + random.randint(-20, 20)
        my = sy + (y-sy)*i//steps + random.randint(-15, 15)
        page.mouse.move(mx, my)
        human_wait(page, 40, 120)

# ============ 配置（从 config.yaml 读取） ============
from playwright.sync_api import sync_playwright

TMP_DIR = Path(config['paths']['tmp_dir'])

# 持久化用户数据目录（Playwright 自动管理登录态）
USER_DATA_DIR = os.environ.get(
    'XIANYU_USER_DATA_DIR',
    os.path.expanduser('~/.hermes/xianyu_browser_profile')
)
os.makedirs(USER_DATA_DIR, exist_ok=True)
log(f"🔑 持久化目录: {USER_DATA_DIR}")

# 加载预处理好的图片
files = sorted([str(f.absolute()) for f in TMP_DIR.glob("*.jpg")])
log(f"📁 共{len(files)}张图（含1张真人坐轮椅）")

pub = config['publish']

# 方向文案（价格 9.9）
DIRECTIONS = pub['directions']
import datetime
hour = datetime.datetime.now().hour
idx = {10:0, 12:1, 14:2, 16:3, 21:4}.get(hour, 0)
direction = DIRECTIONS[idx]

DESC_TEMPLATE = pub['description']
DESC_TEXT = DESC_TEMPLATE.format(direction=direction)

log(f"📝 方向: {direction}")

PRICE_STR = str(pub['price'])
VIEWPORT_W = pub['viewport_width']
VIEWPORT_H = pub['viewport_height']
PROVINCE = pub['province']
CITY = pub['city']
DISTRICT = pub['district']
PUB_BTN_X = pub['publish_button_x']
PUB_BTN_Y = pub['publish_button_y']

# ============ 主流程 ============
start_time = time.time()
log(f"🕵️ V21 真人模拟模式 | 目标120-180秒")

with sync_playwright() as p:
    # 启动持久化浏览器（崩溃自动重建 profile）
    context = None
    for attempt in range(3):
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                viewport={'width': VIEWPORT_W, 'height': VIEWPORT_H},
                args=['--disable-blink-features=AutomationControlled']
            )
            break
        except Exception as e:
            log(f"⚠️ 浏览器启动失败 (尝试{attempt+1}/3): {e}")
            if os.path.exists(USER_DATA_DIR):
                import shutil
                shutil.rmtree(USER_DATA_DIR, ignore_errors=True)
                log("   已清除损坏的 profile")
    if context is None:
        log("❌ 浏览器启动失败，退出")
        sys.exit(1)
    page = context.new_page()
    cdp = context.new_cdp_session(page)

    # ===== 0. 登录检查 =====
    # 直接在发布页登录（闲鱼首页和发布页是两套独立认证，首页cookie带不过去）
    log("0️⃣ 登录检查...")
    page.goto("https://www.goofish.com/publish", wait_until="domcontentloaded")
    human_wait(page, 3000, 5000)
    has_form = page.query_selector('[contenteditable="true"]') or page.query_selector('input[type="file"]')
    
    if not has_form:
        log("🔐 需要登录。请在浏览器中点击「立即登录」扫码（最多等120秒）...")
        for _ in range(120):
            page.wait_for_timeout(1000)
            has_form = page.query_selector('[contenteditable="true"]') or page.query_selector('input[type="file"]')
            if has_form:
                log("✅ 登录成功")
                break
        else:
            log("❌ 登录超时")
            context.close()
            exit(1)
    else:
        log("✅ 已登录（从持久化上下文恢复）")

    # 确认在发布页，有表单
    human_wait(page, 3000, 6000)
    has_publish_form = page.query_selector('[contenteditable="true"]') or page.query_selector('input[type="file"]')
    if not has_publish_form:
        log("❌ 发布表单未加载，请确认已登录")
        context.close()
        exit(1)
    log("1️⃣ 发布表单已就绪")

    # 随意晃动鼠标（模拟浏览）
    human_move(page, random.randint(300, 900), random.randint(100, 400))
    human_wait(page, 500, 1500)

    # ===== 2. 上传图片 =====
    log("2️⃣ 上传图片...")
    human_wait(page, 800, 2000)

    file_input = page.query_selector('input[type="file"]')
    if file_input:
        file_input.set_input_files(files)
        log("   ✅ set_input_files")
    else:
        doc = cdp.send('DOM.getDocument')
        root_id = doc['root']['nodeId']
        node_ids = cdp.send('DOM.querySelectorAll', {
            'nodeId': root_id, 'selector': 'input[type="file"]'
        })['nodeIds']
        if node_ids:
            cdp.send('DOM.setFileInputFiles', {'files': files, 'nodeId': node_ids[-1]})
            log("   ✅ CDP upload")

    # 等上传完成 — 最长的等待
    upload_wait = random.randint(15000, 25000)
    log(f"   ⏳ 等待上传...({upload_wait}ms)")
    page.wait_for_timeout(upload_wait)

    # 随意滚动
    page.mouse.wheel(0, random.randint(100, 300))
    human_wait(page, 300, 800)

    # ===== 3. 填描述（拟人打字） =====
    log("3️⃣ 填描述...")
    human_wait(page, 600, 1500)

    desc_div = page.locator('[contenteditable="true"]').first
    if desc_div.count() > 0:
        desc_div.click()
        human_wait(page, 300, 800)
        page.keyboard.press('Control+a')
        human_wait(page, 100, 250)
        page.keyboard.press('Backspace')
        human_wait(page, 200, 500)

        lines = DESC_TEXT.split('\n')
        for i, line in enumerate(lines):
            if i > 0:
                page.keyboard.press('Enter')
                human_wait(page, 200, 500)
            if line:
                human_type(page, line)
            human_wait(page, 80, 250)

        page.keyboard.press('Tab')  # 触发React onChange
        human_wait(page, 300, 700)

        desc_len = page.evaluate('''() => {
            const d = document.querySelector('[contenteditable="true"]');
            return d ? d.innerText.length : 0;
        }''')
        log(f"   {desc_len}字 {'✅' if desc_len > 10 else '❌'}")
    else:
        log("   ❌ 找不到描述框")

    human_wait(page, 1500, 3500)

    # ===== 4. 填价格 =====
    log(f"4️⃣ 填价格 {PRICE_STR}...")
    human_wait(page, 500, 1200)

    page.evaluate(f'''() => {{
        const inputs = document.querySelectorAll('input[placeholder="0.00"]');
        for (const inp of inputs) {{
            if (!inp.offsetParent) continue;
            inp.focus();
            const ns = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            ns.call(inp, '{PRICE_STR}');
            inp.dispatchEvent(new Event('input', {{bubbles: true}}));
            inp.dispatchEvent(new Event('change', {{bubbles: true}}));
            inp.blur();
        }}
    }}''')
    human_wait(page, 800, 2000)
    log(f"   ✅ {PRICE_STR}")

    # ===== 5. 包邮 =====
    log("5️⃣ 包邮...")
    human_wait(page, 400, 1000)
    page.evaluate('''() => {
        for (const el of document.querySelectorAll('*')) {
            if ((el.innerText||'').trim()==='包邮' && el.offsetParent) {
                el.dispatchEvent(new MouseEvent('click', {bubbles:true}));
                return;
            }
        }
    }''')
    human_wait(page, 1000, 2500)
    log("   ✅")

    # ===== 6. 宝贝所在地 =====
    log("6️⃣ 所在地...")
    human_wait(page, 500, 1200)

    addr_state = page.evaluate(f'''() => {{
        const b = document.body.innerText;
        return {{
            hasProvince: b.includes('{PROVINCE}') || b.includes('{CITY}'),
            hasCity: b.includes('{CITY}'),
        }};
    }}''')

    if not addr_state['hasProvince']:
        page.evaluate('''() => {
            for (const el of document.querySelectorAll('*')) {
                if ((el.innerText||'').trim()==='请选择' && el.offsetParent && !el.children.length) {
                    el.dispatchEvent(new MouseEvent('click', {bubbles:true}));
                    return;
                }
            }
        }''')
        human_wait(page, 2000, 4000)

        # 选省
        page.evaluate(f'''() => {{
            for (const el of document.querySelectorAll('*')) {{
                if ((el.innerText||'').trim()==='{PROVINCE}' && el.offsetParent && el.tagName!=='BODY') {{
                    el.dispatchEvent(new MouseEvent('click', {{bubbles:true}}));
                    return;
                }}
            }}
        }}''')
        human_wait(page, 1500, 3000)

        # 选市
        page.evaluate(f'''() => {{
            for (const el of document.querySelectorAll('*')) {{
                if ((el.innerText||'').trim()==='{CITY}' && el.offsetParent && el.tagName!=='BODY') {{
                    el.dispatchEvent(new MouseEvent('click', {{bubbles:true}}));
                    return;
                }}
            }}
        }}''')
        human_wait(page, 1500, 3000)

        # 选区
        page.evaluate(f'''() => {{
            for (const el of document.querySelectorAll('*')) {{
                const t = (el.innerText||'').trim();
                if ((t==='{DISTRICT}'||t==='{CITY}'||t==='张浦镇') && el.offsetParent && el.tagName!=='BODY') {{
                    el.dispatchEvent(new MouseEvent('click', {{bubbles:true}}));
                    return;
                }}
            }}
        }}''')
        human_wait(page, 1500, 3000)
    log("   ✅")

    # ===== 7. 检查+发布 =====
    log("7️⃣ 发布...")
    human_wait(page, 2000, 5000)

    # Force enable
    page.evaluate('''() => {
        for (const btn of document.querySelectorAll('button')) {
            if ((btn.innerText||'').trim()==='发布') {
                btn.disabled = false;
                btn.style.pointerEvents = 'auto';
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
                const cls = btn.className || '';
                btn.className = cls.replace(/publish-button-disabled[^ ]*/g, '');
                return;
            }
        }
    }''')
    human_wait(page, 500, 1500)

    # 鼠标滑到按钮位置再点
    page.mouse.click(PUB_BTN_X, PUB_BTN_Y)  # 发布按钮常见位置
    human_wait(page, 12000, 18000)  # 等待发布结果

    log(f"   URL: {page.url}")

    if '/item?id=' in page.url:
        item_id = page.url.split('/item?id=')[-1].split('&')[0]
        log(f"\n🎉 发布成功! Item ID: {item_id}")
        log(f"🔗 https://www.goofish.com/item?id={item_id}")
    else:
        body = page.evaluate('document.body.innerText.substring(0, 300)')
        log(f"   ⚠️ 未跳转: {body[:200]}")

        # 最后重试：原生click
        page.evaluate('''() => {
            for (const btn of document.querySelectorAll('button')) {
                if ((btn.innerText||'').trim()==='发布') {
                    btn.click();
                    return;
                }
            }
        }''')
        human_wait(page, 8000, 12000)
        log(f"   重试后URL: {page.url}")

        if '/item?id=' in page.url:
            item_id = page.url.split('/item?id=')[-1].split('&')[0]
            log(f"\n🎉 重试成功! Item ID: {item_id}")

    elapsed = time.time() - start_time
    log(f"\n⏱️ 总耗时: {elapsed:.1f}秒 {'✅ 2-3分钟' if 120<=elapsed<=180 else f'⚠️ {elapsed:.0f}s'}")

    human_wait(page, 2000, 5000)
    context.close()
    log("✅ 完成")
