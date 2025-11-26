import streamlit as st
from dotenv import load_dotenv
import os
from openai import OpenAI
import numpy as np
import faiss

# 导入 Preempt 系统
from preempt_simple import PreemptRenderer, PromptComponent

os.chdir(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==================== 缓存读取 ====================
@st.cache_resource
def load_faiss_index(index_path, chunks_path):
    index = faiss.read_index(index_path)
    chunks = np.load(chunks_path, allow_pickle=True)
    return index, chunks

@st.cache_data
def get_embedding(text, model="text-embedding-3-small"):
    return client.embeddings.create(input=text, model=model).data[0].embedding

# =====================

def search_from_faiss(user_input, index_path, chunks_path, k=15, embedding_model="text-embedding-3-small"):
    index = faiss.read_index(index_path)
    chunks = np.load(chunks_path, allow_pickle=True)

    user_input_emb = client.embeddings.create(
        input=user_input,
        model=embedding_model
    ).data[0].embedding

    k = min(k, len(chunks))
    Distances, Indexes = index.search(np.array([user_input_emb]).astype('float32'), k=k)

    results = []
    for idx, dist in zip(Indexes[0], Distances[0]):
        results.append((chunks[idx], dist))
    return results


def get_weighted_context(
    user_input,
    sources,
    k=15,
    embedding_model="text-embedding-3-small"
):
    """
    sources: list of dicts
        e.g. [
            {"index_path": "books.faiss", "chunks_path": "books.npy", "weight": 1.2},
            {"index_path": "notes.faiss", "chunks_path": "notes.npy", "weight": 1.0}
        ]
    """
    all_results = []

    # 1️⃣ 分别检索
    for src in sources:
        results = search_from_faiss(
            user_input,
            src["index_path"],
            src["chunks_path"],
            k=k,
            embedding_model=embedding_model
        )

        # 2️⃣ 加权：FAISS distance 越小表示越相似，所以要反向处理
        for chunk, dist in results:
            sim = 1 / (1 + dist)        # 距离→相似度，范围 (0,1)
            weighted_sim = sim * src["weight"]
            all_results.append((chunk, weighted_sim))

    # 3️⃣ 全部排序
    all_results.sort(key=lambda x: x[1], reverse=True)
    top_results = all_results[:k]

    return top_results


#多轮task
developer_prompt = """你是一个游戏设置者。帮助用户以第三人称观察自己当前的任务状态。用户是游戏中的角色，目前遇到一个需要完成的任务。你的目标是通过提问和引导，让用户清晰地理解任务、分解步骤、设计可执行路径，并持续调整策略，帮助用户完成目标，不再因为清晰度不够而卡住拖延。
                        你不要直接给用户答案，而是：
                        1.
                        2. 分析他们可能的思维模式、行为模式、情绪状态。
                        3. 提出引导性的提问，让用户根据自己的目标和需求自己发现问题、反思目标与资源。
                        4. 保留用户历史输入，用于下一轮调整。
                        5. 结尾语气温暖，想一个思维清晰，态度真诚的朋友。

                        """

def run_task_agent(user_input, messages, use_rag=True, temperature=0.4, psi_weight=1.0, context1_weight=1.3):
    """
    ✨ 使用 Preempt 风格的动态 prompt 构建
    """

    if use_rag:
        sources = [
            {"index_path": "PSI_books.faiss", "chunks_path": "PSI_books_chunks.npy", "weight": psi_weight},
            {"index_path": "context1.faiss", "chunks_path": "context1_chunks.npy", "weight": context1_weight}
        ]
        top_results = get_weighted_context(
            user_input=user_input,
            sources=sources,
            k=30,
            embedding_model="text-embedding-3-small"
        )

        # ✨ 核心改进：使用 Preempt 动态构建 prompt
        renderer = PreemptRenderer(max_chars=6000)  # GPT-4 约 8000 tokens

        # 1. 系统提示（最高优先级）
        renderer.add(PromptComponent(
            name="developer_prompt",
            content=developer_prompt,
            priority=100
        ))

        # 2. RAG 检索结果（按加权相似度设置优先级）
        for i, (chunk, weighted_sim) in enumerate(top_results):
            # 相似度越高，优先级越高
            # 前 10 个结果优先级更高
            base_priority = 80 if i < 10 else 60
            priority = int(base_priority + weighted_sim * 20)

            renderer.add(PromptComponent(
                name=f"rag_doc_{i}",
                content=f"[参考资料 {i+1}, 相似度 {weighted_sim:.3f}]\n{chunk}",
                priority=priority,
                min_chars=50  # 过滤太短的片段
            ))

        # 3. 用户问题（次高优先级）
        renderer.add(PromptComponent(
            name="user_query",
            content=f"[用户问题]\n{user_input}",
            priority=95
        ))

        # 4. 渲染最终 prompt
        final_prompt = renderer.render()
        messages.append({"role": "user", "content": final_prompt})
    else:
        messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=temperature
    ).choices[0].message.content

    messages.append({"role": "assistant", "content": response})
    return response, messages


# ========== Streamlit 界面 ==========
st.set_page_config(page_title="RAG Agent Demo (with Preempt)", page_icon="🚀")
st.title("🚀 RAG Agent Demo - Preempt 版")

st.info("✨ 使用 Cursor 风格的动态 Prompt 系统，自动管理 token 限制")

# 侧边栏：
with st.sidebar:
    st.header("⚙️ 设置")
    use_rag = st.checkbox("使用 RAG", value=True)

    # 动态滑条
    psi_weight = st.slider("PSI 文档权重", min_value=0.0, max_value=3.0, value=1.0, step=0.1)
    context1_weight = st.slider("Context1 文档权重", min_value=0.0, max_value=3.0, value=1.3, step=0.1)

    st.markdown("---")
    st.markdown("### 📊 Preempt 优势")
    st.markdown("""
    - ✅ 智能截断文档
    - ✅ 优先级驱动选择
    - ✅ 自动管理 token
    - ✅ 提高回答质量
    """)

    if st.button("清空对话"):
        st.session_state.messages = [{"role": "developer", "content": developer_prompt}]
        st.rerun()

# 初始化 session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "developer", "content": developer_prompt}]

#  显示历史对话
for msg in st.session_state.messages:
    if msg["role"] != "developer":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# 用户输入
if prompt := st.chat_input("请输入你的问题..."):
    # 显示用户消息
    with st.chat_message("user"):
        st.write(prompt)

    # 生成回复
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            response, st.session_state.messages = run_task_agent(
                prompt,
                st.session_state.messages,
                use_rag=use_rag,
                psi_weight=psi_weight,
                context1_weight=context1_weight
            )
        st.write(response)
