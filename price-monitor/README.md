# 价格观察站

**黄金 · 石油 · 内存 · 硬盘 · CPU 每日价格跟踪与周期分析**

纯文字静态站点，无图片，无外部依赖，自动更新，安全运行。

---

## 一、站点功能

| 功能 | 说明 |
|------|------|
| **5类27项价格跟踪** | 金价（实时API）、石油、内存、硬盘、CPU |
| **每日自动更新** | GitHub Actions 每天 09:00(北京时间) 自动采集 + 部署 |
| **每日归档页** | 365天历史快照，每页独立可访问 |
| **周/月/年对比报告** | ASCII 趋势图、涨跌幅、30日预测区间、原因分析 |
| **停产标注** | 已停产型号标注红色「停产」标签及停产时间 |

---

## 二、服务器信息

### 免费托管：GitHub Pages

| 项目 | 值 |
|------|-----|
| **服务商** | GitHub Pages (免费) |
| **站点地址** | `https://<你的用户名>.github.io/<仓库名>` |
| **域名** | github.io 子域名（或自定义 CNAME） |
| **SSL** | 自动 HTTPS |
| **CDN** | 全球 CDN 分发 |
| **存储限制** | 1GB 免费（当前约 15MB） |
| **带宽限制** | 100GB/月免费 |
| **运行时间** | 99.9% SLA |
| **费用** | **完全免费** |

> ⚠️ 如需更换其他免费平台：
> - **Vercel** — `vercel deploy` 即用
> - **Cloudflare Pages** — `wrangler pages publish public`
> - **Netlify** — `netlify-cli deploy --dir=public`

---

## 三、账号与凭据

### 你需要准备的账号

| 账号 | 用途 | 注册地址 | 费用 |
|------|------|---------|------|
| **GitHub** | 主站部署 + Actions 自动任务 | https://github.com/signup | 免费 |
| **GitLab** | 备份空间1 | https://gitlab.com/users/sign_up | 免费 |
| **Gitee** | 备份空间2 | https://gitee.com/signup | 免费 |
| **GitHub PAT**（可选） | 手动推送权限（如不用 SSH） | Settings → Developer settings → Personal access tokens | 免费 |

### 凭据配置步骤

#### 1) GitHub Personal Access Token（用于 API 访问）
```
1. 登录 GitHub → 右上角头像 → Settings
2. 左侧菜单 → Developer settings → Personal access tokens → Tokens (classic)
3. Generate new token → 勾选 repo 权限
4. 复制 token（形如 ghp_xxxxxxxxxxxx）
5. 存到安全位置，不要泄露
```

#### 2) GitLab / Gitee 配置备份 Remote
```bash
cd price-monitor

# GitLab
git remote add gitlab git@gitlab.com:<用户名>/price-monitor.git

# Gitee
git remote add gitee git@gitee.com:<用户名>/price-monitor.git

# 或使用 HTTPS 方式（需输入密码）
git remote add gitlab https://gitlab.com/<用户名>/price-monitor.git
git remote add gitee https://gitee.com/<用户名>/price-monitor.git
```

#### 3) 站点管理员查看口令（可选）

本站为**纯静态站点**，无登录后台。如需保护敏感页面，可在 `.github/workflows/daily.yml` 中加入密码验证逻辑。

---

## 四、部署指令

### 首次部署（完整步骤）

```bash
# ===== 步骤1：Fork 或 Clone 本仓库到你的 GitHub =====
git clone https://github.com/<你的用户名>/price-monitor.git
cd price-monitor

# ===== 步骤2：启用 GitHub Pages =====
# 在 GitHub 仓库页面：
#   Settings → Pages → Source 选择 "Deploy from a branch"
#   Branch 选 "gh-pages"，目录选 "/ (root)"
#   点 Save

# ===== 步骤3：启用 GitHub Actions =====
# 将 .github/workflows/daily.yml 推送到 main 分支即可自动激活
# Actions 会每天北京时间 09:00 运行采集+部署

# ===== 步骤4：首次手动触发（不等明天）=====
# 在仓库页面 → Actions → "每日价格更新与部署" → Run workflow

# ===== 步骤5：访问站点 =====
# 约 2 分钟后访问 https://<用户名>.github.io/price-monitor/
```

### 日常同步操作指令

```bash
cd /path/to/price-monitor

# 更新代码后推送到三个备份空间
./scripts/backup.sh

# 手动触发一次采集+构建+本地预览
python3 scripts/fetch.py        # 采集今日数据
python3 scripts/build.py        # 生成站点
python3 -m http.server 8080 --directory public  # 本地预览 http://localhost:8080
```

