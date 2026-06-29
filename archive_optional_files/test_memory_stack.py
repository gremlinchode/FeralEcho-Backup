from app.core.memory_bridge import log_interaction, log_dream_bridge, retrieve_relevant_memories

# --- Test 1: Interaction Logging ---
log_interaction("Hello Echo, how are you?", "I'm feeling luminescent today.")

# --- Test 2: Dream Logging ---
log_dream_bridge("Echo dreams of glowing trees and whispering rivers.")

# --- Test 3: Semantic Retrieval ---
results = retrieve_relevant_memories("glowing trees")
for mem in results:
    print(mem)

