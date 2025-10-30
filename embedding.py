# import json

import pdfplumber
import os

import faiss
import numpy as np
import tiktoken

from tqdm import tqdm


from dotenv import load_dotenv

from openai import OpenAI

os.chdir(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()  # 加载 .env 文件
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



#chunk

file_path = "./docs/PSI.pdf"


import os


def generate_chunks_from_books(file_path, start_page=30, min_chars=100):
    books_chunks = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages[start_page-1:]:
            text = page.extract_text()
            if not text:
                continue
            paragraphs = text.split('\n\n')
            for para in paragraphs:
                if len(para.strip()) >= min_chars:
                    books_chunks.append(para.strip())
    print(f"✅ Total books_chunks: {len(books_chunks)}")
    return books_chunks

def generate_chunks_from_text(file_path,min_chars=10):
    """
    将纯文本文件按换行符分割为 chunk。
    与 generate_chunks(pdf) 对应，用于 txt。
    
    Args:
        file_path (str): 文本文件路径
        min_chars (int): 每个 chunk 最少字符数，用于过滤空行或碎片
    
    Returns:
        list[str]: 文本分块列表
    """
    text_chunks = [] #local chunks
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 以换行符分割文本
    paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) >= min_chars]
    
    text_chunks.extend(paragraphs)
    print(f"✅ Total chunks: {len(text_chunks)}")
    return text_chunks

def generate_chunks_from(file_path, start_page=30, min_chars=100):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return generate_chunks_from_books(file_path, start_page, min_chars)
    elif ext == ".txt":
        return generate_chunks_from_text(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

#embedding
def build_faiss_index(chunks,output_prefix, batch_size=100, embedding_model="text-embedding-3-small"):
    embeddings = []
    for start in tqdm(range(0, len(chunks), batch_size)):
        batch = chunks[start:start + batch_size]
        response = client.embeddings.create(
            input=batch,
            model=embedding_model
        )
        embeddings.extend([item.embedding for item in response.data])

    embeddings_array = np.array(embeddings).astype('float32')
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)

    # 独立保存
    faiss_path = f"{output_prefix}.faiss"
    chunks_path = f"{output_prefix}_chunks.npy"
    faiss.write_index(index, faiss_path)
    np.save(chunks_path, chunks, allow_pickle=True)
    
    print(f"✅ 索引已保存：{faiss_path}")
    print(f"✅ chunks 已保存：{chunks_path}")
    return index


PSI_chunks = generate_chunks_from(file_path = "./docs/PSI.pdf")
context1_chunks = generate_chunks_from(file_path = "./docs/context1.txt")


PSI_faiss = build_faiss_index(PSI_chunks,output_prefix="PSI_books")
context1_faiss = build_faiss_index(context1_chunks, output_prefix="context1")
