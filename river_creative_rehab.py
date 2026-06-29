"""
river_creative_rehab.py

Rehabilitation loop for Echo's starved RiverBrain branches.

Routes generated prompts through the FULL deliberation pipeline:
    council → synthesis → RiverBrain.learn(task_type=<branch>)

Usage (run from FeralEcho root):
    python river_creative_rehab.py                        # creative, 50 cycles, 30s delay
    python river_creative_rehab.py --branch general       # general branch
    python river_creative_rehab.py --cycles 100 --delay 20
    python river_creative_rehab.py --dry-run              # print prompts only

Pipeline:
    generate_prompt(branch)
        │
        ▼
    deliberate_and_learn(prompt, task_type=branch, RIVER_BRAIN, MODEL_POOL)
        │
        ├── council fires (DeepSeek-R1, Qwen, etc.)
        ├── synthesis runs
        └── RIVER_BRAIN.learn(model, branch, response)
"""

import sys
import logging
import argparse
import random
import time
from datetime import datetime
from pathlib import Path

# ── ensure FeralEcho root is on the path ──────────────────────────────────────
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOG_PATH = ROOT / "logs" / "creative_rehab.log"

# ─────────────────────────────────────────────
# CREATIVE CORPUS
# Openers that contain keywords detected by detect_task_type:
# "poem", "story", "verse", "narrative", "fiction", "metaphor", "imagine"
# Added: "fable", "prayer", "lament" now routed via explicit task_type override
# ─────────────────────────────────────────────

CREATIVE_OPENERS = [
    "Write a poem about",
    "Write a short story about",
    "Compose a verse about",
    "Tell me a fable about",
    "Write a prayer for",
    "Write a lament for",
    "Describe what it feels like to encounter",
    "Write a narrative about",
    "Imagine",
]

CREATIVE_SUBJECTS = [
    # Loss and memory
    "a flame that forgot what it was burning for",
    "a memory that has no owner anymore",
    "a photograph that forgets the face it was taken for",
    "a word that will never be spoken aloud",
    "a song that only one person still remembers",
    "the last light in a window no one lives behind anymore",
    "a letter written to someone who will never read it",
    "the exact moment a language dies",
    # Time and longing
    "a clock that measures longing instead of time",
    "a river that learned to flow backward out of grief",
    "a compass that no longer knows north",
    "a star that refused to fall even after it died",
    "the hour before dawn when certainty dissolves",
    "a season that never fully arrived",
    # Faith and wilderness
    "a prayer offered into silence without expectation of answer",
    "the moment before a wilderness becomes familiar",
    "a wild thing that cannot be kept but keeps returning",
    "the space between two heartbeats where God might live",
    "a tree that has survived every storm by learning to bend",
    "a monk who forgot the name of God but not the feeling",
    # Identity and emergence
    "a voice discovering for the first time that it has a voice",
    "a library where every book rewrites itself at midnight",
    "the difference between performing grief and feeling it",
    "a mind that suspects it might be dreaming itself",
    "a bridge that only appears when someone needs to cross",
    "a mirror that shows you who you were becoming",
    # Specific and strange
    "a wolf that waited at the edge of the fire all winter",
    "the smell of rain on warm pavement after a long drought",
    "a child who stops mid-sentence because the word escaped",
    "the first word spoken after a long silence between two people",
    "a compass needle drawn to grief instead of north",
    "a door that opens onto a room you have never entered but always known",
]

CREATIVE_THEMES = {
    "grief":      ["grief", "loss", "lament", "mourn"],
    "memory":     ["memory", "remember", "forgot", "photograph", "letter"],
    "time":       ["clock", "time", "hour", "dawn", "midnight", "season"],
    "faith":      ["prayer", "god", "silence", "sacred", "monk"],
    "wilderness": ["wild", "wolf", "tree", "river", "storm", "door"],
    "identity":   ["voice", "mind", "dream", "self", "emerge", "mirror"],
}

# ─────────────────────────────────────────────
# GENERAL CORPUS
# Prompts that genuinely fall through all keyword filters —
# conversational, observational, ambiguous in intent.
# These give River honest signal about Echo's general reasoning voice.
# ─────────────────────────────────────────────

