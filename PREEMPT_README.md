# Preempt - Cursor 风格的动态 Prompt 系统

## 📖 背景

这个项目实现了 Cursor 团队在采访中提到的核心技术：**Preempt** - 一个受 React/JSX 启发的动态 prompt 构建系统。

### Cursor 团队的原话：

> "我们有一个内部系统叫 Preempt...它有点像设计网站。在网站设计中你用 React 和 JSX，以声明式的方式说'我想要这个，这个优先级更高'。然后有一个渲染引擎（像 Chrome），在我们的案例中是 preempt 渲染器，它会把所有东西放到页面上。"

---

## 🎯 核心思路

### 传统方式的问题

```python
# ❌ 传统固定拼接
prompt = f"""
系统提示：{system_prompt}
文档1：{doc1}
文档2：{doc2}
...
文档100：{doc100}
用户问题：{user_query}
"""
```

**问题：**
- 可能超出 context window
- 无法区分重要/不重要内容
- 调试困难，难以优化
- 大量无关信息降低模型表现

### Cursor/Preempt 方式

```python
# ✅ 动态优先级驱动
renderer = PreemptRenderer(max_chars=4000)

renderer.add(PromptComponent(
    name="system",
    content=system_prompt,
    priority=100  # 最高优先级
))

for doc, similarity in docs:
    renderer.add(PromptComponent(
        name=f"doc_{i}",
        content=doc,
        priority=int(similarity * 100)  # 相似度 → 优先级
    ))

renderer.add(PromptComponent(
    name="user_query",
    content=user_query,
    priority=95
))

# 自动智能截断
final_prompt = renderer.render()
```

---

## 🚀 使用方法

### 1. 基础示例

```bash
python preempt_simple.py
```

这会运行 4 个示例：
1. **基础用法**：展示优先级如何决定内容取舍
2. **Cursor 光标定位**：展示光标周围内容优先的核心创新
3. **RAG 加权**：展示如何结合检索相似度
4. **集成方案**：展示如何改造现有代码

### 2. 运行改进版 Demo

```bash
streamlit run demo_with_preempt.py
```

对比原版：
```bash
streamlit run demo.py  # 原版
```

---

## 📊 架构对比

### 组件化设计

| 特性 | 传统方式 | Preempt 方式 |
|------|---------|-------------|
| **结构** | 字符串拼接 | 组件化（类 React） |
| **优先级** | 无 | 每个组件独立优先级 |
| **截断策略** | 手动 or 全部塞入 | 自动智能截断 |
| **调试** | 困难 | 数据与渲染分离 |
| **优化** | 需重写 prompt | 只需调整优先级 |

### 代码示例对比

#### 原来的 `demo.py` (demo.py:104-118)

```python
if use_rag:
    # 固定拼接，可能超出 context
    context = get_weighted_context(...)
    messages.append({
        "role": "user",
        "content": f"[参考资料]\n{context}\n\n[用户问题]\n{user_input}"
    })
```

#### 改进的 `demo_with_preempt.py`

```python
if use_rag:
    top_results = get_weighted_context(...)

    # 动态构建
    renderer = PreemptRenderer(max_chars=6000)

    # 添加组件
    renderer.add(PromptComponent(
        name="system",
        content=developer_prompt,
        priority=100
    ))

    # RAG 文档按相似度设置优先级
    for i, (chunk, weighted_sim) in enumerate(top_results):
        priority = int(80 + weighted_sim * 20)
        renderer.add(PromptComponent(
            name=f"rag_doc_{i}",
            content=f"[相似度 {weighted_sim:.3f}]\n{chunk}",
            priority=priority
        ))

    renderer.add(PromptComponent(
        name="user_query",
        content=user_input,
        priority=95
    ))

    # 自动渲染
    final_prompt = renderer.render()
    messages.append({"role": "user", "content": final_prompt})
```

---

## 🧩 核心组件说明

### 1. PromptComponent

每个内容块是一个组件：

```python
@dataclass
class PromptComponent:
    name: str              # 组件名称（用于调试）
    content: str | Callable  # 内容（可以是函数，延迟计算）
    priority: int = 1      # 优先级（越高越重要）
    min_chars: int = 0     # 最小字符数
    max_chars: int | None  # 最大字符数
```

### 2. FileComponent

Cursor 的核心创新 - 光标周围内容优先：

```python
file = FileComponent(
    file_path="train.py",
    content=code,
    cursor_line=10  # 光标在第 10 行
)
```

**效果：**
- 光标所在行优先级最高
- 距离光标越远，优先级越低
- 自动高亮光标位置

### 3. PreemptRenderer

渲染引擎 - 类似浏览器：

```python
renderer = PreemptRenderer(max_chars=4000)
renderer.add(component1)
renderer.add(component2)
final_prompt = renderer.render()  # 自动截断
```

**渲染策略：**
1. 按优先级排序
2. 贪心算法：从高优先级开始添加
3. 达到限制时智能截断
4. 输出渲染统计（用于调试）

---

## 🎓 核心优势

