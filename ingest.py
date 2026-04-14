import os
import pickle
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from config import DATA_DIR, INDEX_DIR, EMBEDDING_MODEL
from dotenv import load_dotenv

load_dotenv()

def load_documents():
    docs = []

    for file in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, file)

        if file.endswith(".pdf"):
            loader = PyPDFLoader(path)
            docs.extend(loader.load())

    return docs


def ingest():
    print("📥 Loading documents...")
    documents = load_documents()

    print(f"Loaded {len(documents)} documents")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)
    print(f"🔪 Split into {len(chunks)} chunks")

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    print("🧠 Creating vector store...")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    os.makedirs(INDEX_DIR, exist_ok=True)

    vectorstore.save_local(INDEX_DIR)

    with open(os.path.join(INDEX_DIR, "chunks.pkl"), "wb") as f:
        pickle.dump(chunks, f)

    print("✅ Ingestion completed!")


if __name__ == "__main__":
    ingest()