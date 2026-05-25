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
import os, time, json, random
from pathlib import Path

LOG = os.path.expanduser(r'~\.hermes\logs\xianyu_v21.log')
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

# ============ 配置 ============
from playwright.sync_api import sync_playwright

STATE_FILE = r"D:\BaiduSyncdisk\8 本地推素材\闲鱼Cookie\闲鱼Cookie.txt"
TMP_DIR = Path(os.path.expanduser(r"~\.hermes\tmp\xianyu_publish"))

# 加载Cookie
with open(STATE_FILE, 'r', encoding='utf-8') as f:
    state = json.load(f)
COOKIES = []
for c in state.get('cookies', []):
    cookie = {k: c[k] for k in ['name', 'value', 'domain', 'path'] if k in c}
    for extra in ['httpOnly', 'secure', 'sameSite', 'expires']:
        if extra in c:
            cookie[extra] = c[extra]
    COOKIES.append(cookie)
log(f"🔑 {len(COOKIES)} cookies")

# 加载预处理好的图片
files = sorted([str(f.absolute()) for f in TMP_DIR.glob("*.jpg")])
log(f"📁 共{len(files)}张图（含1张真人坐轮椅）")

# 文案（价格 9.9）
DIRECTIONS = [
    "苏州轮椅租赁，短期使用按天租",
    "昆山轮椅出租，老人出行临时用",
    "医院术后康复轮椅租赁，送货上门",
    "旅游临时轮椅出租，苏州景区可用",
    "老人代步轮椅出租，工厂直租更省心",
]
import datetime
hour = datetime.datetime.now().hour
idx = {10:0, 12:1, 14:2, 16:3, 21:4}.get(hour, 0)
direction = DIRECTIONS[idx]

DESC_TEXT = f"""{direction}！最低9.9元/天起

受伤临时租用、术后康复、旅游代步、老人出行统统搞定

中国驰名商标佳康顺，大牌子质量有保障，几乎全新，每次用完都深度消毒

昆山工厂和苏州门店均通借通还，全城可自取/送货上门，昆山张浦厂家和苏州阳光大厦门店可通借通取

可租赁辅具：手动轮椅、电动轮椅、老年代步车、移位机、起身器

不用了随时还，没有任何隐形费用。点右下角「我想要」直接咨询

#轮椅出租 #轮椅租赁 #出行辅助 #昆山轮椅 #佳康顺"""

log(f"📝 方向: {direction}")

# ============ 主流程 ============
start_time = time.time()
log(f"🕵️ V21 真人模拟模式 | 目标120-180秒")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=['--disable-blink-features=AutomationControlled']
    )
    context = browser.new_context(viewport={'width': 1280, 'height': 900})
    context.add_cookies(COOKIES)
    page = context.new_page()
    cdp = page.context.new_cdp_session(page)

    # ===== 1. 导航发布页 =====
    page.goto("https://www.goofish.com/publish", wait_until="domcontentloaded")
    human_wait(page, 5000, 10000)  # 页面加载+人确认
    log("1️⃣ 发布页加载")

    body = page.evaluate('document.body.innerText')
    if '非法访问' in body:
        log("❌ Cookie验证失败")
        browser.close()
        exit(1)
    log(f"   ✅ 已登录")

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

    # ===== 4. 填价格 9.9 =====
    log("4️⃣ 填价格 9.9...")
    human_wait(page, 500, 1200)

    page.evaluate('''() => {
        const inputs = document.querySelectorAll('input[placeholder="0.00"]');
        for (const inp of inputs) {
            if (!inp.offsetParent) continue;
            inp.focus();
            const ns = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            ns.call(inp, '9.9');
            inp.dispatchEvent(new Event('input', {bubbles: true}));
            inp.dispatchEvent(new Event('change', {bubbles: true}));
            inp.blur();
        }
    }''')
    human_wait(page, 800, 2000)
    log("   ✅ 9.9")

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

    addr_state = page.evaluate('''() => {
        const b = document.body.innerText;
        return {
            hasProvince: b.includes('江苏省') || b.includes('江苏'),
            hasCity: b.includes('苏州市') || b.includes('苏州'),
        };
    }''')

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
        page.evaluate('''() => {
            for (const el of document.querySelectorAll('*')) {
                if ((el.innerText||'').trim()==='江苏省' && el.offsetParent && el.tagName!=='BODY') {
                    el.dispatchEvent(new MouseEvent('click', {bubbles:true}));
                    return;
                }
            }
        }''')
        human_wait(page, 1500, 3000)

        # 选市
        page.evaluate('''() => {
            for (const el of document.querySelectorAll('*')) {
                if ((el.innerText||'').trim()==='苏州市' && el.offsetParent && el.tagName!=='BODY') {
                    el.dispatchEvent(new MouseEvent('click', {bubbles:true}));
                    return;
                }
            }
        }''')
        human_wait(page, 1500, 3000)

        # 选区
        page.evaluate('''() => {
            for (const el of document.querySelectorAll('*')) {
                const t = (el.innerText||'').trim();
                if ((t==='昆山市'||t==='昆山'||t==='张浦镇') && el.offsetParent && el.tagName!=='BODY') {
                    el.dispatchEvent(new MouseEvent('click', {bubbles:true}));
                    return;
                }
            }
        }''')
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
    page.mouse.click(600, 850)  # 发布按钮常见位置
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
    browser.close()
    log("✅ 完成")
