"""
Preempt - Cursor 风格的动态 Prompt 构建系统（简化版）
不依赖外部库，使用字符数近似 token 数

核心思路：
1. 组件化：每个内容块是一个组件（文件、对话历史、文档等）
2. 优先级：类似 CSS z-index，定义什么内容更重要
3. 动态渲染：根据限制，自动决定保留什么内容
"""

from typing import List, Callable
from dataclasses import dataclass, field


@dataclass
class PromptComponent:
    """
    类似 React 组件的 Prompt 片段
    """
    name: str                          # 组件名称
    content: str | Callable[[], str]   # 内容（可以是函数，延迟计算）
    priority: int = 1                  # 优先级（越高越重要）
    min_chars: int = 0                 # 最小字符数（低于这个数就不显示）
    max_chars: int | None = None       # 最大字符数（超过会截断）
    _cached_content: str = field(default="", init=False, repr=False)

    def render(self) -> str:
        """渲染内容"""
        if callable(self.content):
            self._cached_content = self.content()
        else:
            self._cached_content = self.content
        return self._cached_content

    def get_length(self) -> int:
        """计算字符数（简化的 token 估算）"""
        if not self._cached_content:
            self.render()
        # 粗略估算：中文按 1 token/字，英文按 4 字符/token
        return len(self._cached_content)


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
                result_lines.append(f"{i:4d} | {line}")

            # 光标行高亮
            if 0 < self.cursor_line <= len(lines):
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
    def __init__(self, max_chars: int = 8000):
        self.max_chars = max_chars
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
        2. 贪心算法：从高优先级开始添加，直到达到限制
        3. 如果组件太大，智能截断
        """
        # 1. 先渲染所有组件
        for comp in self.components:
            comp.render()

        # 2. 按优先级排序（高→低）
        sorted_comps = sorted(self.components, key=lambda x: x.priority, reverse=True)

        # 3. 贪心选择
        selected = []
        total_chars = 0

        for comp in sorted_comps:
            comp_chars = comp.get_length()

            # 检查是否满足最小字符要求
            if comp_chars < comp.min_chars:
                continue

            # 检查是否超过预算
            if total_chars + comp_chars <= self.max_chars:
                selected.append(comp)
                total_chars += comp_chars
            else:
                # 尝试截断
                remaining = self.max_chars - total_chars
                if remaining > 100:  # 至少保留 100 字符才有意义
                    comp._cached_content = comp._cached_content[:remaining] + "\n... [截断]"
                    selected.append(comp)
                    total_chars += len(comp._cached_content)
                    break

        # 4. 按原始顺序重新排序（保持逻辑顺序）
        selected.sort(key=lambda x: self.components.index(x))

        # 5. 组合成最终 prompt
        final_prompt = "\n\n".join([comp._cached_content for comp in selected])

        print(f"\n📊 渲染统计:")
        print(f"   - 组件: {len(selected)}/{len(self.components)} 个被保留")
        print(f"   - 长度: {total_chars}/{self.max_chars} 字符")
        print(f"   - 保留的组件: {[c.name for c in selected]}")
        return final_prompt


# ================== 使用示例 ==================

def demo_basic():
    """基础示例：展示基本用法"""
    print("\n" + "=" * 70)
    print("示例 1: 基础用法 - 优先级决定内容取舍")
    print("=" * 70)

    renderer = PreemptRenderer(max_chars=500)

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
        content="FastAPI 是一个现代、快速的 Web 框架，用于构建 API。它基于 Python 3.6+ 的类型提示。\n" * 10,  # 很长的文档
        priority=50
    ))

    # 添加对话历史（低优先级）
    renderer.add(PromptComponent(
        name="history",
        content="之前你问过关于 Django 的问题，我给你解释了 MTV 模式。\n" * 5,
        priority=10
    ))

    prompt = renderer.render()
    print("\n📝 最终 Prompt:\n")
    print(prompt)
    print("\n💡 观察：低优先级的 'history' 被自动丢弃了！")


def demo_file_with_cursor():
    """文件示例：展示 Cursor 风格的光标定位"""
    print("\n" + "=" * 70)
    print("示例 2: Cursor 风格 - 光标周围内容优先（核心创新）")
    print("=" * 70)

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

    renderer = PreemptRenderer(max_chars=1500)

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
    print("\n📝 最终 Prompt:\n")
    print(prompt)
    print("\n💡 观察：光标所在行（第 10 行）被 >>> <<< 高亮标记了！")


def demo_weighted_rag():
    """RAG 示例：结合你的 demo.py 中的加权检索"""
    print("\n" + "=" * 70)
    print("示例 3: 结合 RAG - 动态加权文档（解决你的实际问题）")
    print("=" * 70)

    renderer = PreemptRenderer(max_chars=1200)

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
        content="[PSI 文档, 相似度 0.92]\n任务分解的核心是将大目标拆分成小步骤，每个步骤都要具体可执行。",
        priority=92  # 用相似度作为优先级
    ))

    # 中等相似度文档
    renderer.add(PromptComponent(
        name="rag_doc_2",
        content="[Context1, 相似度 0.75]\n用户可能因为目标不清晰而拖延，需要通过提问帮助他们澄清目标。",
        priority=75
    ))

    # 低相似度文档（可能被丢弃）
    renderer.add(PromptComponent(
        name="rag_doc_3",
        content="[Context1, 相似度 0.45]\n游戏设计的基本原理包括：目标明确、反馈及时、难度适中。" + "更多游戏设计理论..." * 50,
        priority=45
    ))

    # 用户问题
    renderer.add(PromptComponent(
        name="user_query",
        content="我想学习 Python，但总是拖延，怎么办？",
        priority=90
    ))

    prompt = renderer.render()
    print("\n📝 最终 Prompt:\n")
    print(prompt)
    print("\n💡 观察：低相似度的 'rag_doc_3' 被自动丢弃了！")


def demo_integration():
    """展示如何集成到你的 RAG 系统中"""
    print("\n" + "=" * 70)
    print("示例 4: 集成方案 - 如何改造你的 demo.py")
    print("=" * 70)

    print("""
