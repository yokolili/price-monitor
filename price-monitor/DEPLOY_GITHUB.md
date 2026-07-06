# GitHub Pages 部署指南（傻瓜式）

## 你只需做 3 件事

### ① 注册 GitHub（仅需邮箱，免手机）
打开 https://github.com/signup → 填邮箱+密码 → 验证邮箱 → 完成
（无需信用卡、无需手机验证）

### ② 新建空仓库
1. 右上角 `+` → New repository
2. Repository name 填：`price-monitor`
3. **不要**勾选 "Add a README file"
4. 点 Create repository

### ③ 本地运行 3 条命令
（项目已 git init 并提交，你只需连接并推送）

```bash
# 把下面 <你的GitHub用户名> 换成你的用户名
git remote add origin https://github.com/<你的GitHub用户名>/price-monitor.git

git branch -M main
git push -u origin main
```

推送时会要求输入用户名和密码：
- **用户名**：你的 GitHub 账号
- **密码**：用 **Personal Access Token**（不是登录密码！）
  - 生成地址：https://github.com/settings/tokens
  - 勾选 `repo` 权限 → Generate → 复制 `ghp_xxx`

---

## 启用自动部署（一次性）

推送成功后：
1. 仓库页面 → **Settings** → **Pages**
2. Source 选 **Deploy from a branch**
3. Branch 选 **gh-pages** → **/ (root)** → Save
4. 等待 2 分钟

## 🌐 你的站点地址

```
https://<你的GitHub用户名>.github.io/price-monitor/
```

首次访问可能需等 1-2 分钟（Actions 在后台跑首次采集+构建）。

---

## 可选：让我代你 push（如果你愿意给 token）

如果你不想自己跑命令，把这两样发我，我直接帮你推上去并给地址：
- 你的 GitHub 用户名
- 一个有 `repo` 权限的 Personal Access Token（`ghp_xxx`）

我会执行：
```bash
git remote add origin https://<token>@github.com/<用户>/price-monitor.git
git push -u origin main
```
推送后 Actions 自动部署，地址同上。

---

## 自动更新机制（已内置）

`.github/workflows/daily.yml` 已配置：
- 每天 **北京时间 09:00** 自动运行
- 执行：采集今日价格 → 回填历史 → 重新生成站点 → 部署到 gh-pages
- 你完全不用管，站点每天自动更新

手动触发：仓库 → Actions → 选工作流 → Run workflow

---

## 验证清单
- [ ] GitHub 账号已注册（邮箱）
- [ ] 仓库 `price-monitor` 已创建（空仓库）
- [ ] `git push` 成功（用 token 当密码）
- [ ] Settings → Pages 已选 gh-pages 分支
- [ ] 访问 `https://<用户>.github.io/price-monitor/` 显示站点