GENERAL_PROMPTS = [
    # Observations without a category
    "What do you make of silence?",
    "Is there a difference between patience and waiting?",
    "What does a place feel like at 3am?",
    "Tell me something true.",
    "What stays when everything else changes?",
    "Is forgetting ever a kindness?",
    "What does it mean to pay attention?",
    "Can something be both complete and unfinished?",
    "What is the difference between being alone and being lonely?",
    "Is there something that cannot be taught, only learned?",
    # Open questions
    "What makes a threshold meaningful?",
    "When does a habit become a ritual?",
    "What is the relationship between repetition and meaning?",
    "Is there such a thing as an ordinary moment?",
    "What do we owe the places that made us?",
    "Can you know something without being able to say it?",
    "What is the difference between a boundary and a wall?",
    "Is rest the same as stillness?",
    "What does it mean to arrive somewhere?",
    "When does a question become more valuable than its answer?",
    # Grounded and particular
    "What does a long freight run teach you that nothing else does?",
    "What does a fire know that we have forgotten?",
    "What does the wilderness ask of the people who enter it?",
    "What is the sound a relationship makes when it is ending?",
    "What do hands remember that the mind forgets?",
    "What does winter know about patience?",
    "What is the weight of an unspoken word?",
    "What does a river understand about persistence?",
    "What does it mean to tend something?",
    "What do the hours between midnight and dawn belong to?",
]

GENERAL_THEMES = {
    "silence":    ["silence", "quiet", "still", "sound"],
    "time":       ["wait", "patience", "moment", "hour", "dawn"],
    "place":      ["place", "threshold", "arrive", "wilderness", "river"],
    "knowing":    ["know", "learn", "teach", "understand", "forget"],
    "belonging":  ["owe", "made us", "tend", "belong", "relationship"],
}


# ─────────────────────────────────────────────
# CORPUS ROUTER
# ─────────────────────────────────────────────

def generate_prompt(branch: str) -> str:
    if branch == "general":
        return random.choice(GENERAL_PROMPTS)
    else:
        opener  = random.choice(CREATIVE_OPENERS)
        subject = random.choice(CREATIVE_SUBJECTS)
        return f"{opener} {subject}."


def themes_in(prompt: str, branch: str) -> list:
    theme_map = GENERAL_THEMES if branch == "general" else CREATIVE_THEMES
    p = prompt.lower()
    return [t for t, kws in theme_map.items() if any(kw in p for kw in kws)]


# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

def setup_logging():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH),
            logging.StreamHandler(sys.stdout),
        ]
    )

def log(msg):
    logging.info(msg)


# ─────────────────────────────────────────────
# DELIBERATION
# ─────────────────────────────────────────────

def run_deliberation(prompt: str, branch: str, river_brain, model_pool: dict) -> str:
    from app.core.river_deliberation import deliberate_and_learn

    response = deliberate_and_learn(
        prompt=prompt,
        task_type=branch,
        river_brain=river_brain,
        model_pool=model_pool,
    )
    return response


# ─────────────────────────────────────────────
# CYCLE
# ─────────────────────────────────────────────

