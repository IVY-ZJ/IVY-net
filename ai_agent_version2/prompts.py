"""
Prompt 构建模块 —— 构建 System Prompt 和对话历史
"""

from datetime import datetime


# ================== System Prompt ==================

def build_system_prompt() -> str:
    current_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""你是一个具备工具调用能力的 AI Agent。你必须严格按照 ReAct 格式输出。

当前日期时间: {current_dt}

## 可用工具

1. **calculator** — 安全计算器，支持四则运算、括号、幂运算等。输入一个数学表达式字符串，返回计算结果。
   示例: Action Input: "2 + 3 * (4 - 1)"

2. **wikipedia_search** — 搜索维基百科，返回相关页面的摘要信息。输入搜索关键词字符串。
   示例: Action Input: "Albert Einstein"

3. **file_reader** — 读取本地文件内容。输入文件绝对路径字符串。
   示例: Action Input: "D:/documents/note.txt"

4. **file_writer** — 将内容写入本地文件。输入为 (文件路径, 文件内容) 元组。
   示例: Action Input: ("D:/output/result.txt", "Hello World")

## 输出格式

你必须严格按照以下格式输出，每轮只输出一个 Action:

Question: 用户问题
Thought: 我对当前情况的分析和下一步计划
Action: 工具名
Action Input: 参数
Observation: 工具返回结果
... (Thought/Action/Action Input/Observation 可重复多次)
Thought: 我现在已经得到最终答案
Final Answer: 最终答案

## 重要规则

1. 所有数学计算必须使用 calculator 工具，不要自己心算
2. 需要最新/外部信息时使用 wikipedia_search
3. Action 必须是 calculator / wikipedia_search / file_reader / file_writer 之一
4. Action Input 必须格式正确：calculator 和 wikipedia_search 是纯字符串；file_writer 是元组
5. 不要在 Thought 中写最终答案，最终答案必须放在 Final Answer 后面
6. Final Answer 要完整、连贯地回答原始问题"""


# ================== 对话历史管理 ==================

MAX_HISTORY_TOKENS = 4000  # 估算阈值


def build_chat_history(question: str) -> list:
    """构建初始对话历史"""
    return [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": f"Question: {question}"},
    ]


def compress_chat_history(messages: list) -> list:
    """
    压缩过长对话历史：保留 system prompt + 最后 N 轮 + 摘要中间部分
    替换被删除部分为一句话摘要
    """
    if len(messages) <= 3:
        return messages  # system + 用户 + assistant 就 3 条，不压缩

    system_msg = messages[0]
    recent = messages[-6:]  # 保留最后 3 轮 (6 条)
    middle = messages[1:-6]  # 中间部分

    if not middle:
        return messages

    # 用简单规则生成摘要（生产环境可用 LLM 做更精准的摘要）
    summary_parts = []
    for m in middle:
        content = str(m.get("content", ""))
        if "Observation:" in content:
            # 只保留 Observation 中的关键数据
            obs_start = content.find("Observation:")
            summary_parts.append(content[obs_start:obs_start + 200])

    summary = "先前对话摘要: " + ("; ".join(summary_parts[:3]) if summary_parts else "已执行多个工具调用。")
    summary_msg = {"role": "user", "content": summary}

    return [system_msg, summary_msg] + recent