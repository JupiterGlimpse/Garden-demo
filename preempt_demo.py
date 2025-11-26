"""
Preempt - Cursor 风格的动态 Prompt 构建系统
灵感来自 React/JSX，用声明式方式构建智能 prompt

核心思路：
1. 组件化：每个内容块是一个组件（文件、对话历史、文档等）
2. 优先级：类似 CSS z-index，定义什么内容更重要
3. 动态渲染：根据 token 限制，自动决定保留什么内容
"""

import tiktoken
from typing import List, Dict, Any, Callable
from dataclasses import dataclass, field


@dataclass
class PromptComponent:
    """
    类似 React 组件的 Prompt 片段
    """
    name: str                          # 组件名称
    content: str | Callable[[], str]   # 内容（可以是函数，延迟计算）
    priority: int = 1                  # 优先级（越高越重要）
    min_tokens: int = 0                # 最小 token 数（低于这个数就不显示）
    max_tokens: int | None = None      # 最大 token 数（超过会截断）
    _cached_content: str = field(default="", init=False, repr=False)

    def render(self) -> str:
        """渲染内容"""
        if callable(self.content):
            self._cached_content = self.content()
        else:
            self._cached_content = self.content
        return self._cached_content

    def get_token_count(self, encoding) -> int:
        """计算 token 数"""
        if not self._cached_content:
            self.render()
        return len(encoding.encode(self._cached_content))


class FileComponent(PromptComponent):
    """
    文件组件 - Cursor 风格的智能文件展示
    光标所在行优先级最高，距离越远优先级越低
    """
    def __init__(self, file_path: str, content: str, cursor_line: int | None = None):
        self.file_path = file_path
        self.full_content = content
        self.cursor_line = cursor_line

        # 动态计算优先级的内容
        def smart_content():
            lines = self.full_content.split('\n')

            if self.cursor_line is None:
                # 没有光标位置，返回全部
                return f"File: {self.file_path}\n```\n{self.full_content}\n```"

            # 以光标为中心，计算每行的优先级
            result_lines = []
            for i, line in enumerate(lines, start=1):
                distance = abs(i - self.cursor_line)
                # 距离越远，优先级越低（在这里我们用标记表示）
                result_lines.append(f"{i:4d} | {line}")

            # 光标行高亮
            result_lines[self.cursor_line - 1] = f">>> {result_lines[self.cursor_line - 1]} <<<"

            return f"File: {self.file_path}\n```\n" + '\n'.join(result_lines) + "\n```"

        super().__init__(
            name=f"file:{file_path}",
            content=smart_content,
            priority=10  # 文件通常很重要
        )


class PreemptRenderer:
    """
    Prompt 渲染引擎 - 类似浏览器渲染引擎
    负责将组件按优先级智能组合成最终 prompt
    """
    def __init__(self, max_tokens: int = 4000, model: str = "gpt-4"):
        self.max_tokens = max_tokens
        self.encoding = tiktoken.encoding_for_model(model)
        self.components: List[PromptComponent] = []

    def add(self, component: PromptComponent):
        """添加组件"""
        self.components.append(component)
        return self

    def render(self) -> str:
        """
        智能渲染 - 核心算法

        策略：
        1. 按优先级排序
        2. 贪心算法：从高优先级开始添加，直到达到 token 限制
        3. 如果组件太大，智能截断
        """
        # 1. 先渲染所有组件
        for comp in self.components:
            comp.render()

        # 2. 按优先级排序（高→低）
        sorted_comps = sorted(self.components, key=lambda x: x.priority, reverse=True)

        # 3. 贪心选择
        selected = []
        total_tokens = 0

        for comp in sorted_comps:
            comp_tokens = comp.get_token_count(self.encoding)

            # 检查是否满足最小 token 要求
            if comp_tokens < comp.min_tokens:
                continue

            # 检查是否超过预算
            if total_tokens + comp_tokens <= self.max_tokens:
                selected.append(comp)
                total_tokens += comp_tokens
            else:
                # 尝试截断
                remaining = self.max_tokens - total_tokens
                if remaining > 50:  # 至少保留 50 tokens 才有意义
                    truncated = self._truncate(comp._cached_content, remaining)
                    comp._cached_content = truncated + "\n... [截断]"
                    selected.append(comp)
                    break

        # 4. 按原始顺序重新排序（保持逻辑顺序）
        selected.sort(key=lambda x: self.components.index(x))

        # 5. 组合成最终 prompt
        final_prompt = "\n\n".join([comp._cached_content for comp in selected])

        print(f"📊 渲染统计: {len(selected)}/{len(self.components)} 组件, {total_tokens}/{self.max_tokens} tokens")
        return final_prompt

    def _truncate(self, text: str, max_tokens: int) -> str:
        """智能截断文本"""
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)


# ================== 使用示例 ==================

def demo_basic():
    """基础示例：展示基本用法"""
    print("=" * 60)
    print("示例 1: 基础用法")
    print("=" * 60)

    renderer = PreemptRenderer(max_tokens=500)

    # 添加系统提示（最高优先级）
    renderer.add(PromptComponent(
        name="system",
        content="你是一个 Python 编程助手。",
        priority=100
    ))

    # 添加用户问题（次高优先级）
    renderer.add(PromptComponent(
        name="user_query",
        content="如何使用 FastAPI 创建 API？",
        priority=90
    ))

    # 添加文档（中等优先级）
    renderer.add(PromptComponent(
        name="docs",
        content="FastAPI 是一个现代、快速的 Web 框架...\n" * 50,  # 很长的文档
        priority=50
    ))

    # 添加对话历史（低优先级）
    renderer.add(PromptComponent(
        name="history",
        content="之前你问过关于 Django 的问题...",
        priority=10
    ))

    prompt = renderer.render()
    print("\n最终 Prompt:\n")
    print(prompt)
    print("\n")


