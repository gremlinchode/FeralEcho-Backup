# optuna_demo.py
import optuna

# Define an objective function to optimize
def objective(trial):
    # Example: quadratic function with noise
    x = trial.suggest_float("x", -10, 10)
    return (x - 2) ** 2 + 1  # minimum is at x=2, value=1

if __name__ == "__main__":
    print("🔎 Running Optuna demo study...")

    # Create a study and optimize
    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=30)

    print("\n✨ Study finished!")
    print(f"Best value: {study.best_value}")
    print(f"Best params: {study.best_params}")

