"""
命令行入口 —— 单 Agent 模式（流式 ReAct）
"""

import sys
from agent import Agent


def main():
    agent = Agent()

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        print("=" * 60)
        print("AI Agent — ReAct 框架 (单 Agent 模式)")
        print("工具: calculator | wikipedia_search | file_reader | file_writer")
        print("输入 'exit' 退出")
        print("=" * 60)
        print()
        question = input("请输入问题: ").strip()

        if not question or question.lower() == "exit":
            return

    print("\n执行中...\n")
    agent.run(question, verbose=True)


if __name__ == "__main__":
    main()