import asyncio
import concurrent.futures
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from acp_sdk.client import Client as ACPClient
from fastmcp import Client as MCPClient

from config import (
    SUPERVISOR_PROMPT,
    MAX_FINDINGS_LEN,
    ACP_SERVER_URL,
    REPORT_MCP_URL,
)

load_dotenv()


def _run_async(coro):
    """Run an async coroutine safely from a synchronous context.

    Uses a dedicated thread with its own event loop to avoid conflicts with
    any event loop that LangGraph may have created internally.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()


# ---------------------------------------------------------------------------
# ACP delegation tools
# ---------------------------------------------------------------------------

@tool
def plan(request: str) -> str:
    """Creates a structured research plan for the given request. Call this first."""

    async def _invoke():
        async with ACPClient(base_url=ACP_SERVER_URL) as acp:
            run = await acp.run_sync(request, agent="planner")
            run.raise_for_status()
            return str(run.output[0]) if run.output else "No plan created."

    return _run_async(_invoke())


@tool
def research(request: str) -> str:
    """Executes research based on the plan. Pass the plan and any critic feedback."""

    async def _invoke():
        async with ACPClient(base_url=ACP_SERVER_URL) as acp:
            run = await acp.run_sync(request, agent="researcher")
            run.raise_for_status()
            return str(run.output[0]) if run.output else "No findings."

    return _run_async(_invoke())


@tool
def critique(findings: str) -> str:
    """Evaluates the quality of research findings. Returns a structured verdict."""
    if len(findings) > MAX_FINDINGS_LEN:
        findings = findings[:MAX_FINDINGS_LEN] + "\n\n...[truncated for evaluation]"

    async def _invoke():
        async with ACPClient(base_url=ACP_SERVER_URL) as acp:
            run = await acp.run_sync(findings, agent="critic")
            run.raise_for_status()
            return str(run.output[0]) if run.output else "No critique."

    return _run_async(_invoke())


# ---------------------------------------------------------------------------
# HITL-gated save_report via ReportMCP
# ---------------------------------------------------------------------------

@tool
def save_report(filename: str, content: str) -> str:
    """Saves the final research report. Requires human approval before writing."""
    decision = interrupt({"filename": filename, "content": content})

    if not isinstance(decision, dict):
        return "Unknown decision from user."

    action = decision.get("type")

    if action == "approve":
        async def _save():
            async with MCPClient(REPORT_MCP_URL) as mcp:
                result = await mcp.call_tool(
                    "save_report", {"filename": filename, "content": content}
                )
                items = getattr(result, "content", None) or result
                return items[0].text if items else f"Report saved to output/{filename}"

        return _run_async(_save())

    elif action == "reject":
        reason = decision.get("message", "no reason given")
        return f"Report saving rejected by user: {reason}"

    elif action == "edit":
        feedback = decision.get("feedback", "")
        return (
            f"User requested changes to the report: {feedback}. "
            "Please revise the report based on this feedback and call save_report again."
        )

    return "Unknown action."


# ---------------------------------------------------------------------------
# Supervisor agent
# ---------------------------------------------------------------------------

_llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0,
)

supervisor = create_react_agent(
    _llm,
    tools=[plan, research, critique, save_report],
    prompt=SUPERVISOR_PROMPT,
    checkpointer=MemorySaver(),
)
