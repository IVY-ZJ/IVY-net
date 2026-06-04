"""
增强版 Agent —— 支持流式输出、记忆系统
"""

from openai import OpenAI
from config import load_config
from prompts import build_system_prompt, build_chat_history
from tools import TOOL_NAMES, TOOL_MAP
from utils import extract_action_and_action_input
from memory import MemorySystem

MAX_ITERATIONS = 15


class Agent:
    """ReAct Agent —— 支持流式输出 + 记忆系统"""

    def __init__(self, memory: MemorySystem = None):
        config = load_config()
        self.client = OpenAI(
            api_key=config["api_key"],
            base_url=config["api_base"],
        )
        self.model = config["model"]
        self.temperature = config["temperature"]
        self.memory = memory or MemorySystem()

    def _init_chat_history(self, question: str) -> list:
        """构建初始对话历史（含记忆注入）"""
        system = build_system_prompt()
        # 注入长期记忆
        facts = self.memory.recall_facts()
        if facts:
            system += "\n" + facts

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Question: {question}"},
        ]

    # ================= 流式输出模式 =================

    def run_stream(self, question: str):
        """
        流式执行 ReAct 循环，逐 token yield 输出
        返回生成器：(type, content)
          type: "think" / "action" / "observation" / "final" / "token"
        """
        chat_history = self._init_chat_history(question)

        for iteration in range(1, MAX_ITERATIONS + 1):
            # ----- 流式调用 LLM -----
            full_text = ""
            stream = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=chat_history,
                stop=["Observation:"],
                stream=True,
            )

            yield ("think", f"\n### ReAct 循环 #{iteration}\n")

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_text += token
                    yield ("token", token)

            # ----- 解析 Action -----
            action, action_input = extract_action_and_action_input(full_text)

            if action:
                yield ("action", f"\n>>> 执行: {action}({action_input})")

                tool_func = TOOL_MAP.get(action)
                if tool_func:
                    if action == "file_writer":
                        action_result = tool_func(*action_input)
                    else:
                        action_result = tool_func(action_input)
                else:
                    action_result = f"未知工具: {action}"

                yield ("observation", f"\n>>> 结果: {action_result}")

                chat_history.extend([
                    {"role": "assistant", "content": full_text},
                    {"role": "user", "content": f"Observation: {action_result}"},
                ])
            else:
                if "Final Answer:" in full_text:
                    idx = full_text.find("Final Answer:")
                    yield ("final", full_text[idx:])
                    # 保存到短期记忆
                    self.memory.add_message("user", question)
                    self.memory.add_message("assistant", full_text[idx:])
                    # 尝试提取长期记忆
                    self._extract_long_term_memory(question, full_text[idx:])
                    return
                else:
                    yield ("action", "\n>>> 格式无效，重新提示...")
                    chat_history.extend([
                        {"role": "assistant", "content": full_text},
                        {"role": "user", "content": (
                            "你的输出格式不正确。你必须提供有效的 Action 和 Action Input。"
                            f"Action 必须是 {TOOL_NAMES} 之一。"
                        )},
                    ])

        yield ("final", "达到最大循环次数，未能完成任务。")

    # ================= 非流式模式（兼容旧接口） =================

    def run(self, question: str, verbose: bool = True) -> str:
        """非流式执行（兼容旧接口）"""
        final_answer = ""
        for msg_type, content in self.run_stream(question):
            if verbose and msg_type != "token":
                print(content, end="", flush=True)
            if msg_type == "token" and verbose:
                print(content, end="", flush=True)
            if msg_type == "final":
                final_answer = content
        if verbose:
            print()
        return final_answer

    # ================= 长期记忆提取 =================

    def _extract_long_term_memory(self, question: str, final_answer: str):
        """从对话中自动提取可能需要长期记住的事实"""
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": (
                        "从以下对话中判断是否有值得长期记住的用户偏好或重要事实。"
                        "如果有，以 JSON 格式返回: {\"key\": \"简短键名\", \"value\": \"事实内容\"}。"
                        "如果没有值得长期记住的内容，返回: {\"skip\": true}。"
                        "只输出 JSON，不要其他文字。"
                    )},
                    {"role": "user", "content": f"Q: {question}\nA: {final_answer[:500]}"},
                ],
            )
            text = resp.choices[0].message.content.strip()
            if "skip" not in text:
                import re
                m = re.search(r'"key"\s*:\s*"([^"]+)"\s*,\s*"value"\s*:\s*"([^"]+)"', text)
                if m:
                    self.memory.remember_fact(m.group(1), m.group(2))
        except Exception:
            pass  # 静默失败，不影响主流程