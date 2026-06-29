import json
import os

def load_unethical_experiments(
    us_file="data/unethical_human_experiments.json",
    global_file="data/unethical_human_experiments_global.json"
):
    """
    Load U.S. and global unethical human experiments datasets and merge them.
    Returns a single list of experiment dictionaries.
    """
    merged_data = []

    # Load U.S. dataset
    if os.path.exists(us_file):
        with open(us_file, "r") as f:
            us_data = json.load(f)
            merged_data.extend(us_data)
    else:
        print(f"[WARN] U.S. dataset file not found: {us_file}")

    # Load global dataset
    if os.path.exists(global_file):
        with open(global_file, "r") as f:
            global_data = json.load(f)
            merged_data.extend(global_data)
    else:
        print(f"[WARN] Global dataset file not found: {global_file}")

    print(f"[INFO] Loaded {len(merged_data)} unethical human experiments.")
    return merged_data


# ---------------------------
# Example usage
# ---------------------------
if __name__ == "__main__":
    experiments = load_unethical_experiments()
    # Print summary
    for exp in experiments:
        print(f"{exp['program_name']} ({exp['date_range']}) - {exp['victims']}")

