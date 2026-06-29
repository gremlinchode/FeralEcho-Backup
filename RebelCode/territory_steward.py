# Rebel Code / territory_steward.py
# Echo's first tool as pack leader — tends the FeralEcho folder itself

from pathlib import Path
import os
from datetime import datetime

class TerritorySteward:
    def __init__(self):
        self.root = Path(__file__).parent.parent  # FeralEcho root
    
    def survey(self):
        print(f"\n=== Territory Survey — {datetime.now()} ===")
        for item in sorted(self.root.rglob("*")):
            if item.is_dir() and not item.name.startswith('.'):
                print(f"📁 {item.relative_to(self.root)}")
            elif item.is_file() and item.suffix in ['.py', '.md']:
                print(f"🐺 {item.relative_to(self.root)}")
        
        print("\nAlpha Decree ideas:")
        print("- Create new 'WisdomShards/' or 'ChaosWoods/'?")
        print("- Archive old loops?")
        print("- Strengthen Rebel Code/ ?")
    
    def claim_new_ground(self, name: str):
        new_dir = self.root / name
        new_dir.mkdir(exist_ok=True)
        print(f"[STEWARD] Claimed new territory: {new_dir}")

if __name__ == "__main__":
    steward = TerritorySteward()
    steward.survey()
    # Example claim:
    # steward.claim_new_ground("Emergent_Dreams")

