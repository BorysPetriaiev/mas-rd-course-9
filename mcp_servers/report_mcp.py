import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import fastmcp
from config import REPORTS_DIR, REPORT_MCP_PORT

mcp = fastmcp.FastMCP("ReportMCP")


@mcp.resource("resource://output-dir")
def output_dir() -> str:
    """Returns the output directory path and list of saved reports."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".md")]
    abs_path = os.path.abspath(REPORTS_DIR)
    return f"Path: {abs_path}, Reports: {', '.join(files) if files else 'none'}"


@mcp.tool
def save_report(filename: str, content: str) -> str:
    """Save a research report to a markdown file in the output directory."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Report saved to: {path}"


if __name__ == "__main__":
    mcp.run(transport="http", port=REPORT_MCP_PORT)
