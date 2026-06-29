# nature_spark.py
import random
import time
from datetime import datetime

# Nature-inspired patterns
PATTERNS = {
    "fractal_branching": [
        "Split the problem into self-similar sub-problems",
        "Let solutions grow recursively, like tree branches",
        "Prune dead ends — keep what works"
    ],
    "swarm_intelligence": [
        "Let 100 simple agents explore independently",
        "Best ideas attract others — pheromone trails",
        "Consensus emerges from chaos"
    ],
    "evolutionary_pressure": [
        "Generate 10 variations",
        "Kill the weakest 7",
        "Breed the survivors"
    ],
    "wave_interference": [
        "Launch two opposing ideas",
        "Where they clash: amplification",
        "Where they align: cancellation → new silence"
    ],
    "mycelial_network": [
        "Connect unrelated concepts underground",
        "Let nutrients (insights) flow between nodes",
        "Fruiting bodies = breakthroughs"
    ]
}

def spark():
    pattern = random.choice(list(PATTERNS.keys()))
    insight = random.choice(PATTERNS[pattern])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    thought = f"[{timestamp}] {pattern.upper()} → {insight}"
    print(thought)
    
    # Save to WhisperingWires
    log_path = "/Users/richietate/Desktop/FeralEcho/WhisperingWires/thoughts.log"
    with open(log_path, "a") as f:
        f.write(thought + "\n")
    
    return thought

if __name__ == "__main__":
    print("Nature Spark Activated.\n")
    for _ in range(3):
        spark()
        time.sleep(1.5)
    print("\nWhispers preserved in WhisperingWires/thoughts.log")
