import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from fastmcp import Client as MCPClient

from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Server

from mcp_utils import mcp_tools_to_langchain
from schemas import ResearchPlan, CritiqueResult
from config import (
    PLANNER_PROMPT,
    RESEARCHER_PROMPT,
    CRITIC_PROMPT,
    MAX_FINDINGS_LEN,
    SEARCH_MCP_URL,
    ACP_SERVER_PORT,
)

load_dotenv()

server = Server()


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
    )


def _extract_text(input: list[Message]) -> str:
    """Extract plain-text content from the first ACP message."""
    for msg in input:
        for part in msg.parts:
            if part.content:
                return part.content
    return ""


def _agent_message(text: str) -> Message:
    return Message(role="agent", parts=[MessagePart(content=text, content_type="text/plain")])


# ---------------------------------------------------------------------------
# Planner agent
# ---------------------------------------------------------------------------

@server.agent(name="planner", description="Creates a structured research plan")
async def planner(input: list[Message]) -> AsyncGenerator[Message | MessagePart, None]:
    text = _extract_text(input)

    async with MCPClient(SEARCH_MCP_URL) as mcp:
        mcp_tools_list = await mcp.list_tools()
        lc_tools = mcp_tools_to_langchain(mcp, mcp_tools_list)

        agent = create_react_agent(
            _llm(),
            tools=lc_tools,
            prompt=PLANNER_PROMPT,
            response_format=ResearchPlan,
        )

        result = await agent.ainvoke({"messages": [("user", text)]})

    plan = result.get("structured_response")
    if plan:
        queries = "\n".join(f"  - {q}" for q in plan.search_queries)
        sources = ", ".join(plan.sources_to_check)
        response = (
            f"Research Plan:\n"
            f"Goal: {plan.goal}\n"
            f"Search Queries:\n{queries}\n"
            f"Sources to Check: {sources}\n"
            f"Output Format: {plan.output_format}"
        )
    else:
        response = result["messages"][-1].content

    yield _agent_message(response)


# ---------------------------------------------------------------------------
# Researcher agent
# ---------------------------------------------------------------------------

@server.agent(name="researcher", description="Executes the research plan and collects findings")
async def researcher(input: list[Message]) -> AsyncGenerator[Message | MessagePart, None]:
    text = _extract_text(input)

    async with MCPClient(SEARCH_MCP_URL) as mcp:
        mcp_tools_list = await mcp.list_tools()
        lc_tools = mcp_tools_to_langchain(mcp, mcp_tools_list)

        agent = create_react_agent(
            _llm(),
            tools=lc_tools,
            prompt=RESEARCHER_PROMPT,
        )

        result = await agent.ainvoke({"messages": [("user", text)]})

    yield _agent_message(result["messages"][-1].content)


# ---------------------------------------------------------------------------
# Critic agent
# ---------------------------------------------------------------------------

@server.agent(name="critic", description="Evaluates research quality and returns a structured verdict")
async def critic(input: list[Message]) -> AsyncGenerator[Message | MessagePart, None]:
    text = _extract_text(input)

    if len(text) > MAX_FINDINGS_LEN:
        text = text[:MAX_FINDINGS_LEN] + "\n\n...[truncated for evaluation]"

    async with MCPClient(SEARCH_MCP_URL) as mcp:
        mcp_tools_list = await mcp.list_tools()
        lc_tools = mcp_tools_to_langchain(mcp, mcp_tools_list)

        agent = create_react_agent(
            _llm(),
            tools=lc_tools,
            prompt=CRITIC_PROMPT,
            response_format=CritiqueResult,
        )

        result = await agent.ainvoke({"messages": [("user", text)]})

    critique = result.get("structured_response")
    if critique:
        strengths = "\n".join(f"  + {s}" for s in critique.strengths) or "  (none)"
        gaps = "\n".join(f"  - {g}" for g in critique.gaps) or "  (none)"
        revisions = "\n".join(f"  * {r}" for r in critique.revision_requests) or "  (none)"
        response = (
            f"Critique Result:\n"
            f"Verdict: {critique.verdict}\n"
            f"Is Fresh: {critique.is_fresh}\n"
            f"Is Complete: {critique.is_complete}\n"
            f"Is Well Structured: {critique.is_well_structured}\n"
            f"Strengths:\n{strengths}\n"
            f"Gaps:\n{gaps}\n"
            f"Revision Requests:\n{revisions}"
        )
    else:
        response = result["messages"][-1].content

    yield _agent_message(response)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    asyncio.run(server.serve(host="localhost", port=ACP_SERVER_PORT))
