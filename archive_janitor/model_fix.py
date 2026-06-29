import os
import shutil

file_path = os.path.expanduser(
    "~/miniforge3/envs/feral_echo/lib/python3.11/site-packages/gpt4all/_pyllmodel.py"
)
backup_path = file_path + ".bak"
shutil.copyfile(file_path, backup_path)
print(f"Backup created: {backup_path}")

with open(file_path, "r") as f:
    lines = f.readlines()

patched_lines = []
skip_block = False

for line in lines:
    # Remove any line related to sysctl/subprocess
    if "sysctl.proc_translated" in line or "subprocess.run(" in line:
        if not skip_block:
            patched_lines.append("is_translated = False  # safe bypass\n")
            skip_block = True
        continue
    # Remove dangling try/if
    if line.strip() == "try:" or line.strip().startswith("if "):
        continue
    patched_lines.append(line)

with open(file_path, "w") as f:
    f.writelines(patched_lines)

print("✅ GPT4All _pyllmodel.py patched_

