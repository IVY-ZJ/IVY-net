"""
多 Agent 协作模块 —— 规划 Agent + 执行 Agent

规划 Agent：将复杂任务拆解为步骤列表
执行 Agent：逐步执行每个子任务，将上一步结果传递给下一步
"""

from openai import OpenAI
from config import load_config
from tools import (
    TOOL_NAMES, TOOL_MAP,
    calculator, wikipedia_search, file_reader, file_writer,
)
from utils import extract_action_and_action_input
from memory import MemorySystem

MAX_STEPS = 10  # 规划最大步骤数
MAX_ITERATIONS_PER_STEP = 8


class PlannerAgent:
    """规划 Agent —— 接收原始任务，拆解为执行步骤"""

    def __init__(self, memory: MemorySystem = None):
        config = load_config()
        self.client = OpenAI(
            api_key=config["api_key"],
            base_url=config["api_base"],
        )
        self.model = config["model"]
        self.memory = memory or MemorySystem()

    def plan(self, task: str) -> list:
        """
        将复杂任务拆解为可执行步骤

        Args:
            task: 用户原始任务

        Returns:
            步骤列表，每项为 (step_number, description)
        """
        system = f"""你是一个任务规划专家。将用户任务拆解为可执行的步骤列表。

可用工具: {TOOL_NAMES}

规则:
1. 每步应能用单个工具调用完成
2. 步骤之间可以有依赖（后续步骤使用前面步骤的结果）
3. 普通对话、不需要工具的问题，拆为 1 步即可
4. 以 JSON 数组格式输出，每项含 "step"（序号）和 "description"（步骤描述）
5. 只输出 JSON 数组，不要其他文字

示例:
输入: "查爱因斯坦出生年份，然后算他活了多少岁"
输出: [{{"step":1,"description":"wikipedia_search 查爱因斯坦的出生和去世年份"}},{{"step":2,"description":"calculator 计算去世年份减出生年份"}}]
"""

        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": task},
            ],
        )
        text = resp.choices[0].message.content

        # 解析 JSON
        import re
        import json
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                steps = json.loads(match.group())
                return [(s["step"], s["description"]) for s in steps]
            except json.JSONDecodeError:
                pass

        # 解析失败，回退为单步
        return [(1, task)]


class ExecutorAgent:
    """执行 Agent —— 逐步执行规划好的子任务"""

    def __init__(self, memory: MemorySystem = None):
        config = load_config()
        self.client = OpenAI(
            api_key=config["api_key"],
            base_url=config["api_base"],
        )
        self.model = config["model"]
        self.temperature = config["temperature"]
        self.memory = memory or MemorySystem()

    def execute_step(self, step_desc: str, context: str = "") -> str:
        """
        执行单个步骤，返回结果

        Args:
            step_desc: 步骤描述
            context: 前面步骤的累积结果

        Returns:
            本步骤执行结果
        """
        system = f"""你是一个 ReAct 执行 Agent。执行以下步骤并返回结果。

可用工具: {TOOL_NAMES}

你必须严格遵循格式:
Thought: 你的思考
Action: 工具名
Action Input: 参数
（等待 Observation 后继续）
Thought: 我现在知道结果了
Final Answer: 本步骤的结果（简洁，保留关键数字和事实）
"""
        if context:
            system += f"\n\n前面步骤的结果:\n{context}"

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Question: {step_desc}"},
        ]

        for _ in range(MAX_ITERATIONS_PER_STEP):
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                messages=messages,
                stop=["Observation:"],
            )
            text = resp.choices[0].message.content

            action, action_input = extract_action_and_action_input(text)

            if action:
                tool_func = TOOL_MAP.get(action)
                if tool_func:
                    if action == "file_writer":
                        result = tool_func(*action_input)
                    else:
                        result = tool_func(action_input)
                else:
                    result = f"未知工具: {action}"

                messages.extend([
                    {"role": "assistant", "content": text},
                    {"role": "user", "content": f"Observation: {result}"},
                ])
            else:
                if "Final Answer:" in text:
                    idx = text.find("Final Answer:")
                    return text[idx + len("Final Answer:"):].strip()
                else:
                    messages.extend([
                        {"role": "assistant", "content": text},
                        {"role": "user", "content": "请按格式输出 Thought/Action/Action Input 或 Final Answer。"},
                    ])

        return "本步骤未能完成。"


