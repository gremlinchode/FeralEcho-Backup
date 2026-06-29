# app/core/tool_manager.py
import logging

class Tool:
    def __init__(self, name, func, description=""):
        self.name = name
        self.func = func
        self.description = description

class ToolManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.tools = {}
        return cls._instance

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool
        logging.info(f"[ToolManager] Registered tool: {tool.name}")

    def list_tools(self):
        return list(self.tools.keys())

    def get_tool(self, name):
        return self.tools.get(name)
