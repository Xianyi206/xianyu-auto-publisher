# 🐟 Xianyu-Post — 闲鱼AI反检测自动发布机器人 / AI Anti-Detection Idle Fish Auto Publisher

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Idle%20Fish%20|%20闲鱼-ff5000?style=for-the-badge&logo=alibaba" alt="platform">
  <img src="https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python" alt="python">
  <img src="https://img.shields.io/badge/Anti--Detection-V21-success?style=for-the-badge" alt="anti-detection">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="license">
  <img src="https://img.shields.io/badge/Contributor-Dabao-orange?style=for-the-badge" alt="contributor">
</p>

<p align="center">
  <b>🇨🇳 闲鱼轮椅租赁图文全自动发布 | 🇬🇧 Smart image selection + auto crop + watermark + human-like publishing for Idle Fish (Xianyu)</b>
</p>

---

## 📖 中文 / English

### 🇨🇳 中文介绍

**闲鱼AI反检测自动发布机器人** — 专为闲鱼平台打造的100%全自动图文发布系统。

从 `D:\10 轮椅租赁` 素材库自动选5张图（4产品+1真人坐轮椅），居中裁剪1440×1920，首图配"出租"手写大字，Cookie注入绕过闲鱼反爬，120-180秒真人模拟发布。全程零人工干预。

#### 🔥 核心特性

| 特性 | 说明 |
|------|------|
| 🎨 **智能选图** | 从14个子目录自动选5张（4产品+1真人），主力不足自动从备用目录补选 |
| ✂️ **自动裁剪** | EXIF旋转修正 → 居中裁剪1440×1920 → 首图配"出租"手写字 |
| 🕵️ **V21反检测** | Cookie注入 + 随机延迟 + 拟人打字 + 非直线鼠标，120-180秒真人节奏 |
| 📋 **自动标记** | 发布成功自动标记原图`(已发)`，供抖音dy-post技能复用 |
| 🔄 **断连重试** | 网络驱动器超时探头 + 3次递增延迟重试 |
| 🪟 **Windows原生** | 完美适配Windows 11，Python 3.12+ |

#### 📊 发布节奏

每天6篇：`08:45 / 10:00 / 12:00 / 14:00 / 16:00 / 21:00`

#### 🚀 快速开始

```bash
# 图片预处理
python xianyu_process_images.py

# 发布到闲鱼
python xianyu_publish_v21.py
```

---

### 🇬🇧 English

**Xianyu Auto Publisher** — 100% automated image posting system for Alibaba's Idle Fish (Xianyu) marketplace.

Automatically selects 5 images (4 product + 1 person in wheelchair) from `D:\10 轮椅租赁` library, center-crops to 1440×1920, adds "出租" (rental) watermark on first image, injects cookies to bypass anti-bot detection, and publishes with human-like behavior in 120-180 seconds.

#### 🔥 Key Features

| Feature | Description |
|---------|-------------|
| 🎨 **Smart Selection** | Auto-pick 5 images from 14 product categories, with fallback directories |
| ✂️ **Auto Process** | EXIF rotation fix → 1440×1920 crop → hand-drawn watermark on cover |
| 🕵️ **V21 Anti-Detect** | Cookie injection + random delays + human typing + curved mouse moves |
| 📋 **Auto Tagging** | Marks source images `(已发)` for reuse by dy-post skill |
| 🔄 **Retry Logic** | Subprocess probe with 15s timeout + 3 retries (5s/10s/15s) |

#### 📊 Schedule

6 posts/day: `08:45 / 10:00 / 12:00 / 14:00 / 16:00 / 21:00` (CST)

#### 🚀 Quick Start

```bash
# Image preprocessing
python xianyu_process_images.py

# Publish to Xianyu
python xianyu_publish_v21.py
```

---

## 🏗️ 架构 / Architecture

```
xianyu-post/
├── README.md
├── xianyu_process_images.py    # 🎨 智能选图+裁剪+配字
├── xianyu_publish_v21.py       # 🔴 V21反检测发布（Cookie注入）
└── xianyu_login.py             # 🔑 登录态获取（Cookie过期时用）
```

---

## 📊 实战数据 / Production Stats

| 指标 / Metric | 数据 / Value |
|------|------|
| 总发布轮次 | 200+ (截至2026-05-25) |
| 成功率 | >95% |
| 单次耗时 | 120-180秒 |
| 素材库图片 | 2000+张（14个产品线） |
| 无反检测封号 | ✅ 0 |

---

## 🧩 技术栈 / Tech Stack

| 技术 | 用途 |
|------|------|
| `Pillow` | 图片EXIF修正、裁剪、配字 |
| `Playwright` | 浏览器自动化 + 反检测 |
| `CDP Protocol` | Chrome DevTools文件注入 |
| Cookie Injection | 绕过闲鱼反爬系统 |
| `subprocess` | 网络驱动器超时探头 |

---

## 🔗 生态协作 / Ecosystem

```
闲鱼先发 → 标记(已发) → 抖音dy-post跟发 → 标记(已发双平台)
```

配套项目：**[dy-post](https://github.com/DaBaoAgent/dy-post)** | **[xhs-post](https://github.com/DaBaoAgent/xhs-post)**

---

## 🤝 贡献者 / Contributor

| 角色 | 贡献 |
|------|------|
| **大宝 / Dabao (徐海平)** | 产品Owner、需求、Cookie提供 |
| **Hermes Agent** | AI驱动全流程开发、200+轮调试 |
| **Nous Research** | Hermes Agent框架 |

---

## ⚠️ 免责声明

本项目仅供技术交流学习，请遵守闲鱼平台使用条款。使用者自行承担合规责任。

---

## 📄 License

MIT © [DaBaoAgent](https://github.com/DaBaoAgent)

<p align="center">
  <b>Made with ❤️ by Dabao & Hermes Agent</b><br>
  <sub>2026 · 佳康顺医疗器械 · 昆山</sub>
</p>
