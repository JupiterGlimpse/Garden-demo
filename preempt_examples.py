"""
Preempt 实战案例集合
展示在不同场景下如何使用动态 prompt 系统
"""

from preempt_simple import PreemptRenderer, PromptComponent, FileComponent


# ============================================================
# 案例 1: 多数据源 RAG（你的实际场景）
# ============================================================

def example_1_multi_source_rag():
    """
    场景：有多个知识库，每个库的重要性不同

    例如：
    - 官方文档（最重要）
    - 博客文章（中等重要）
    - 社区讨论（较不重要）
    """
    print("\n" + "="*70)
    print("案例 1: 多数据源 RAG - 给不同来源设置基础优先级")
    print("="*70)

    # 模拟检索结果
    results = {
        "官方文档": [
            ("FastAPI 使用 Pydantic 进行数据验证...", 0.85),
            ("FastAPI 支持异步请求处理...", 0.78)
        ],
        "博客文章": [
            ("我是如何用 FastAPI 构建 API 的...", 0.82),
            ("FastAPI vs Flask 性能对比...", 0.65)
        ],
        "社区讨论": [
            ("有人遇到 FastAPI 的 bug 吗...", 0.70),
            ("推荐学习 FastAPI 的资源...", 0.60)
        ]
    }

    # 设置基础优先级
    source_base_priority = {
        "官方文档": 80,    # 最高
        "博客文章": 60,    # 中等
        "社区讨论": 40     # 最低
    }

    renderer = PreemptRenderer(max_chars=800)

    # 系统提示
    renderer.add(PromptComponent(
        name="system",
        content="你是 Python 编程助手。",
        priority=100
    ))

    # 添加检索结果
    for source, docs in results.items():
        for i, (doc, similarity) in enumerate(docs):
            # 基础优先级 + 相似度加成
            base = source_base_priority[source]
            priority = base + int(similarity * 20)

            renderer.add(PromptComponent(
                name=f"{source}_{i}",
                content=f"[来源: {source}, 相似度: {similarity:.2f}]\n{doc}",
                priority=priority
            ))

    # 用户问题
    renderer.add(PromptComponent(
        name="user_query",
        content="FastAPI 如何进行数据验证？",
        priority=95
    ))

    prompt = renderer.render()
    print("\n📝 最终 Prompt:")
    print(prompt)
    print("\n💡 观察：官方文档被优先保留，社区讨论可能被丢弃")


# ============================================================
# 案例 2: 对话历史管理
# ============================================================

def example_2_conversation_history():
    """
    场景：多轮对话，早期对话逐渐变得不重要

    策略：越新的对话优先级越高
    """
    print("\n" + "="*70)
    print("案例 2: 对话历史管理 - 越新的对话优先级越高")
    print("="*70)

    # 模拟对话历史（从旧到新）
    conversation = [
        {"role": "user", "content": "你好", "turn": 1},
        {"role": "assistant", "content": "你好！有什么可以帮你的？", "turn": 1},
        {"role": "user", "content": "Python 是什么？", "turn": 2},
        {"role": "assistant", "content": "Python 是一种高级编程语言...", "turn": 2},
        {"role": "user", "content": "如何安装 FastAPI？", "turn": 3},
        {"role": "assistant", "content": "使用 pip install fastapi...", "turn": 3},
        {"role": "user", "content": "FastAPI 如何定义路由？", "turn": 4},
    ]

    renderer = PreemptRenderer(max_chars=600)

    # 系统提示（最高优先级）
    renderer.add(PromptComponent(
        name="system",
        content="你是 Python 编程助手。",
        priority=100
    ))

    # 对话历史（越新优先级越高）
    max_turn = max(msg["turn"] for msg in conversation)
    for i, msg in enumerate(conversation):
        # 计算优先级：最新的对话优先级最高
        age = max_turn - msg["turn"]  # 距离当前有多远
        priority = 60 - (age * 10)    # 每轮降低 10

        renderer.add(PromptComponent(
            name=f"history_{i}",
            content=f"{msg['role']}: {msg['content']}",
            priority=max(20, priority),  # 最低不低于 20
            min_chars=5  # 太短的过滤掉
        ))

    prompt = renderer.render()
    print("\n📝 最终 Prompt:")
    print(prompt)
    print("\n💡 观察：早期的'你好'对话被丢弃，近期的 FastAPI 讨论被保留")


# ============================================================
# 案例 3: 代码审查 - 多文件场景
# ============================================================

