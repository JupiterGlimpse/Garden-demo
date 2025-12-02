# Preempt 快速使用指南

## 🚀 3 种运行方式

### 1️⃣ 基础示例（最简单，先看这个）

```bash
python preempt_simple.py
```

**展示内容：**
- 示例 1: 基础用法 - 优先级如何工作
- 示例 2: Cursor 光标定位 - 核心创新
- 示例 3: RAG 加权 - 结合检索
- 示例 4: 集成方案 - 如何改造代码

**关键看什么：**
```
📊 渲染统计:
   - 组件: 3/4 个被保留  ← 看这里！哪些被保留
   - 长度: 509/500 字符
   - 保留的组件: ['system', 'user_query', 'docs']
```

---

### 2️⃣ 实战案例（6 个真实场景）

```bash
python preempt_examples.py
```

**展示内容：**
1. **多数据源 RAG** - 官方文档 > 博客 > 社区讨论
2. **对话历史管理** - 越新的对话越重要
3. **代码审查** - 主文件 > 相关文件
4. **长文档问答** - 标题/摘要 + 相关段落优先
5. **错误调试** - 错误信息 > 代码 > 日志
6. **延迟计算** - 性能优化

**适合场景：**
- 想看具体怎么用
- 想找类似自己项目的案例
- 想学习最佳实践

---

### 3️⃣ 改进版 Demo（实际应用）

```bash
streamlit run demo_with_preempt.py
```

**功能：**
- 集成了 Preempt 的完整 RAG 应用
- 可以实时调整权重
- 在控制台查看"渲染统计"

**对比：**
```bash
streamlit run demo.py              # 原版（固定拼接）
streamlit run demo_with_preempt.py # 改进版（动态 Preempt）
```

---

## 💡 快速上手 - 只需 3 步

### 第 1 步：导入

```python
from preempt_simple import PreemptRenderer, PromptComponent
```

### 第 2 步：创建渲染器 + 添加组件

```python
renderer = PreemptRenderer(max_chars=4000)

# 添加系统提示（优先级 100）
renderer.add(PromptComponent(
    name="system",
    content="你是 AI 助手",
    priority=100
))

# 添加文档（优先级 80）
renderer.add(PromptComponent(
    name="doc1",
    content="重要文档内容...",
    priority=80
))

# 添加用户问题（优先级 95）
renderer.add(PromptComponent(
    name="query",
    content="用户的问题",
    priority=95
))
```

### 第 3 步：渲染

```python
final_prompt = renderer.render()
# 自动输出渲染统计
# 使用 final_prompt 调用 LLM
```

---

## 🎯 核心概念 - 3 个关键点

### 1. 组件化

每个内容块是一个组件：

```python
PromptComponent(
    name="组件名",        # 用于调试
    content="内容",       # 可以是字符串或函数
    priority=80,         # 优先级（0-100）
    min_chars=50         # 可选：最小字符数
)
```

### 2. 优先级

推荐优先级范围：

| 类型 | 优先级 | 说明 |
|------|-------|------|
| 系统提示 | 100 | 必须保留 |
| 用户问题 | 90-95 | 最重要 |
| 高相关文档 | 80-90 | 很重要 |
| 中等相关文档 | 60-79 | 重要 |
| 对话历史 | 40-59 | 可选 |
| 日志/调试信息 | 20-39 | 不重要 |

### 3. 自动截断

```python
renderer = PreemptRenderer(max_chars=4000)
# 自动处理：
# - 按优先级选择组件
# - 超出限制时智能截断
# - 输出渲染统计
```

---

## 📊 实际案例模板

### 场景 1: 你的 RAG 系统

```python
renderer = PreemptRenderer(max_chars=6000)

# 系统提示
renderer.add(PromptComponent(
    name="system",
    content=system_prompt,
    priority=100
))

# RAG 检索结果（按相似度）
for i, (chunk, similarity) in enumerate(rag_results):
    priority = int(80 + similarity * 20)  # 相似度转优先级
    renderer.add(PromptComponent(
        name=f"rag_{i}",
        content=chunk,
        priority=priority
    ))

# 用户问题
renderer.add(PromptComponent(
    name="query",
    content=user_input,
    priority=95
))

prompt = renderer.render()
```

### 场景 2: 多轮对话

```python
renderer = PreemptRenderer(max_chars=4000)

# 对话历史（越新越重要）
for i, msg in enumerate(history):
    age = len(history) - i  # 距离现在多远
    priority = max(30, 60 - age * 5)  # 越早优先级越低

    renderer.add(PromptComponent(
        name=f"history_{i}",
        content=f"{msg['role']}: {msg['content']}",
        priority=priority
    ))
```

