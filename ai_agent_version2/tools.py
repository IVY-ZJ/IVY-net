"""
工具定义模块 —— calculator / wikipedia_search / file_reader / file_writer
"""

import ast
import operator
import math
import os
import re
import requests


# ================== 1. Calculator ==================

# AST 安全白名单：只允许数学运算和安全的内置函数
SAFE_NODES = {
    ast.Expression, ast.Constant, ast.BinOp, ast.UnaryOp, ast.Call,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
    ast.USub, ast.UAdd,
    ast.Name, ast.Load,
    ast.Tuple, ast.List,
}

SAFE_BUILTINS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "int": int,
    "float": float,
    "sum": sum,
    "pow": pow,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
}


class UnsafeExpressionError(Exception):
    pass


def _validate_ast(node):
    """递归验证 AST 节点是否在白名单内"""
    if type(node) not in SAFE_NODES:
        raise UnsafeExpressionError(f"禁止的 AST 节点: {type(node).__name__}")
    if isinstance(node, ast.Name):
        if node.id not in SAFE_BUILTINS:
            raise UnsafeExpressionError(f"禁止的标识符: {node.id}")
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise UnsafeExpressionError("禁止的属性调用")
        if node.func.id not in SAFE_BUILTINS:
            raise UnsafeExpressionError(f"禁止的函数: {node.func.id}")
    for child in ast.iter_child_nodes(node):
        _validate_ast(child)


def calculator(expression: str) -> str:
    """
    安全计算数学表达式。

    使用 AST 白名单防止代码注入，仅允许四则运算和安全的数学函数。

    Args:
        expression: 数学表达式字符串，如 "2 + 3 * (4 - 1)" 或 "sqrt(16) + log(100)"

    Returns:
        计算结果字符串
    """
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        _validate_ast(tree)
        compiled = compile(tree, "<calculator>", "eval")
        namespace = SAFE_BUILTINS.copy()
        result = eval(compiled, {"__builtins__": {}}, namespace)
        # 格式化输出
        if isinstance(result, float):
            if result == int(result):
                return str(int(result))
            return f"{result:.10g}"
        return str(result)
    except UnsafeExpressionError as e:
        return f"错误: 表达式包含不允许的操作 — {e}"
    except SyntaxError as e:
        return f"错误: 表达式语法无效 — {e}"
    except ZeroDivisionError:
        return "错误: 不能除以零"
    except Exception as e:
        return f"错误: {e}"


# ================== 2. Wikipedia Search ==================

WIKI_API = "https://en.wikipedia.org/api/rest_v1"


def wikipedia_search(query: str) -> str:
    """
    搜索维基百科并返回页面摘要。

    Args:
        query: 搜索关键词

    Returns:
        格式化的搜索结果
    """
    url = f"{WIKI_API}/page/summary/{requests.utils.quote(query)}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            title = data.get("title", query)
            extract = data.get("extract", "无摘要")
            desc = data.get("description", "")
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

            result = f"【{title}】\n"
            if desc:
                result += f"描述: {desc}\n"
            result += f"\n{extract[:1500]}"
            if page_url:
                result += f"\n\n来源: {page_url}"
            return result
        elif resp.status_code == 404:
            return f"未找到关于 '{query}' 的维基百科页面。"
        else:
            return f"维基百科请求失败: HTTP {resp.status_code}"
    except requests.exceptions.Timeout:
        return "维基百科请求超时。"
    except Exception as e:
        return f"维基百科搜索出错: {e}"


# ================== 3. File Reader ==================

def file_reader(file_path: str) -> str:
    """
    读取本地文件内容。

    Args:
        file_path: 文件绝对路径

    Returns:
        文件内容字符串（最多 5000 字符）
    """
    try:
        if not os.path.exists(file_path):
            return f"文件不存在: {file_path}"
        if not os.path.isfile(file_path):
            return f"路径不是文件: {file_path}"

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read(5000)
        return content if len(content) < 5000 else content + "\n...(内容已截断)"
    except UnicodeDecodeError:
        return f"无法以 UTF-8 读取文件: {file_path}（可能是二进制文件）"
    except PermissionError:
        return f"没有权限读取文件: {file_path}"
    except Exception as e:
        return f"读取文件出错: {e}"


# ================== 4. File Writer ==================

def file_writer(file_path: str, content: str) -> str:
    """
    将内容写入本地文件。

    Args:
        file_path: 目标文件绝对路径
        content: 要写入的内容

    Returns:
        操作结果描述
    """
    try:
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"文件已写入: {file_path} ({len(content)} 字符)"
    except PermissionError:
        return f"没有权限写入文件: {file_path}"
    except Exception as e:
        return f"写入文件出错: {e}"


# ================== 工具注册表 ==================

TOOL_NAMES = ["calculator", "wikipedia_search", "file_reader", "file_writer"]

TOOL_MAP = {
    "calculator": calculator,
    "wikipedia_search": wikipedia_search,
    "file_reader": file_reader,
    "file_writer": file_writer,
}