def example_3_code_review():
    """
    场景：代码审查，有主文件和相关文件

    策略：
    - 主文件（用户正在看的）优先级最高
    - 相关文件按引用关系降低优先级
    """
    print("\n" + "="*70)
    print("案例 3: 代码审查 - 主文件优先，相关文件次之")
    print("="*70)

    # 主文件
    main_file = """from utils import validate_data
from models import User

def create_user(name: str, email: str):
    if not validate_data(email):
        raise ValueError("Invalid email")
    return User(name=name, email=email)
"""

    # 相关文件
    utils_file = """import re

def validate_data(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'
    return re.match(pattern, email) is not None
"""

    models_file = """class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
"""

    renderer = PreemptRenderer(max_chars=1000)

    # 系统提示
    renderer.add(PromptComponent(
        name="system",
        content="你是代码审查助手。检查代码中的潜在问题。",
        priority=100
    ))

    # 主文件（最高优先级）
    renderer.add(FileComponent(
        file_path="main.py",
        content=main_file,
        cursor_line=4  # 用户光标在第 4 行
    ))
    # 注意：FileComponent 默认优先级是 10，我们手动提升
    renderer.components[-1].priority = 90

    # 相关文件（中等优先级）
    renderer.add(PromptComponent(
        name="file:utils.py",
        content=f"File: utils.py\n```python\n{utils_file}\n```",
        priority=60
    ))

    renderer.add(PromptComponent(
        name="file:models.py",
        content=f"File: models.py\n```python\n{models_file}\n```",
        priority=50
    ))

    # 用户问题
    renderer.add(PromptComponent(
        name="user_query",
        content="这段代码有什么问题？",
        priority=95
    ))

    prompt = renderer.render()
    print("\n📝 最终 Prompt:")
    print(prompt)
    print("\n💡 观察：主文件被完整保留，相关文件根据空间选择性保留")


# ============================================================
# 案例 4: 文档问答 - 长文档智能截断
# ============================================================

def example_4_long_document():
    """
    场景：查询一个超长文档

    策略：
    - 文档的不同部分设置不同优先级
    - 标题/摘要优先级最高
    - 正文根据相关性设置优先级
    """
    print("\n" + "="*70)
    print("案例 4: 长文档问答 - 标题和相关段落优先")
    print("="*70)

    # 模拟一个长文档的不同部分
    doc_parts = {
        "标题": "FastAPI 完整教程",
        "摘要": "本文介绍 FastAPI 的核心概念和最佳实践...",
        "章节1": "FastAPI 简介\n" + "FastAPI 是一个现代 Web 框架..." * 20,
        "章节2": "路由和请求处理\n" + "使用 @app.get() 装饰器定义路由..." * 20,
        "章节3": "数据验证\n" + "FastAPI 使用 Pydantic 进行自动数据验证..." * 20,
        "章节4": "数据库集成\n" + "可以使用 SQLAlchemy 或 Tortoise ORM..." * 20,
    }

    # 用户问题
    user_query = "FastAPI 如何进行数据验证？"

    renderer = PreemptRenderer(max_chars=800)

    # 系统提示
    renderer.add(PromptComponent(
        name="system",
        content="你是技术文档助手。",
        priority=100
    ))

    # 文档各部分（不同优先级）
    renderer.add(PromptComponent(
        name="doc_title",
        content=f"# {doc_parts['标题']}",
        priority=85  # 标题很重要
    ))

    renderer.add(PromptComponent(
        name="doc_summary",
        content=doc_parts['摘要'],
        priority=80  # 摘要很重要
    ))

    # 章节按相关性设置优先级
    # 假设我们通过关键词匹配判断相关性
    chapter_relevance = {
        "章节1": 40,  # 简介，不太相关
        "章节2": 50,  # 路由，不太相关
        "章节3": 90,  # 数据验证，高度相关！
        "章节4": 45,  # 数据库，不太相关
    }

    for chapter, content in list(doc_parts.items())[2:]:  # 跳过标题和摘要
        renderer.add(PromptComponent(
            name=f"doc_{chapter}",
            content=content,
            priority=chapter_relevance[chapter]
        ))

    # 用户问题
    renderer.add(PromptComponent(
        name="user_query",
        content=user_query,
        priority=95
    ))

    prompt = renderer.render()
    print("\n📝 最终 Prompt:")
    print(prompt[:500] + "...")  # 只显示前 500 字符
    print("\n💡 观察：标题、摘要和'数据验证'章节被保留，其他章节被丢弃")


# ============================================================
# 案例 5: 错误调试 - 堆栈跟踪优先
# ============================================================

