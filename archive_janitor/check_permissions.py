# check_permissions.py
import os
import stat

def check_permissions(root="."):
    for dirpath, dirnames, filenames in os.walk(root):
        for name in filenames + dirnames:
            path = os.path.join(dirpath, name)
            try:
                st = os.stat(path)
            except Exception as e:
                print(f"⚠️ Cannot access {path}: {e}")
                continue

            perms = stat.filemode(st.st_mode)
            owner = os.getlogin()
            print(f"{perms} {path} (owner: {owner})")

if __name__ == "__main__":
    check_permissions(".")

