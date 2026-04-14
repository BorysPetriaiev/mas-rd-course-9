import os
import pickle

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.retrievers import BM25Retriever
from sentence_transformers import CrossEncoder

from config import INDEX_DIR, EMBEDDING_MODEL, TOP_K, RERANK_TOP_K
from dotenv import load_dotenv

load_dotenv()

def get_retriever():
    print("🔄 Loading vector store...")

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    vectorstore = FAISS.load_local(
        INDEX_DIR,
        embeddings,
        allow_dangerous_deserialization=True
    )

    semantic_retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    # BM25
    with open(os.path.join(INDEX_DIR, "chunks.pkl"), "rb") as f:
        chunks = pickle.load(f)

    bm25_retriever = BM25Retriever.from_documents(chunks)
    bm25_retriever.k = TOP_K

    # reranker
    reranker = CrossEncoder("BAAI/bge-reranker-base")

    def retrieve(query: str):
        # 1. semantic search
        docs_semantic = semantic_retriever.invoke(query)

        # 2. BM25 search
        docs_bm25 = bm25_retriever.invoke(query)

        # 3. merge results
        docs = docs_semantic + docs_bm25

        # remove duplicates
        unique_docs = list({doc.page_content: doc for doc in docs}.values())

        # 4. rerank
        pairs = [(query, doc.page_content) for doc in unique_docs]
        scores = reranker.predict(pairs)

        ranked = sorted(
            zip(unique_docs, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return [doc for doc, _ in ranked[:RERANK_TOP_K]]

    return retrieve
