"""
Gradio Web 界面 —— AI Agent 可视化交互

功能:
- 单 Agent 模式（流式输出）
- 多 Agent 协作模式（Planner + Executor）
- 对话历史展示
- 记忆管理面板

部署方式:
  python web_ui.py
  然后访问 http://localhost:7860

部署到 Hugging Face Spaces（与 GitHub 联动）:
  1. 将整个项目 push 到 GitHub
  2. 在 https://huggingface.co/spaces 创建 Space，选择 Gradio SDK
  3. 关联 GitHub 仓库即可自动部署
"""

import gradio as gr
from agent import Agent
from multi_agent import MultiAgentSystem
from memory import MemorySystem


# ================= 全局实例 =================
memory = MemorySystem()
agent = Agent(memory=memory)
multi = MultiAgentSystem(memory=memory)


# ================= 回调函数 =================

def chat_single(message: str, history: list):
    """单 Agent 模式 - 流式输出"""
    partial = ""
    for msg_type, content in agent.run_stream(message):
        if msg_type in ("token", "final"):
            partial += content
            yield partial
        elif msg_type == "action":
            partial += f"\n{content}\n"
            yield partial
        elif msg_type == "observation":
            partial += f"\n{content}\n"
            yield partial
        elif msg_type == "think":
            partial += f"\n{content}"
            yield partial


def chat_multi(message: str, history: list):
    """多 Agent 协作模式 - 流式输出"""
    partial = ""
    for msg_type, content in multi.run_stream(message):
        if msg_type == "token":
            partial += content
            yield partial
        else:
            partial += content
            yield partial


def get_memory_info():
    """获取记忆系统状态"""
    short_count = len(memory.short_term)
    long_count = len(memory.long_term)
    summary_len = len(memory.summary)

    long_text = ""
    for key, entry in memory.long_term.items():
        value = entry["value"] if isinstance(entry, dict) else entry
        long_text += f"- {key}: {value}\n"

    return (
        f"**短期记忆**: {short_count} 条消息\n"
        f"**摘要长度**: {summary_len} 字符\n\n"
        f"**长期记忆** ({long_count} 条):\n{long_text or '(无)'}"
    )


def clear_memory():
    """清空短期记忆"""
    memory.clear_short_term()
    return "短期记忆已清空。长期记忆保留。"


def add_fact(key: str, value: str):
    """手动添加长期记忆"""
    if key.strip() and value.strip():
        memory.remember_fact(key.strip(), value.strip())
        return f"已记录: {key} = {value}"
    return "请输入键和值"


# ================= Gradio UI 构建 =================

CSS = """
.gradio-container { max-width: 900px !important; margin: auto !important; }
footer { display: none !important; }
"""

with gr.Blocks(css=CSS, title="AI Agent — ReAct 框架") as demo:
    gr.Markdown("""
    # AI Agent Framework — 基于 ReAct 范式

    **工具**: calculator | wikipedia_search | file_reader | file_writer

    **模式**: 单 Agent（流式 ReAct 循环）/ 多 Agent 协作（规划 + 执行）
    """)

    with gr.Tabs():
        # ---------- Tab 1: 对话 ----------
        with gr.TabItem("对话"):
            with gr.Row():
                mode = gr.Radio(
                    choices=["单 Agent（流式 ReAct）", "多 Agent 协作（Planner + Executor）"],
                    value="单 Agent（流式 ReAct）",
                    label="执行模式",
                )

            chatbot = gr.Chatbot(
                label="对话记录",
                height=450,
                bubble_full_width=False,
            )
            msg = gr.Textbox(
                placeholder="输入你的问题，例如：查一下爱因斯坦的出生年份，然后算一下他活了多少岁",
                label="输入",
                scale=9,
            )
            with gr.Row():
                send_btn = gr.Button("发送", variant="primary")
                clear_btn = gr.Button("清空对话")

            def respond(message, history, mode_choice):
                if mode_choice == "多 Agent 协作（Planner + Executor）":
                    fn = chat_multi
                else:
                    fn = chat_single
                for resp in fn(message, history):
                    yield resp

            send_btn.click(
                respond,
                inputs=[msg, chatbot, mode],
                outputs=[chatbot],
            ).then(lambda: "", outputs=[msg])

            msg.submit(
                respond,
                inputs=[msg, chatbot, mode],
                outputs=[chatbot],
            ).then(lambda: "", outputs=[msg])

            clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])

        # ---------- Tab 2: 记忆管理 ----------
        with gr.TabItem("记忆管理"):
            gr.Markdown("### 记忆系统状态")
            memory_status = gr.Markdown("加载中...")

            refresh_btn = gr.Button("刷新状态")
            refresh_btn.click(get_memory_info, outputs=[memory_status])

            clear_mem_btn = gr.Button("清空短期记忆", variant="secondary")
            clear_mem_btn.click(clear_memory, outputs=[memory_status])

            gr.Markdown("---")
            gr.Markdown("### 添加长期记忆")
            with gr.Row():
                fact_key = gr.Textbox(label="键", placeholder="例如: 用户名字")
                fact_value = gr.Textbox(label="值", placeholder="例如: 张三")
            add_fact_btn = gr.Button("记录")
            add_fact_result = gr.Textbox(label="结果")
            add_fact_btn.click(
                add_fact,
                inputs=[fact_key, fact_value],
                outputs=[add_fact_result],
            ).then(get_memory_info, outputs=[memory_status])

        # ---------- Tab 3: 关于 ----------
        with gr.TabItem("关于"):
            gr.Markdown("""
            ## AI Agent Framework

            **核心技术要点:**

            1. **Prompt 工程** — ReAct 范式 System Prompt，交替输出 Thought 和 Action
            2. **解析与执行循环** — 提取 Action/Action Input，执行工具，注入 Observation
            3. **对话历史管理** — messages 列表维护，超出长度自动压缩为摘要

            **工具:**

            | 工具 | 功能 |
            |------|------|
            | `calculator` | 安全数学表达式求值（AST 白名单） |
            | `wikipedia_search` | 维基百科搜索和摘要获取 |
            | `file_reader` | 读取本地文件内容 |
            | `file_writer` | 写入本地文件 |

            **进阶功能:**

            - 流式输出（逐 token 实时展示）
            - 短期记忆（会话上下文 + 自动压缩）
            - 长期记忆（跨会话持久化存储）
            - 多 Agent 协作（规划 Agent + 执行 Agent）

            **GitHub:** [项目地址](#)
            """)


# ================= 启动 =================

if __name__ == "__main__":
    # 页面加载时初始化记忆状态
    demo.load(get_memory_info, outputs=[demo.select_blocks["记忆管理"].blocks[1]])

    demo.queue(default_concurrency_limit=1)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )