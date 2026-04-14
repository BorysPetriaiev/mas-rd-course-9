from typing import Any, Optional

from pydantic import create_model, Field
from langchain_core.tools import StructuredTool


def _json_schema_to_fields(schema: dict) -> dict:
    """Convert a JSON Schema object to Pydantic field definitions."""
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    fields: dict = {}
    for prop_name, prop_info in properties.items():
        prop_type = prop_info.get("type", "string")
        if prop_type == "integer":
            annotation = int
        elif prop_type == "boolean":
            annotation = bool
        elif prop_type == "number":
            annotation = float
        else:
            annotation = str

        description = prop_info.get("description", "")
        if prop_name in required:
            fields[prop_name] = (annotation, Field(description=description))
        else:
            fields[prop_name] = (
                Optional[annotation],
                Field(default=None, description=description),
            )

    return fields


def mcp_tools_to_langchain(client: Any, tools: list) -> list:
    """Convert a list of MCP tool descriptors to LangChain StructuredTools.

    Each resulting tool is async and calls `client.call_tool(name, kwargs)`.
    The `client` must remain open for the lifetime of tool execution.
    """
    lc_tools = []

    for tool in tools:
        name: str = tool.name
        description: str = tool.description or ""
        input_schema: dict = getattr(tool, "inputSchema", {}) or {}

        fields = _json_schema_to_fields(input_schema)
        if not fields:
            fields = {"input": (str, Field(description="Input"))}

        args_model = create_model(f"{name}_args", **fields)

        def _make_coroutine(tool_name: str):
            async def _run(**kwargs: Any) -> str:
                result = await client.call_tool(tool_name, kwargs)
                items = getattr(result, "content", None) or result
                if items:
                    return "\n".join(
                        item.text if hasattr(item, "text") else str(item)
                        for item in items
                    )
                return ""

            _run.__name__ = tool_name
            return _run

        lc_tool = StructuredTool.from_function(
            coroutine=_make_coroutine(name),
            name=name,
            description=description,
            args_schema=args_model,
        )
        lc_tools.append(lc_tool)

    return lc_tools
