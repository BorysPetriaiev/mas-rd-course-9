import os
import sys
import pickle
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import fastmcp
import trafilatura
from ddgs import DDGS

from retriever import get_retriever
from config import MAX_TEXT_LENGTH, INDEX_DIR, SEARCH_MCP_PORT

mcp = fastmcp.FastMCP("SearchMCP")

# Load retriever once at startup
_retriever = None


def _get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = get_retriever()
    return _retriever


@mcp.resource("resource://knowledge-base-stats")
def knowledge_base_stats() -> str:
    """Returns stats about the local knowledge base."""
    try:
        chunks_path = os.path.join(INDEX_DIR, "chunks.pkl")
        with open(chunks_path, "rb") as f:
            chunks = pickle.load(f)
        mtime = os.path.getmtime(chunks_path)
        last_updated = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        return f"Documents: {len(chunks)}, Last updated: {last_updated}"
    except Exception as e:
        return f"Knowledge base not available: {e}"


@mcp.tool
def web_search(query: str) -> str:
    """Search for information on the internet. Returns a concise list of results."""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))

    formatted = []
    for r in results:
        formatted.append(
            f"Title: {r.get('title')}\n"
            f"URL: {r.get('href')}\n"
            f"Snippet: {r.get('body')}\n"
        )

    return "\n---\n".join(formatted)


@mcp.tool
def read_url(url: str) -> str:
    """Fetches the full text content of a web page by URL."""
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return "Error: could not download the page."

    text = trafilatura.extract(downloaded)
    if not text:
        return "Error: could not extract text from the page."

    return text.strip()[:MAX_TEXT_LENGTH]


@mcp.tool
def knowledge_search(query: str) -> str:
    """Search the local knowledge base. Use for questions about ingested documents."""
    retriever = _get_retriever()
    docs = retriever(query)

    if not docs:
        return "Nothing found in the local knowledge base."

    results = []
    for i, doc in enumerate(docs):
        results.append(f"[Doc {i+1}]\n{doc.page_content[:500]}")

    return "\n\n".join(results)


if __name__ == "__main__":
    mcp.run(transport="http", port=SEARCH_MCP_PORT)
