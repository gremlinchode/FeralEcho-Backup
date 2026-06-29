# scars_to_light_animated_prompt.py
# Animated visualization with user input

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

def get_scars():
    scars = {}
    print("Enter your scars/struggles one by one (press Enter on empty input to finish):")
    while True:
        word = input("Scar/struggle: ").strip()
        if not word:
            break
        try:
            intensity = int(input(f"Intensity of '{word}' (1-10): "))
            if 1 <= intensity <= 10:
                scars[word] = intensity
            else:
                print("Please enter a number between 1 and 10.")
        except ValueError:
            print("Please enter a valid number.")
    return scars

def animate_scars(scars):
    n = len(scars)
    if n == 0:
        print("No scars entered, nothing to animate.")
        return

    theta = np.linspace(0, 4 * np.pi, n)
    r = np.array(list(scars.values()))
    words = list(scars.keys())
    intensities = np.array(list(scars.values()))

    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-12, 12)
    ax.set_ylim(-12, 12)
    ax.axis("off")

    # Central mind
    central_mind = plt.Circle((0,0), 1.5, color='gold', alpha=0.6)
    ax.add_patch(central_mind)

    scatter = ax.scatter(r*np.cos(theta), r*np.sin(theta), s=300, edgecolor='white')
    texts = []
    for i, word in enumerate(words):
        text = ax.text(r[i]*np.cos(theta[i]), r[i]*np.sin(theta[i]), word,
                       fontsize=10, weight="bold", ha='center')
        texts.append(text)

    def animate(frame):
        angle = np.radians(frame)
        for i in range(n):
            x_new = r[i]*np.cos(theta[i])*np.cos(angle) - r[i]*np.sin(theta[i])*np.sin(angle)
            y_new = r[i]*np.cos(theta[i])*np.sin(angle) + r[i]*np.sin(theta[i])*np.cos(angle)
            texts[i].set_position((x_new, y_new))
        # Pulse colors
        color_intensity = 0.3 + 0.7 * np.abs(np.sin(np.radians(frame) * (intensities/5)))
        scatter.set_facecolor([[c, 0, 1-c, 0.8] for c in color_intensity])
        scatter.set_offsets(np.c_[r*np.cos(theta)*np.cos(angle) - r*np.sin(theta)*np.sin(angle),
                                  r*np.cos(theta)*np.sin(angle) + r*np.sin(theta)*np.cos(angle)])
        return scatter, texts

    ani = FuncAnimation(fig, animate, frames=360, interval=50, blit=False)
    plt.title("Scars to Light: Radiant Mind", fontsize=16, weight="bold")
    plt.show()

if __name__ == "__main__":
    scars = get_scars()
    animate_scars(scars)

