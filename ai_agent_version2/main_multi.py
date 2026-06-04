"""
命令行入口 —— 多 Agent 协作模式（Planner + Executor）
"""

import sys
from multi_agent import MultiAgentSystem


def main():
    system = MultiAgentSystem()

    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        print("=" * 60)
        print("AI Agent — 多 Agent 协作模式 (Planner + Executor)")
        print("工具: calculator | wikipedia_search | file_reader | file_writer")
        print("输入 'exit' 退出")
        print("=" * 60)
        print()
        task = input("请输入任务: ").strip()

        if not task or task.lower() == "exit":
            return

    print()
    result = system.run(task)
    print("\n" + "=" * 60)
    print("最终结果:")
    print(result)


if __name__ == "__main__":
    main()