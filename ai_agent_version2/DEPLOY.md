# AI Agent Framework — 部署教程

> 零基础可操作，每一步都有截图说明和命令对照。全程约 15 分钟。

---

## 部署架构

```
你的电脑 → GitHub（代码仓库）→ Hugging Face Spaces（免费云托管）
                                    ↓
                           https://你的用户名-ai-agent.hf.space
```

---

## 阶段一：推送到 GitHub（5 分钟）

### 1.1 安装 Git

如果已经装了，跳到 1.2。

- 访问 https://git-scm.com/download/win
- 下载 64-bit Git for Windows Setup，一路 Next 安装即可
- 安装完成后，在桌面右键 → "Open Git Bash here" 验证：

```bash
git --version
# 应输出类似: git version 2.47.0
```

### 1.2 注册 GitHub 账号

- 访问 https://github.com/signup
- 用邮箱注册，免费账号即可
- 注册后创建一个新仓库（New Repository）：
  - Repository name: `ai-agent`
  - 选择 Public（公开）
  - 不要勾选 "Add a README file"
  - 点击 "Create repository"

### 1.3 配置 Git 用户信息

在 Git Bash 中执行：

```bash
git config --global user.name "你的GitHub用户名"
git config --global user.email "你的注册邮箱"
```

### 1.4 推送项目到 GitHub

打开 Git Bash，逐条执行：

```bash
# 进入项目目录
cd "/c/Users/Li Xiang/Desktop/ai_agent_version2"

# 初始化 Git
git init

# 添加所有文件
git add .

# 首次提交
git commit -m "初始版本: AI Agent ReAct 框架"

# 关联远程仓库（把下面的 YOUR_USERNAME 换成你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/ai-agent.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

推送成功后在浏览器刷新 GitHub 仓库页面，应该能看到所有 15 个文件。

> 如果 `git push` 报错 "Authentication failed"，需要在 GitHub 创建 Personal Access Token。
> 操作：GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token → 勾选 repo 权限 → 生成后把 token 当密码填入。

---

## 阶段二：部署到 Hugging Face Spaces（5 分钟）

### 2.1 注册 Hugging Face

- 访问 https://huggingface.co/join
- 免费注册即可

### 2.2 创建 Space

- 登录后点击右上角头像 → "+ New Space"
- 填写配置：

| 字段 | 值 |
|------|-----|
| Owner | 你的用户名 |
| Space name | ai-agent |
| License | MIT |
| Space SDK | **Gradio** |
| Gradio Version | 4.44.0 |
| Space Hardware | CPU (免费) |
| Public / Private | Public |

- 点击 "Create Space"

### 2.3 关联 GitHub 仓库

创建成功后，页面会进入 Space 主页。此时项目还是空的，需要关联 GitHub：

- 点击 "Settings" 标签页
- 找到 "Connected Git Repo" 区域
- 填入你的 GitHub 仓库地址：`https://github.com/YOUR_USERNAME/ai-agent`
- 点击 "Set as upstream repo"

### 2.4 设置 API Key Secret

- 在 Settings 标签页，找到 "Repository Secrets" 区域
- 点击 "New Secret"

| Secret Name | Secret Value |
|-------------|--------------|
| LLM_API_KEY | sk-你的API Key |

- 点击 "Add secret"

如果使用 DeepSeek 以外的模型，还需添加：

| Secret Name | Secret Value |
|-------------|--------------|
| LLM_PROVIDER | openai（或 deepseek/qwen） |
| LLM_API_BASE | https://api.openai.com/v1（可选） |
| LLM_MODEL | gpt-4o（可选） |

### 2.5 触发部署

- 切换到 "Settings" 的 "Factory reboot" 区域
- 点击 "Factory reboot"  → "Reboot"
- Space 会自动从 GitHub 拉取代码并构建

等待 2-3 分钟，状态变为 "Running" 即部署完成。

### 2.6 访问你的 Web UI

浏览器打开：`https://huggingface.co/spaces/YOUR_USERNAME/ai-agent`

或者直接：`https://YOUR_USERNAME-ai-agent.hf.space`

---

## 阶段三：测试（2 分钟）

在 Web UI 的输入框输入：

```
查一下爱因斯坦的出生年份，然后算一下他活了多少岁
```

如果看到 Agent 调用 wikipedia_search 获取信息、calculator 计算年龄，说明部署成功。

---

## 常见问题

| 问题 | 解决方案 |
|------|---------|
| Space 构建报错 "ModuleNotFoundError" | 检查 requirements.txt 是否正确推送到了 GitHub |
| Space 构建成功但运行报错 | 检查 Secret 中 LLM_API_KEY 是否设置 |
| Gradio 版本不兼容 | README.md 头部 YAML 中 `sdk_version` 写为 `"4.44.0"` |
| "No space left on device" | 免费版有一定磁盘限制，确认没提交大文件 |
| 国内访问 Hugging Face 慢 | 使用镜像或 VPN |

---

## 后续更新代码

本地修改代码后，重新推送即可自动触发 Space 重新部署：

```bash
cd "/c/Users/Li Xiang/Desktop/ai_agent_version2"
git add .
git commit -m "描述你的改动"
git push
```

推送后 Hugging Face Space 会自动检测并重新构建，无需手动操作。