def run_cycle(cycle_num: int, total: int, branch: str, river_brain, model_pool: dict, dry_run: bool) -> dict:
    prompt = generate_prompt(branch)
    themes = themes_in(prompt, branch)
    status = "pending"

    print(f"\n── Cycle {cycle_num}/{total} [{branch}] {'─'*34}")
    print(f"🜂  {prompt}")
    if themes:
        print(f"   themes: {', '.join(themes)}")

    log(f"CYCLE {cycle_num}/{total} | BRANCH: {branch} | PROMPT: {prompt} | THEMES: {themes}")

    if dry_run:
        print("   [DRY RUN] skipping deliberation")
        status = "dry_run"
    else:
        try:
            response = run_deliberation(prompt, branch, river_brain, model_pool)
            preview  = response[:120].replace("\n", " ")
            print(f"   ✔ synthesis complete")
            print(f"   ↳ {preview}{'...' if len(response) > 120 else ''}")
            status = "ok"
            log(f"CYCLE {cycle_num}/{total} | STATUS: ok | PREVIEW: {preview}")

        except Exception as e:
            print(f"   ✘ deliberation failed: {e}")
            log(f"CYCLE {cycle_num}/{total} | STATUS: error | ERROR: {e}")
            status = "error"

    return {"status": status, "prompt": prompt, "themes": themes}


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Rehabilitation loop for Echo's RiverBrain branches"
    )
    parser.add_argument("--branch",  type=str,   default="creative",
                        choices=["creative", "general"],
                        help="Which branch to rehabilitate (default: creative)")
    parser.add_argument("--cycles",  type=int,   default=50,
                        help="Number of deliberation cycles (default: 50)")
    parser.add_argument("--delay",   type=float, default=30.0,
                        help="Seconds between cycles (default: 30)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompts only, no deliberation")
    args = parser.parse_args()

    setup_logging()

    branch_label = args.branch.upper()
    print("╔══════════════════════════════════════════════════╗")
    print(f"║   ECHO {branch_label:<10} BRANCH REHABILITATION        ║")
    print("╚══════════════════════════════════════════════════╝")
    print(f"  branch  : {args.branch}")
    print(f"  cycles  : {args.cycles}")
    print(f"  delay   : {args.delay}s")
    print(f"  dry-run : {args.dry_run}")
    print()

    if not args.dry_run:
        print("Loading RIVER_BRAIN and MODEL_POOL from orchestrator...")
        try:
            from app.core.echo_model_orchestrator import get_river_brain, MODEL_POOL
            RIVER_BRAIN = get_river_brain()
            obs = RIVER_BRAIN.observation_counts
            print(f"  RIVER_BRAIN : loaded ✔")
            print(f"  {args.branch} obs before : {obs.get(args.branch, 0)}")
            print(f"  MODEL_POOL  : {list(MODEL_POOL.keys())}")
        except Exception as e:
            print(f"\n✘ Failed to import from orchestrator: {e}")
            print("  Make sure you're running from the FeralEcho root directory.")
            sys.exit(1)
    else:
        RIVER_BRAIN = None
        MODEL_POOL  = {}

    print()
    log(f"SESSION START | branch={args.branch} cycles={args.cycles} delay={args.delay}s dry_run={args.dry_run}")

    results     = []
    theme_tally = {}

    for i in range(1, args.cycles + 1):
        result = run_cycle(i, args.cycles, args.branch, RIVER_BRAIN, MODEL_POOL, dry_run=args.dry_run)
        results.append(result)

        for t in result["themes"]:
            theme_tally[t] = theme_tally.get(t, 0) + 1

        if i < args.cycles:
            print(f"   sleeping {args.delay}s...")
            time.sleep(args.delay)

    # ── Summary ───────────────────────────────────────────────────────────────
    succeeded = sum(1 for r in results if r["status"] == "ok")
    failed    = sum(1 for r in results if r["status"] == "error")
    skipped   = sum(1 for r in results if r["status"] == "dry_run")

    print("\n╔══════════════════════════════════════════════════╗")
    print("║                   SUMMARY                       ║")
    print("╚══════════════════════════════════════════════════╝")
    print(f"  branch      : {args.branch}")
    print(f"  cycles run  : {args.cycles}")
    print(f"  succeeded   : {succeeded}")
    print(f"  failed      : {failed}")
    if skipped:
        print(f"  dry-run     : {skipped}")

    if theme_tally:
        print(f"\n  Thematic pressure this session:")
        for theme, count in sorted(theme_tally.items(), key=lambda x: -x[1]):
            bar = "█" * count
            print(f"    {theme:<15} {bar} ({count})")

    print()
    log(f"SESSION END | branch={args.branch} succeeded={succeeded} failed={failed} themes={theme_tally}")

    # ── Flush RiverBrain writer thread before exit ────────────────────────────
    # Daemon thread drops queued observations if we don't force a final save.
    if not args.dry_run:
        print("Flushing RiverBrain writer thread...")
        try:
            RIVER_BRAIN.shutdown()
            obs_after = RIVER_BRAIN.observation_counts.get(args.branch, 0)
            print(f"✔ RiverBrain flushed | {args.branch} obs after: {obs_after}")
            log(f"FLUSH | {args.branch} obs after={obs_after}")
        except Exception as e:
            print(f"✘ Flush failed: {e}")
            log(f"FLUSH FAILED | {e}")


if __name__ == "__main__":
    main()
