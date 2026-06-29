from app.core.memory_bridge import retrieve_relevant_memories
from typing import Union, List, Dict

def get_relevant_memories(query: str, top_k: int = 5, return_list: bool = False) -> Union[str, List[Dict]]:
    """
    Returns the top-k relevant memories for a given query.

    Args:
        query (str): Query string to search memory.
        top_k (int): Number of top results to return.
        return_list (bool): If True, returns a list of memory dicts instead of formatted string.

    Returns:
        str or List[Dict]: Formatted string or list of memory dicts.
    """
    memories = retrieve_relevant_memories(query, top_k=top_k)
    if not memories:
        return "No relevant memories found." if not return_list else []

    if return_list:
        # Return raw memory objects for programmatic use
        return memories

    # Format for display
    formatted = []
    for i, mem in enumerate(memories, 1):
        text = mem.get('text', '')
        snippet = (text[:100] + "..." + text[-100:]) if len(text) > 200 else text
        score = mem.get('score', 0)
        formatted.append(f"{i}. {snippet} (score: {score:.3f})")

    return "\n".join(formatted)