### 场景 3: 多数据源

```python
# 设置基础优先级
base_priority = {
    "官方文档": 80,
    "博客": 60,
    "社区": 40
}

for source, docs in all_docs.items():
    for doc, score in docs:
        # 基础优先级 + 相似度加成
        priority = base_priority[source] + int(score * 20)
        renderer.add(PromptComponent(
            name=f"{source}_{i}",
            content=doc,
            priority=priority
        ))
```

---

## 🔍 调试技巧

### 查看渲染统计

每次调用 `renderer.render()` 会自动输出：

```
📊 渲染统计:
   - 组件: 15/30 个被保留
   - 长度: 3950/4000 字符
   - 保留的组件: ['system', 'user_query', ...]
```

**根据统计调整：**
- 保留太少？→ 提高限制或降低优先级差距
- 某些组件总是被丢弃？→ 提高优先级
- 空间浪费？→ 增加更多组件或降低限制

### 测试不同策略

```python
# 策略 1: 激进截断
renderer1 = PreemptRenderer(max_chars=2000)

# 策略 2: 保守截断
renderer2 = PreemptRenderer(max_chars=6000)

# 用同样的组件测试
for comp in components:
    renderer1.add(comp)
    renderer2.add(comp)

prompt1 = renderer1.render()
prompt2 = renderer2.render()

# 对比效果
```

---

## ⚡ 性能优化

### 1. 使用延迟计算

```python
# ❌ 立即计算（即使不用也会执行）
expensive_result = expensive_function()
renderer.add(PromptComponent(
    name="expensive",
    content=expensive_result,
    priority=30
))

# ✅ 延迟计算（只在被选中时执行）
renderer.add(PromptComponent(
    name="expensive",
    content=lambda: expensive_function(),  # 函数！
    priority=30
))
```

### 2. 设置最小字符数

```python
renderer.add(PromptComponent(
    name="short_doc",
    content=chunk,
    priority=70,
    min_chars=100  # 太短直接过滤
))
```

---

## 📚 文件说明

```
Garden-demo/
├── preempt_simple.py         ← 核心实现 + 基础示例（先看这个）
├── preempt_examples.py       ← 6 个实战案例
├── demo_with_preempt.py      ← 完整 RAG 应用
├── QUICK_START.md            ← 本文档
└── PREEMPT_README.md         ← 详细文档
```

---

## 🎓 学习路径

1. **理解概念**（5 分钟）
   ```bash
   python preempt_simple.py
   ```
   看完 4 个基础示例

2. **学习实战**（15 分钟）
   ```bash
   python preempt_examples.py
   ```
   找到类似你项目的案例

3. **动手改造**（30 分钟）
   - 参考 `demo_with_preempt.py`
   - 改造你自己的代码
   - 观察渲染统计调优

---

## 💬 常见问题

### Q1: 优先级应该设置为多少？

**A:** 没有固定答案，从这些范围开始：
- 必须保留：90-100
- 很重要：70-89
- 重要：50-69
- 可选：30-49
- 不重要：10-29

然后根据"渲染统计"调整。

### Q2: max_chars 设置为多少？

**A:** 根据模型 context window：
- GPT-3.5: 3000-4000 字符
- GPT-4: 6000-8000 字符
- Claude: 8000-12000 字符

留 20-30% 的空间给模型回复。

### Q3: 如何知道效果好不好？

**A:** 两个方法：
1. 查看"渲染统计"，确认重要内容被保留
2. 实际测试模型回答质量

可以 A/B 测试不同策略。

### Q4: 和传统方式对比？

**A:**

| 特性 | 传统方式 | Preempt |
|------|---------|---------|
| Token 管理 | ❌ 手动 | ✅ 自动 |
| 内容选择 | ❌ 全部或截断 | ✅ 智能选择 |
| 调试 | ❌ 困难 | ✅ 有统计 |
| 维护 | ❌ 字符串拼接 | ✅ 组件化 |

---

## 🎯 总结

**核心价值：**
> 不是给模型更多信息，而是给模型更好的信息

**3 个关键词：**
1. **声明式** - 只需声明优先级
2. **自动化** - 自动截断和选择
3. **可优化** - 数据与渲染分离

**立即开始：**
```bash
python preempt_simple.py  # 5 分钟理解核心
```