### 1. 声明式编程

像 React 一样，只需声明「想要什么」：

```python
# 不需要关心如何截断，只需声明优先级
renderer.add(PromptComponent(
    name="important_doc",
    content=long_document,
    priority=80
))
```

### 2. 智能截断

```
📊 渲染统计:
   - 组件: 15/30 个被保留
   - 长度: 3950/4000 字符
   - 保留的组件: ['system', 'user_query', 'rag_doc_1', ...]
```

自动决定：
- 哪些内容保留
- 哪些内容丢弃
- 如何截断过长内容

### 3. 优先级驱动

```python
# 系统提示 - 最高优先级
priority=100

# 用户问题 - 次高优先级
priority=95

# RAG 文档 - 按相似度
priority=int(similarity * 100)

# 对话历史 - 低优先级
priority=10
```

### 4. 调试友好

数据与渲染分离：

```python
# 可以用历史数据测试不同渲染策略
old_data = load_eval_data()
for scenario in old_data:
    prompt = renderer.render()
    # 评估效果
```

这就是 Cursor 如何用 eval 来优化 prompt 的！

---

## 💡 实际应用场景

### 1. RAG 系统（你的场景）

**问题：** 检索出 30 个文档片段，但只有前 10 个真正相关

**解决：**
```python
for i, (chunk, similarity) in enumerate(results):
    priority = int(similarity * 100)  # 相似度高 → 优先级高
    renderer.add(PromptComponent(
        name=f"doc_{i}",
        content=chunk,
        priority=priority
    ))
```

### 2. 代码编辑（Cursor 的场景）

**问题：** 文件很大（1000+ 行），但只关心光标附近

**解决：**
```python
FileComponent(
    file_path="large_file.py",
    content=file_content,
    cursor_line=500  # 只有第 500 行附近会被优先保留
)
```

### 3. 多轮对话

**问题：** 对话历史越来越长，早期对话不再相关

**解决：**
```python
for i, msg in enumerate(history):
    # 越早的对话，优先级越低
    priority = max(10, 50 - i * 2)
    renderer.add(PromptComponent(
        name=f"history_{i}",
        content=msg,
        priority=priority
    ))
```

---

## 🔧 进阶优化

### 1. 基础优先级 + 动态调整

```python
# PSI 文档基础优先级更高
base_priority = 80 if source == "PSI" else 60
final_priority = base_priority + int(similarity * 20)
```

### 2. 最小字符数过滤

```python
renderer.add(PromptComponent(
    name="doc",
    content=chunk,
    priority=70,
    min_chars=100  # 太短的片段直接丢弃
))
```

### 3. 延迟计算（性能优化）

```python
# 内容可以是函数，只有被选中时才计算
renderer.add(PromptComponent(
    name="expensive_doc",
    content=lambda: expensive_computation(),  # 延迟计算
    priority=50
))
```

---

## 📈 性能对比

| 指标 | 传统方式 | Preempt 方式 |
|------|---------|-------------|
| **Token 使用** | 常常超出限制 | 自动控制在限制内 |
| **响应质量** | 噪音多，质量不稳定 | 只保留高优先级信息 |
| **调试时间** | 需要反复调整字符串 | 只需调整优先级数字 |
| **可维护性** | 难以理解和修改 | 组件化，易于维护 |

---

## 🎯 为什么 Cursor 更智能？

这就是答案：

1. **智能 context 管理**：不会把无关信息塞给模型
2. **优先级驱动**：重要内容优先，提高回答质量
3. **可持续优化**：数据与渲染分离，可以用历史数据测试优化
4. **声明式设计**：开发者只需关心「想要什么」，不用关心「怎么实现」

---

## 📚 文件说明

```
Garden-demo/
├── preempt_simple.py         # 核心实现 + 4 个示例
├── demo.py                    # 原版（固定拼接）
├── demo_with_preempt.py      # 改进版（动态 Preempt）
├── PREEMPT_README.md         # 本文档
└── embedding.py              # RAG embedding 逻辑
```

---

## 🚀 下一步

### 立即体验

```bash
# 1. 运行示例，理解概念
python preempt_simple.py

# 2. 对比原版和改进版
streamlit run demo.py              # 原版
streamlit run demo_with_preempt.py # 改进版

# 3. 观察控制台输出的"渲染统计"
```

### 集成到你的项目

只需 3 步：

1. 导入 Preempt
```python
from preempt_simple import PreemptRenderer, PromptComponent
```

2. 构建组件
```python
renderer = PreemptRenderer(max_chars=4000)
renderer.add(PromptComponent(...))
```

3. 渲染使用
```python
prompt = renderer.render()
```

---

## 💬 总结

Cursor 的 Preempt 系统展示了一个重要理念：

> **不是给模型更多信息，而是给模型更好的信息**

通过优先级驱动的动态 prompt 构建：
- ✅ 自动管理 context window
- ✅ 提高模型响应质量
- ✅ 降低成本（更少 token）
- ✅ 更好的开发体验

这就是现代 AI 应用的核心竞争力！
