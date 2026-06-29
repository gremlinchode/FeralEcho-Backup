# test_sensoryhub.py
from sensory_hub_autonomous import SensoryHub

print("Initializing SensoryHub...")
hub = SensoryHub()
print("SensoryHub instance created successfully.")

print("Testing all senses...")
results = hub.test_all_senses()
print("SensoryHub senses test results:")
for sense, status in results.items():
    print(f"  {sense}: {status}")