🔧 集成步骤：

1️⃣  在 demo.py 顶部导入：
    from preempt_simple import PreemptRenderer, PromptComponent

2️⃣  修改 run_task_agent 函数中的 prompt 构建部分：

    # ❌ 原来的方式（固定拼接，可能超出 context）：
    messages.append({
        "role": "user",
        "content": f"[参考资料]\\n{context}\\n\\n[用户问题]\\n{user_input}"
    })

    # ✅ 新方式（动态 Preempt，智能管理 token）：
    renderer = PreemptRenderer(max_chars=3000)  # GPT-4 约 4000 tokens

    # 添加系统提示
    renderer.add(PromptComponent(
        name="system",
        content=developer_prompt,
        priority=100
    ))

    # 添加 RAG 检索结果（按相似度设置优先级）
    for i, (chunk, weighted_sim) in enumerate(top_results):
        renderer.add(PromptComponent(
            name=f"rag_{i}",
            content=f"[相似度 {weighted_sim:.3f}]\\n{chunk}",
            priority=int(weighted_sim * 100)  # 相似度 → 优先级
        ))

    # 添加用户问题（次高优先级）
    renderer.add(PromptComponent(
        name="user_query",
        content=user_input,
        priority=95
    ))

    # 渲染最终 prompt
    final_prompt = renderer.render()
    messages.append({"role": "user", "content": final_prompt})

3️⃣  优势：
    ✅ 自动处理 token 限制，不会超出 context window
    ✅ 高相似度文档优先保留，低相似度自动丢弃
    ✅ 数据与渲染分离，方便调试和测试
    ✅ 可以用历史数据测试不同渲染策略（像 Cursor 的 eval）

4️⃣  进阶优化：
    - 可以给不同来源的文档设置基础优先级
      例如：PSI 文档基础优先级 80，Context1 基础优先级 60
      然后再乘以相似度

    - 可以根据对话轮次动态调整优先级
      例如：越早的对话历史，优先级越低

    - 可以添加 min_chars 参数，过滤太短的文档片段
    """)


if __name__ == "__main__":
    # 运行所有示例
    demo_basic()

    demo_file_with_cursor()

    demo_weighted_rag()

    demo_integration()

    print("\n" + "=" * 70)
    print("✅ 全部示例完成！")
    print("=" * 70)
    print("""
🎯 核心优势（Cursor 的创新点）：

1. 📦 声明式：像 React 一样，只需声明「想要什么」，不用管「怎么截断」
2. 🧠 智能截断：自动处理 token 限制，不会超出 context window
3. ⚖️  优先级驱动：重要内容优先保留，不重要的自动丢弃
4. 🔍 调试友好：数据与渲染分离，可以用历史数据测试不同策略
5. 🎯 性能优化：避免在 prompt 中塞入无用信息，提高模型响应质量

💡 这就是为什么 Cursor 比其他 AI 编程工具更智能的原因！
    """)
