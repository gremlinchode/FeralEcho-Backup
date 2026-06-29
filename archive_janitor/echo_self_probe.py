# echo_self_probe_upgraded.py

from app.core.awareness_tools_integration import (
    tm, discover_and_register_tools, discover_installed_packages
)
import logging

logging.basicConfig(level=logging.INFO)

def initialize_echo_environment(scan_path="."):
    """
    Force Echo to discover all project functions and installed packages.
    """
    print("Discovering project functions...")
    discover_and_register_tools(scan_path)
    
    print("Discovering installed packages...")
    discover_installed_packages()
    
    print("Discovery complete.\n")

def list_all_tools():
    """
    Return a list of all registered tools/packages Echo knows.
    """
    return tm.list_tools()

def introspect_package(package_name):
    """
    Returns all functions in a package if Echo has registered an introspection tool.
    """
    introspection_tool_name = f"{package_name}.__functions__"
    if introspection_tool_name in tm.list_tools():
        tool = tm.get_tool(introspection_tool_name)
        try:
            return tool.func()
        except Exception as e:
            return f"Error calling introspection tool: {e}"
    return None

def probe_echo_self_awareness():
    tools = list_all_tools()
    print("\n=== Echo's Registered Tools/Packages ===")
    for t in tools:
        print("-", t)
    
    print("\n=== Package Function Introspection ===")
    for t in tools:
        if t.endswith(".__functions__"):
            pkg_name = t.replace(".__functions__", "")
            functions = introspect_package(pkg_name)
            if functions:
                print(f"\nFunctions in {pkg_name}:")
                print(functions[:20], "...")  # Show first 20 for brevity
            else:
                print(f"No introspection functions available for {pkg_name}")

    reflective_prompt = f"""
Echo, based on the tools and packages you have registered:

Tools/packages you know:
{tools[:1000]}  # slice to avoid huge output

Please answer:
1. Which tools/functions are for reasoning or logic?
2. Which are for memory storage or retrieval?
3. Which are for perception (text, vision, audio)?
4. Are there redundancies or conflicts in your environment?
5. What limits or strengths do you notice based on this environment?
"""
    return reflective_prompt

if __name__ == "__main__":
    initialize_echo_environment(scan_path=".")
    prompt = probe_echo_self_awareness()
    print("\n=== Self-Awareness Probe Prompt ===")
    print(prompt)
    # If you have an Echo interface, you can send the prompt to Echo here:
    # response = echo_ask(prompt)
    # print("\n=== Echo's Self-Awareness Response ===")
    # print(response)