### 三备份空间完整同步流程

```bash
#!/bin/bash
# 完整同步脚本示例（保存为 sync_all.sh）
set -euo pipefail

cd ~/price-monitor

echo "=== [1] 采集 ===" && python3 scripts/fetch.py
echo "=== [2] 回填 ===" && python3 scripts/backfill.py 7
echo "=== [3] 构建 ===" && python3 scripts/build.py
echo "=== [4] 提交 ===" && \
    git add -A && \
    git commit -m "auto-update: $(date '+%Y-%m-%d')" || true
echo "=== [5] GitHub ===" && git push origin main
echo "=== [6] GitLab ===" && git push gitlab main || echo "GitLab 未配置"
echo "=== [7] Gitee ==="  && git push gitee main  || echo "Gitee 未配置"
echo "=== 完成 $(date) ==="

# 加入 crontab 实现每日自动同步（可选，与 GitHub Actions 冗余但更可控）
# 0 */6 * * * cd ~/price-monitor && bash ~/sync_all.sh >> /tmp/price-sync.log 2>&1
```

---

## 五、安全措施

本站已内置以下安全防护：

| 安全项 | 措施 |
|--------|------|
| **无服务端注入** | 纯静态 HTML，无后端处理用户输入 |
| **XSS 防护** | 所有输出经 `html.escape()` 转义 |
| **无外部资源** | CSS 内联，不加载 CDN/第三方 JS |
| **无 Cookie/Session** | 无状态，无需认证 |
| **HTTPS 强制** | GitHub Pages 自动提供 TLS |
| **供应链安全** | 零第三方依赖（仅 Python 标准库 + requests） |
| **数据不可篡改** | Git 版本控制，每次提交哈希可审计 |
| **无数据库暴露** | 数据以 JSON 文件存于私有仓库分支 |
| **CORS 不适用** | 静态文件直接分发 |

### 额外安全建议
- 仓库设置为 Private（数据 JSON 含在 history 目录中）
- GitHub Token 仅给最小权限（repo scope）
- 定期检查 Actions 日志有无异常
- 如需公开展示，确保 data/history 不被意外 push 到公开 gh-pages 分支

---

## 六、项目文件结构

```
price-monitor/
├── .github/workflows/
│   └── daily.yml          # GitHub Actions 自动更新配置
├── data/
│   ├── latest.json        # 最新价格数据
│   ├── history/           # 每日历史快照 (YYYY-MM-DD.json)
│   └── reports/           # 周期报告缓存
├── public/                # 生成的静态站点（部署目标）
│   ├── index.html         # 首页（今日价格）
│   ├── archive/           # 每日归档页 (364页)
│   │   └── index.html     # 归档索引
│   ├── weekly/index.html  # 周报
│   ├── monthly/index.html # 月报
│   └── yearly/index.html  # 年报
├── scripts/
│   ├── models.py          # 型号数据库（五类27项，含停产标注）
│   ├── fetch.py           # 每日价格采集脚本
│   ├── backfill.py        # 历史回填脚本
│   ├── analyze.py         # 分析预测模块
│   ├── build.py           # 站点生成器
│   └── backup.sh          # 三备份同步脚本
└── README.md              # 本文档
```

---

## 七、技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3.11 | 数据处理 + 页面生成 |
| 生成方式 | 静态 HTML + 内联 CSS | 零外部依赖 |
| 字体 | 系统等宽字体 | SF Mono / Consolas / Liberation Mono |
| 数据格式 | JSON | 人机可读，版本控制友好 |
| 图表 | Unicode Sparkline | 纯文字字符画趋势图 |
| 部署 | GitHub Pages + Actions | 免费自动化 |
| 备份 | Git 多 Remote | GitHub + GitLab + Gitee |

---

## 八、常见问题

**Q: 金价是真实数据吗？**
A: 国际金价通过 gold-api.com 公开接口获取（实时），国内金价按汇率换算。硬件类为参考价（标注模拟），基于日期种子的确定性波动。

**Q: 能加更多型号吗？**
A: 编辑 `scripts/models.py` 的 MODELS 字典即可。每个条目需 name/category/unit/base/discontinued/note 五个字段。

**Q: 如何修改更新时间？**
A: 编辑 `.github/workflows/daily.yml` 的 cron 表达式。默认 UTC 01:00 = 北京时间 09:00。

**Q: 罙站能自定义域名吗？**
A: 可以。在仓库根目录创建 `CNAME` 文件写入域名，DNS 配置 CNAME 到 `<user>.github.io`。

---

*生成时间: 2026-07-06*
