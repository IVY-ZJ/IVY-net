"""
Hugging Face Spaces 入口文件

在 Hugging Face Spaces 中设置以下 Secrets:
  - LLM_API_KEY: 你的 API Key
  - (可选) LLM_PROVIDER: deepseek / openai / qwen
  - (可选) LLM_API_BASE: API 地址
  - (可选) LLM_MODEL: 模型名称
"""

import os
import gradio as gr
from agent import Agent
from multi_agent import MultiAgentSystem
from memory import MemorySystem

# HF Spaces 中通过 os.environ 设置密钥
# 优先级: 环境变量 > .env 文件

memory = MemorySystem()
agent = Agent(memory=memory)
multi = MultiAgentSystem(memory=memory)


def chat_single(message, history):
    partial = ""
    for msg_type, content in agent.run_stream(message):
        if msg_type in ("token", "final"):
            partial += content
            yield partial
        elif msg_type in ("action", "observation", "think"):
            partial += f"\n{content}\n"
            yield partial


def chat_multi(message, history):
    partial = ""
    for msg_type, content in multi.run_stream(message):
        if msg_type == "token":
            partial += content
            yield partial
        else:
            partial += content
            yield partial


CSS = """
.gradio-container { max-width: 900px !important; margin: auto !important; }
footer { display: none !important; }
"""

with gr.Blocks(css=CSS, title="AI Agent — ReAct Framework") as demo:
    gr.Markdown("""
    # AI Agent Framework — 基于 ReAct 范式

    **工具**: calculator | wikipedia_search | file_reader | file_writer

    **模式**: 单 Agent（流式 ReAct）/ 多 Agent 协作（Planner + Executor）
    """)

    with gr.Tabs():
        with gr.TabItem("对话"):
            mode = gr.Radio(
                choices=["单 Agent（流式 ReAct）", "多 Agent 协作（Planner + Executor）"],
                value="单 Agent（流式 ReAct）",
                label="执行模式",
            )
            chatbot = gr.Chatbot(label="对话记录", height=450, bubble_full_width=False)
            msg = gr.Textbox(placeholder="输入你的问题...", label="输入", scale=9)
            with gr.Row():
                send_btn = gr.Button("发送", variant="primary")
                clear_btn = gr.Button("清空对话")

            def respond(message, history, mode_choice):
                fn = chat_multi if "多 Agent" in mode_choice else chat_single
                for resp in fn(message, history):
                    yield resp

            send_btn.click(respond, [msg, chatbot, mode], [chatbot]).then(lambda: "", outputs=[msg])
            msg.submit(respond, [msg, chatbot, mode], [chatbot]).then(lambda: "", outputs=[msg])
            clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])

        with gr.TabItem("关于"):
            gr.Markdown("""
            ## AI Agent Framework — 技术要点

            1. **Prompt 工程** — ReAct 范式 System Prompt
            2. **解析与执行循环** — 提取 Action → 执行工具 → 注入 Observation
            3. **对话历史管理** — 自动压缩为摘要

            **进阶功能**:
            - 流式输出（逐 token 实时展示）
            - 短期记忆 + 长期记忆
            - 多 Agent 协作（Planner + Executor）
            """)

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=1)
    demo.launch(server_name="0.0.0.0", server_port=7860)