"""
解析工具 —— 从 LLM 输出中提取 Action 和 Action Input
"""

import ast
import re


def clean_parentheses(s: str) -> str:
    """
    去除末尾多余的右括号，使括号匹配。
    处理 LLM 偶尔多输出一个 ) 的情况。
    """
    opens = s.count("(")
    closes = s.count(")")
    while closes > opens and s.endswith(")"):
        s = s[:-1]
        closes -= 1
    return s


def extract_action_and_action_input(text: str):
    """
    从 LLM 回复中解析 Action 和 Action Input。

    支持格式:
      Action: calculator
      Action Input: "2 + 3"

    也支持不带引号的参数和元组格式。

    Returns:
        (action: str, action_input: Any) 或 (None, None)
    """
    action_match = re.search(r"Action:\s*(.+?)(?:\n|$)", text)
    action_input_match = re.search(r"Action Input:\s*(.+?)(?:\n|$)", text)

    if not action_match or not action_input_match:
        return None, None

    action = action_match.group(1).strip()
    action_input_raw = action_input_match.group(1).strip()

    # 针对不同工具类型处理 Action Input
    if action == "file_writer":
        # file_writer 需要元组: (path, content)
        try:
            cleaned = clean_parentheses(action_input_raw)
            parsed = ast.literal_eval(cleaned)
            if isinstance(parsed, (tuple, list)) and len(parsed) >= 2:
                return action, (str(parsed[0]), str(parsed[1]))
            return action, action_input_raw
        except Exception:
            return action, action_input_raw

    elif action in ("calculator", "wikipedia_search", "file_reader"):
        # 这些工具接受纯字符串
        # 去掉可能的多余引号
        if action_input_raw.startswith('"') and action_input_raw.endswith('"'):
            action_input_raw = action_input_raw[1:-1]
        elif action_input_raw.startswith("'") and action_input_raw.endswith("'"):
            action_input_raw = action_input_raw[1:-1]
        return action, action_input_raw

    else:
        # 未知工具
        return action, action_input_raw


def shorten(text: str, width: int = 600) -> str:
    """压缩空白并截断文本"""
    if not text:
        return ""
    collapsed = " ".join(text.split())
    if len(collapsed) <= width:
        return collapsed
    return collapsed[:width] + "..."