from types import ModuleType

from mcp.server import FastMCP
from mcp.server.fastmcp.prompts import Prompt


def add_prompts_from_module(server: FastMCP, module: ModuleType) -> None:
    """Adds all prompts from a module to the server."""
    for prompt in dir(module):
        if not prompt.startswith("__") or not prompt.endswith("__"):
            attribute = getattr(module, prompt)
            if callable(attribute):
                server.add_prompt(Prompt.from_function(attribute))


def add_tools_from_module(server: FastMCP, module: ModuleType):
    """Adds all tools from a module to the server."""
    for tool in dir(module):
        if not tool.startswith("__") or not tool.endswith("__"):
            attribute = getattr(module, tool)
            if callable(attribute):
                server.add_tool(attribute)
