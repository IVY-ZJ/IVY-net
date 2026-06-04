"""
记忆系统模块

短期记忆：当前会话的对话历史 + 最近 N 轮摘要
长期记忆：跨会话持久化存储（JSON 文件），记录用户偏好和重要事实
"""

import json
import os
from datetime import datetime
from openai import OpenAI


class MemorySystem:
    """
    记忆系统：短期 + 长期记忆

    短期记忆：维护当前会话的完整对话历史，超出长度时自动压缩旧消息为摘要
    长期记忆：将用户偏好、重要事实持久化到 JSON，跨会话加载
    """

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_store.json")
        self.storage_path = storage_path
        self.short_term: list = []          # 当前会话消息列表
        self.summary: str = ""              # 被压缩的历史摘要
        self.long_term: dict = self._load_long_term()
        self.max_short_messages = 20        # 短消息上限，超出则压缩

    # ==================== 长期记忆 ====================

    def _load_long_term(self) -> dict:
        """从文件加载长期记忆"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, dict) else {}
            except Exception:
                return {}
        return {}

    def _save_long_term(self):
        """将长期记忆写入文件"""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.long_term, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Memory] 保存长期记忆失败: {e}")

    def remember_fact(self, key: str, value: str):
        """记录一个事实到长期记忆"""
        self.long_term[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
        }
        self._save_long_term()

    def recall_facts(self) -> str:
        """返回长期记忆的文本描述，供 System Prompt 注入"""
        if not self.long_term:
            return ""
        lines = ["\n[用户长期记忆]"]
        for key, entry in self.long_term.items():
            value = entry["value"] if isinstance(entry, dict) else entry
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    # ==================== 短期记忆 ====================

    def add_message(self, role: str, content: str):
        """向短期记忆添加一条消息"""
        self.short_term.append({"role": role, "content": content})

    def get_messages(self) -> list:
        """获取当前有效的消息列表（含摘要前缀）"""
        messages = []
        if self.summary:
            messages.append({
                "role": "system",
                "content": f"[历史摘要] {self.summary}"
            })
        messages.extend(self.short_term)
        return messages

    def compress(self, llm_client, model: str):
        """
        当短消息超出上限时，将最旧的消息压缩为摘要。
        调用 LLM 生成一段摘要文本，替代被移除的旧消息。
        """
        if len(self.short_term) <= self.max_short_messages:
            return

        # 取最旧的 N 条消息用于摘要
        old_messages = self.short_term[: len(self.short_term) // 2]
        self.short_term = self.short_term[len(self.short_term) // 2 :]

        # 构造摘要请求
        conversation_text = "\n".join(
            f"{m['role']}: {m['content'][:300]}" for m in old_messages
        )
        try:
            resp = llm_client.chat.completions.create(
                model=model,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": "将以下对话压缩为一段简洁的摘要（不超过200字），只保留关键事实和结论。"},
                    {"role": "user", "content": conversation_text},
                ],
            )
            new_summary = resp.choices[0].message.content
            # 合并新旧摘要
            if self.summary:
                self.summary = f"{self.summary}; {new_summary}"
            else:
                self.summary = new_summary
        except Exception as e:
            print(f"[Memory] 压缩失败: {e}")

    def clear_short_term(self):
        """清空短期记忆（保留摘要）"""
        self.short_term = []