# ================= 多 Agent 协作入口 =================

class MultiAgentSystem:
    """多 Agent 协作系统：Planner + Executor"""

    def __init__(self, memory: MemorySystem = None):
        self.memory = memory or MemorySystem()
        self.planner = PlannerAgent(self.memory)
        self.executor = ExecutorAgent(self.memory)

    def run(self, task: str) -> str:
        """
        完整执行流程: 规划 → 逐步执行 → 汇总

        Args:
            task: 用户原始任务

        Returns:
            最终汇总结果
        """
        # ---------- 阶段 1: 规划 ----------
        print("=" * 60)
        print("[规划 Agent] 正在拆解任务...")
        plan = self.planner.plan(task)
        print(f"[规划 Agent] 拆解为 {len(plan)} 个步骤:")
        for step_num, desc in plan:
            print(f"  步骤 {step_num}: {desc}")
        print()

        # ---------- 阶段 2: 逐步执行 ----------
        results = []
        context = ""

        for step_num, desc in plan:
            print(f"[执行 Agent] 正在执行步骤 {step_num}: {desc}")
            result = self.executor.execute_step(desc, context)
            print(f"[执行 Agent] 步骤 {step_num} 完成: {result[:200]}")
            results.append((step_num, desc, result))
            context += f"\n步骤 {step_num} ({desc}) 结果: {result}"
            print()

        # ---------- 阶段 3: 汇总 ----------
        print("[汇总] 所有步骤完成，生成最终回答...")
        summary_prompt = f"""根据以下步骤的结果，回答用户的原始问题。

用户问题: {task}

各步骤结果:
{context}

请给出完整、连贯的最终回答。"""
        resp = self.planner.client.chat.completions.create(
            model=self.planner.model,
            temperature=0.3,
            messages=[{"role": "user", "content": summary_prompt}],
        )
        final = resp.choices[0].message.content

        # 记忆
        self.memory.add_message("user", task)
        self.memory.add_message("assistant", final)

        return final

    def run_stream(self, task: str):
        """
        流式版本：多 Agent 协作 + 流式输出
        yield (type, content)
        type: "phase" / "step_start" / "step_result" / "final" / "token"
        """
        # 规划阶段
        yield ("phase", "[规划 Agent] 正在拆解任务...\n")
        plan = self.planner.plan(task)
        yield ("phase", f"拆解为 {len(plan)} 个步骤:\n")
        for step_num, desc in plan:
            yield ("phase", f"  步骤 {step_num}: {desc}\n")
        yield ("phase", "\n")

        # 执行阶段
        results = []
        context = ""
        for step_num, desc in plan:
            yield ("step_start", f"[执行 Agent] 步骤 {step_num}: {desc}\n")
            result = self.executor.execute_step(desc, context)
            yield ("step_result", f"  结果: {result[:300]}\n\n")
            results.append((step_num, desc, result))
            context += f"\n步骤 {step_num} ({desc}) 结果: {result}"

        # 汇总阶段
        summary_prompt = f"""根据以下步骤的结果，回答用户的原始问题。

用户问题: {task}

各步骤结果:
{context}

请给出完整、连贯的最终回答。"""

        stream = self.planner.client.chat.completions.create(
            model=self.planner.model,
            temperature=0.3,
            messages=[{"role": "user", "content": summary_prompt}],
            stream=True,
        )

        yield ("phase", "\n[汇总] 最终回答:\n")
        full_text = ""
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_text += token
                yield ("token", token)

        self.memory.add_message("user", task)
        self.memory.add_message("assistant", full_text)
        yield ("final", full_text)