def demo_file_with_cursor():
    """文件示例：展示 Cursor 风格的光标定位"""
    print("=" * 60)
    print("示例 2: Cursor 风格 - 光标周围内容优先")
    print("=" * 60)

    # 模拟一个 Python 文件
    code = """import numpy as np
import pandas as pd

def load_data(file_path):
    '''加载数据'''
    return pd.read_csv(file_path)

def preprocess(df):
    '''预处理数据'''
    df = df.dropna()
    df = df.reset_index(drop=True)
    return df

def train_model(X, y):
    '''训练模型'''
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.fit(X, y)
    return model

def evaluate(model, X_test, y_test):
    '''评估模型'''
    score = model.score(X_test, y_test)
    return score
"""

    renderer = PreemptRenderer(max_tokens=800)

    # 系统提示
    renderer.add(PromptComponent(
        name="system",
        content="你是代码助手。光标位置用 >>> <<< 标记。",
        priority=100
    ))

    # 文件组件 - 光标在第 10 行（preprocess 函数）
    renderer.add(FileComponent(
        file_path="train.py",
        content=code,
        cursor_line=10  # 用户光标在这一行
    ))

    # 用户问题
    renderer.add(PromptComponent(
        name="user_query",
        content="这个函数有 bug 吗？",
        priority=95
    ))

    prompt = renderer.render()
    print("\n最终 Prompt:\n")
    print(prompt)
    print("\n")


def demo_weighted_rag():
    """RAG 示例：结合你的 demo.py 中的加权检索"""
    print("=" * 60)
    print("示例 3: 结合 RAG - 动态加权文档")
    print("=" * 60)

    renderer = PreemptRenderer(max_tokens=1000)

    # 系统提示
    renderer.add(PromptComponent(
        name="system",
        content="你是游戏设置者，帮助用户分解任务。",
        priority=100
    ))

    # 模拟 RAG 检索结果
    # 高相似度文档（高优先级）
    renderer.add(PromptComponent(
        name="rag_doc_1",
        content="[PSI 文档] 任务分解的核心是将大目标拆分成小步骤...",
        priority=80  # 加权相似度高
    ))

    # 中等相似度文档
    renderer.add(PromptComponent(
        name="rag_doc_2",
        content="[Context1] 用户可能因为目标不清晰而拖延...",
        priority=60
    ))

    # 低相似度文档（可能被丢弃）
    renderer.add(PromptComponent(
        name="rag_doc_3",
        content="[Context1] 游戏设计的基本原理包括..." + "很多内容..." * 100,
        priority=30
    ))

    # 用户问题
    renderer.add(PromptComponent(
        name="user_query",
        content="我想学习 Python，但总是拖延，怎么办？",
        priority=90
    ))

    prompt = renderer.render()
    print("\n最终 Prompt:\n")
    print(prompt)
    print("\n")


def demo_integration_with_rag():
    """展示如何集成到你的 RAG 系统中"""
    print("=" * 60)
    print("示例 4: 集成方案 - 替换 demo.py 中的 prompt 构建")
    print("=" * 60)

    print("""
建议的集成方式（修改 demo.py）：

# 原来的方式（固定拼接）：
# messages.append({
#     "role": "user",
#     "content": f"[参考资料]\\n{context}\\n\\n[用户问题]\\n{user_input}"
# })

# 新方式（动态 Preempt）：
from preempt_demo import PreemptRenderer, PromptComponent

def build_smart_prompt(user_input, rag_results, max_tokens=4000):
    renderer = PreemptRenderer(max_tokens=max_tokens)

    # 1. 系统提示（最高优先级）
    renderer.add(PromptComponent(
        name="system",
        content=developer_prompt,
        priority=100
    ))

    # 2. 用户问题（次高优先级）
    renderer.add(PromptComponent(
        name="user_query",
        content=user_input,
        priority=90
    ))

    # 3. RAG 文档（按加权相似度设置优先级）
    for i, (chunk, weighted_sim) in enumerate(rag_results):
        renderer.add(PromptComponent(
            name=f"rag_doc_{i}",
            content=f"[相似度 {weighted_sim:.3f}]\\n{chunk}",
            priority=int(weighted_sim * 50)  # 相似度越高，优先级越高
        ))

    # 4. 渲染最终 prompt
    return renderer.render()

# 使用：
prompt = build_smart_prompt(user_input, rag_results)
messages.append({"role": "user", "content": prompt})
    """)


if __name__ == "__main__":
    # 运行所有示例
    demo_basic()
    input("按回车继续下一个示例...")

    demo_file_with_cursor()
    input("按回车继续下一个示例...")

    demo_weighted_rag()
    input("按回车查看集成方案...")

    demo_integration_with_rag()

    print("\n✅ 全部示例完成！")
    print("\n核心优势：")
    print("1. 声明式：像 React 一样，只需声明「想要什么」")
    print("2. 智能截断：自动处理 token 限制，不会超出 context window")
    print("3. 优先级驱动：重要内容优先保留，不重要的自动丢弃")
    print("4. 调试友好：可以单独测试每个组件，数据与渲染分离")
