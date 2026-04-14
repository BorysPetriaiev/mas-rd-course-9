# 🤖 AI Research Agent

Персональний автономний агент.

Агент працює за циклом **ReAct** (Reasoning + Acting): він обмірковує запит, планує дії, використовує інструменти та формує фінальний аналітичний звіт.



## 🛠 Технологічний стек
- **Python 3.12**
- **uv** 
- **LangGraph** 
- **OpenAI**

## 📦 Встановлення та запуск

### 1. Підготовка середовища
Переконайтеся, що у вас встановлено інструмент [uv](https://docs.astral.sh/uv/).

```bash
# Клонуйте проєкт та перейдіть у папку
cd mas-rd-course-8

# Синхронізуйте залежності
uv sync
```


### 2. Налаштування конфіденційних даних
Створіть файл .env у кореневій директорії та додайте ваші ключі:

```
OPENAI_API_KEY=your_openai_key_here
```

### 3. Запуск агента

```bash
uv run ingest.py
uv run mcp_servers/search_mcp.py
uv run mcp_servers/report_mcp.py
uv run acp_server.py

uv run main.py

```

### Приклади запитів

- "Порівняй стратегії індексації: Flat, HNSW та IVF."
- "Досліди підхід Agentic RAG"

### Структура проєкту

```
/
├── main.py              # REPL with HITL interrupt/resume loop
├── supervisor.py        # Supervisor agent + ACP delegation tools
├── acp_server.py        # ACP server with 3 agents (planner, researcher, critic)
├── mcp_servers/
│   ├── search_mcp.py    # SearchMCP: web_search, read_url, knowledge_search
│   └── report_mcp.py    # ReportMCP: save_report
├── schemas.py           # Pydantic models: ResearchPlan, CritiqueResult
├── mcp_utils.py         # mcp_tools_to_langchain helper (from lesson 9)
├── config.py            # Prompts + settings + ports
├── retriever.py         # Reused from hw5/hw8
├── ingest.py            # Reused from hw5/hw8
├── pyproject.toml
├── data/                # Documents for RAG
└── .env                 # API keys (do not commit!)

```


### Приклад відпрацювання 
```
uv run main.py
🤖 Multi-agent research system ready! (type 'exit' to quit)
   Architecture: Supervisor → Planner → Researcher → Critic → save_report


You: Compare RAG approaches: naive, sentence-window, and parent-child

🔧 [agent] plan(request='Compare RAG (Retrieval-Augmented Generation) approaches: naive, sentence-window, and parent-child. Discuss their methodo...')
   📎 [plan]: Research Plan:
Goal: To compare three Retrieval-Augmented Generation (RAG) approaches: naive, sentence-window, and parent-child, focusing on their methodologies, advantages, disadvantages, and use cases.
Search Queries:
  - RAG naive approach methodology advantages disadvantages use cases
  - RAG se

🔧 [agent] research(request="{'plan': {'goal': 'To compare three Retrieval-Augmented Generation (RAG) approaches: naive, sentence-window, and parent-...")
   📎 [research]: Error invoking tool 'research' with kwargs {'request': {'plan': {'goal': 'To compare three Retrieval-Augmented Generation (RAG) approaches: naive, sentence-window, and parent-child, focusing on their methodologies, advantages, disadvantages, and use cases.', 'search_queries': ['RAG naive approach me

🔧 [agent] research(request='Compare three Retrieval-Augmented Generation (RAG) approaches: naive, sentence-window, and parent-child. Discuss their m...')
   📎 [research]: ### Overview of Retrieval-Augmented Generation (RAG)

Retrieval-Augmented Generation (RAG) is a technique that enhances the capabilities of large language models (LLMs) by integrating information retrieval mechanisms. This approach allows LLMs to access and incorporate external data sources, such as

🔧 [agent] critique(findings='### Overview of Retrieval-Augmented Generation (RAG)\n\nRetrieval-Augmented Generation (RAG) is a technique that enhances ...')
   📎 [critique]: Critique Result:
Verdict: REVISE
Is Fresh: False
Is Complete: False
Is Well Structured: True
Strengths:
  + Clear explanation of RAG components and methodologies.
  + Logical organization of content into sections.
  + Good overview of applications across various domains.
Gaps:
  - Lacks recent advan

🔧 [agent] research(request='Revise the comparison of RAG approaches: naive, sentence-window, and parent-child by incorporating findings and advancem...')
   📎 [research]: ### Revised Comparison of RAG Approaches: Naive, Sentence-Window, Parent-Child, Long RAG, and Self-RAG

Retrieval-Augmented Generation (RAG) has evolved significantly from its initial implementations, with advancements in techniques and architectures that enhance the performance and applicability of

🔧 [agent] save_report(filename='comparison_of_rag_approaches_naive_sentence_window_parent_child_long_self_rag.md', content='# Revised Comparison of RAG Approaches: Naive, Sentence-Window, Parent-Child, Long RAG, and Self-RAG\n\nRetrieval-Augmente...')

============================================================
⏸️  ACTION REQUIRES APPROVAL
============================================================
  Tool:  save_report
  File:  comparison_of_rag_approaches_naive_sentence_window_parent_child_long_self_rag.md

  Content preview:

    # Revised Comparison of RAG Approaches: Naive, Sentence-Window, Parent-Child, Long RAG, and Self-RAG
    
    Retrieval-Augmented Generation (RAG) has evolved significantly from its initial implementations, with advancements in techniques and architectures that enhance the performance and applicability of AI systems. This comparison will explore traditional RAG approaches—naive, sentence-window, and parent-child—while also incorporating recent innovations such as Long RAG and Self-RAG, as well as other advanced techniques that have emerged between 2024 and 2026.
    
    ## 1. Traditional RAG Approaches
    
    **1....
============================================================

👉 approve / edit / reject: approve
   📎 [save_report]: Report saved to: output/comparison_of_rag_approaches_naive_sentence_window_parent_child_long_self_rag.md

🤖 [Agent]: The research comparing various Retrieval-Augmented Generation (RAG) approaches has been successfully completed and documented. The report includes a detailed analysis of the naive, sentence-window, and parent-child methods, as well as recent advancements such as Long RAG and Self-RAG. 

### Summary of the Report:
- **Introduction**: Overview of RAG and its significance in enhancing AI capabilities.
- **Traditional RAG Approaches**: Detailed methodologies, advantages, and disadvantages of naive, sentence-window, and parent-child approaches.
- **Recent Advancements**: Discussion of Long RAG and Self-RAG, along with other innovative techniques like DeepRAG, CoRAG, VideoRAG, and GraphRAG.
- **Evaluation and Future Directions**: Insights into the evolving landscape of RAG and potential future research areas.
- **Conclusion**: Summary of the advancements in RAG techniques and their implications for AI applications.

The final report has been saved as `comparison_of_rag_approaches_naive_sentence_window_parent_child_long_self_rag.md`. You can access it for a comprehensive understanding of the topic.

You: exit
👋 Goodbye!
```