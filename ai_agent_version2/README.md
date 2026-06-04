---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: e09b297cf2db44360f14aebe3dcf0280_2076740f601311f1960a5254007bceed
    ReservedCode1: DXw0wFOaBtr2tEOCNOJOpObz7mrVmWXt7gN4clptCnRHjMGyz+zjkfXXJ42rSSDjlsqgO5wIJefompn+6heigAdpddoSnwv9yyOhwQbLAPjRquArE6F+hFifPRbCkll4F5IvskKZqQgsa+Un/5fUAXCzOzRneQO9JJJ8f12+Y3Uvu+Pf4Hyb64npDBo=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: e09b297cf2db44360f14aebe3dcf0280_2076740f601311f1960a5254007bceed
    ReservedCode2: DXw0wFOaBtr2tEOCNOJOpObz7mrVmWXt7gN4clptCnRHjMGyz+zjkfXXJ42rSSDjlsqgO5wIJefompn+6heigAdpddoSnwv9yyOhwQbLAPjRquArE6F+hFifPRbCkll4F5IvskKZqQgsa+Un/5fUAXCzOzRneQO9JJJ8f12+Y3Uvu+Pf4Hyb64npDBo=
---



# AI Agent Framework — 基于 ReAct 范式

基于 ReAct (Reasoning + Acting) 范式的 AI Agent，具备流式输出、记忆系统和多 Agent 协作能力。可直接部署到 Hugging Face Spaces。

## 一键部署到 Hugging Face Spaces

1. **Fork 本仓库**
2. 在 Hugging Face Spaces 创建新 Space，选择 Gradio SDK
3. 关联你的 GitHub 仓库
4. 设置 Secret: `LLM_API_KEY` = 你的 API Key
5. （可选）设置 `LLM_PROVIDER`、`LLM_API_BASE`、`LLM_MODEL`
6. Space 自动构建并上线

## 本地运行

```bash
git clone <repo_url>
cd ai-agent
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入 API Key
python web_ui.py
```

访问 http://localhost:7860

## 命令行使用

```bash
python main.py           # 单 Agent 模式
python main_multi.py     # 多 Agent 协作模式
```

## 架构

```
用户输入 → Agent (ReAct 循环)
                ├── Thought → Action → Observation → ...
                ├── 流式输出 (逐 token)
                ├── 短期记忆 (自动压缩摘要)
                └── 长期记忆 (跨会话持久化)

多 Agent 模式:
用户输入 → Planner Agent (任务拆解)
                ↓
         Executor Agent → Step 1 → Step 2 → ... → 汇总
```

## 可用工具

| 工具 | 功能 |
|------|------|
| `calculator` | 安全数学表达式求值 |
| `wikipedia_search` | 维基百科搜索 |
| `file_reader` | 读取本地文件 |
| `file_writer` | 写入本地文件 |

## 文件结构

```
ai_agent/
├── agent.py          # 增强版 Agent（流式+记忆）
├── multi_agent.py    # 多 Agent 协作（Planner + Executor）
├── web_ui.py         # 本地 Web 界面
├── app.py            # HF Spaces 入口
├── main.py           # 命令行入口（单 Agent）
├── main_multi.py     # 命令行入口（多 Agent）
├── config.py         # 配置加载
├── prompts.py        # Prompt 构建
├── tools.py          # 工具定义
├── utils.py          # 解析工具
├── memory.py         # 记忆系统
├── requirements.txt  # Python 依赖
├── .env.example      # 配置文件模板
└── README.md         # 本文件
```
*（内容由AI生成，仅供参考）*