def example_5_error_debugging():
    """
    场景：调试错误，有大量上下文信息

    策略：
    - 错误信息优先级最高
    - 相关代码次之
    - 日志信息最低
    """
    print("\n" + "="*70)
    print("案例 5: 错误调试 - 错误信息和相关代码优先")
    print("="*70)

    # 模拟调试信息
    error_trace = """Traceback (most recent call last):
  File "main.py", line 15, in create_user
    validate_email(email)
  File "utils.py", line 8, in validate_email
    raise ValueError("Invalid email format")
ValueError: Invalid email format"""

    related_code = """def create_user(name, email):
    validate_email(email)  # Line 15
    return User(name, email)"""

    logs = """[2024-01-01 10:00:00] INFO: Server started
[2024-01-01 10:00:05] INFO: Request received
[2024-01-01 10:00:06] DEBUG: Processing user data
[2024-01-01 10:00:07] ERROR: Validation failed
""" * 10  # 很长的日志

    renderer = PreemptRenderer(max_chars=600)

    # 系统提示
    renderer.add(PromptComponent(
        name="system",
        content="你是调试助手。帮助定位和解决错误。",
        priority=100
    ))

    # 错误堆栈（最高优先级）
    renderer.add(PromptComponent(
        name="error",
        content=f"错误信息:\n```\n{error_trace}\n```",
        priority=95
    ))

    # 相关代码（高优先级）
    renderer.add(PromptComponent(
        name="code",
        content=f"相关代码:\n```python\n{related_code}\n```",
        priority=85
    ))

    # 日志（低优先级）
    renderer.add(PromptComponent(
        name="logs",
        content=f"系统日志:\n```\n{logs}\n```",
        priority=30
    ))

    # 用户问题
    renderer.add(PromptComponent(
        name="user_query",
        content="为什么会出现这个错误？如何修复？",
        priority=90
    ))

    prompt = renderer.render()
    print("\n📝 最终 Prompt:")
    print(prompt)
    print("\n💡 观察：错误信息和相关代码被保留，大量日志被丢弃")


# ============================================================
# 案例 6: 延迟计算 - 性能优化
# ============================================================

def example_6_lazy_evaluation():
    """
    场景：某些内容计算成本很高（如数据库查询、文件读取）

    策略：使用函数作为 content，只有被选中才计算
    """
    print("\n" + "="*70)
    print("案例 6: 延迟计算 - 只计算需要的内容（性能优化）")
    print("="*70)

    # 模拟昂贵的计算
    def expensive_computation_1():
        print("   ⚙️  执行昂贵计算 1...")
        return "复杂分析结果 1：" + "数据..." * 100

    def expensive_computation_2():
        print("   ⚙️  执行昂贵计算 2...")
        return "复杂分析结果 2：" + "数据..." * 100

    def cheap_data():
        print("   ✅ 执行简单查询...")
        return "基础信息：用户名、邮箱等"

    renderer = PreemptRenderer(max_chars=500)

    # 系统提示
    renderer.add(PromptComponent(
        name="system",
        content="你是数据分析助手。",
        priority=100
    ))

    # 基础数据（高优先级）
    renderer.add(PromptComponent(
        name="basic_data",
        content=cheap_data,  # 函数！
        priority=80
    ))

    # 复杂分析 1（中等优先级）
    renderer.add(PromptComponent(
        name="analysis_1",
        content=expensive_computation_1,  # 函数！
        priority=50
    ))

    # 复杂分析 2（低优先级）
    renderer.add(PromptComponent(
        name="analysis_2",
        content=expensive_computation_2,  # 函数！
        priority=30
    ))

    # 用户问题
    renderer.add(PromptComponent(
        name="user_query",
        content="显示用户基本信息",
        priority=90
    ))

    print("\n开始渲染...")
    prompt = renderer.render()
    print("\n📝 最终 Prompt:")
    print(prompt[:300] + "...")
    print("\n💡 观察：只执行了被选中的组件的计算，低优先级的昂贵计算被跳过")


# ============================================================
# 运行所有案例
# ============================================================

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                   Preempt 实战案例集合                              ║
║                6 个真实场景的使用示例                               ║
╚════════════════════════════════════════════════════════════════════╝
    """)

    # 案例 1
    example_1_multi_source_rag()
    input("\n按回车继续下一个案例...")

    # 案例 2
    example_2_conversation_history()
    input("\n按回车继续下一个案例...")

    # 案例 3
    example_3_code_review()
    input("\n按回车继续下一个案例...")

    # 案例 4
    example_4_long_document()
    input("\n按回车继续下一个案例...")

    # 案例 5
    example_5_error_debugging()
    input("\n按回车继续下一个案例...")

    # 案例 6
    example_6_lazy_evaluation()

    print("\n" + "="*70)
    print("✅ 所有案例演示完成！")
    print("="*70)
    print("""
📚 6 个实战案例总结：

1️⃣  多数据源 RAG        → 不同来源设置不同基础优先级
2️⃣  对话历史管理        → 越新的对话优先级越高
3️⃣  代码审查            → 主文件优先，相关文件次之
4️⃣  长文档问答          → 标题/摘要 + 相关段落优先
5️⃣  错误调试            → 错误信息 > 代码 > 日志
6️⃣  延迟计算            → 只计算需要的内容（性能优化）

💡 核心思路：
   - 明确什么最重要（优先级）
   - 让 Preempt 自动处理剩下的（截断、选择）
   - 声明式，易维护，易调试

🎯 下一步：
   - 用这些模式改造你自己的项目
   - 根据实际情况调整优先级数值
   - 观察"渲染统计"来优化策略
    """)
