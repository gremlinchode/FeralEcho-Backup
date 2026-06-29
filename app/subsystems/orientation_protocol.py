# FILE: app/subsystems/orientation_protocol.py
# Enhanced Orientation Protocol for Echo
# Fully offline, safe, read-only system survey
# Autonomous heuristic exploration, dynamic path classification, and resource monitoring

import os
import platform
import psutil
import subprocess
import time
from typing import Optional, Set
from app.subsystems.reflection_shard import ReflectionShard

class OrientationProtocol:
    def __init__(self, reflection_shard: Optional[ReflectionShard] = None, sandbox_path: str = ""):
        self.reflection_shard = reflection_shard
        self.sandbox_path = os.path.expanduser(sandbox_path)
        self.os_type = platform.system()
        self.known_paths: Set[str] = set()
        self.known_processes: Set[int] = set()

    def full_orientation(self):
        """Perform a full, safe system orientation and feed observations into ReflectionShard."""
        # --- High-Level System Info ---
        self._observe(f"OS: {platform.system()} {platform.release()} ({platform.version()})")
        self._observe(f"Machine: {platform.machine()} | Processor: {platform.processor()}")
        self._observe(f"Python version: {platform.python_version()} | Implementation: {platform.python_implementation()}")

        # --- CPU / Memory / Load ---
        self._observe_system_resources()

        # --- Disk & Sandbox Survey ---
        self._observe_disks_and_sandbox()

        # --- Environment Variables (safe subset) ---
        self._observe_environment()

        # --- Running Processes ---
        self._observe_processes()

        # --- Installed Python Packages ---
        self._observe_python_packages()

        # --- Autonomous Filesystem & Heuristic Exploration ---
        self._explore_filesystem()

    # ------------------------- OBSERVERS -------------------------
    def _observe(self, msg: str):
        if self.reflection_shard:
            self.reflection_shard.observe(f"[Orientation] {msg}")

    def _observe_system_resources(self):
        try:
            cpu_count = os.cpu_count()
            load_avg = os.getloadavg() if hasattr(os, "getloadavg") else "N/A"
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            self._observe(f"CPU cores: {cpu_count}, Load avg: {load_avg}")
            self._observe(f"Memory: total={mem.total//(1024*1024)}MB, available={mem.available//(1024*1024)}MB, used={mem.used//(1024*1024)}MB")
            self._observe(f"Swap: total={swap.total//(1024*1024)}MB, used={swap.used//(1024*1024)}MB")
        except Exception as e:
            self._observe(f"[Orientation Error - CPU/Memory] {e}")

    def _observe_disks_and_sandbox(self):
        try:
            root_disk = psutil.disk_usage("/")
            self._observe(f"Root disk: total={root_disk.total//(1024*1024)}MB, free={root_disk.free//(1024*1024)}MB, used={root_disk.used//(1024*1024)}MB")

            if os.path.exists(self.sandbox_path):
                sandbox_items = os.listdir(self.sandbox_path)
                self._observe(f"Sandbox path '{self.sandbox_path}' contains {len(sandbox_items)} items: {sandbox_items[:10]}...")
            else:
                self._observe(f"Sandbox path '{self.sandbox_path}' does not exist")
        except Exception as e:
            self._observe(f"[Orientation Error - Disk/Sandbox] {e}")

    def _observe_environment(self):
        safe_env_vars = ["HOME", "PATH", "USER", "SHELL", "TMPDIR", "PYTHONPATH"]
        env_snapshot = {k: os.environ.get(k, "") for k in safe_env_vars}
        self._observe(f"Environment snapshot: {env_snapshot}")

    def _observe_processes(self):
        try:
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                pid = proc.info['pid']
                if pid not in self.known_processes:
                    self.known_processes.add(pid)
                    mem_info = proc.info.get('memory_info')
                    mem_mb = mem_info.rss//(1024*1024) if mem_info else 0
                    self._observe(f"PROC: {proc.info['name']} (PID: {pid}) | Memory: {mem_mb}MB")
        except Exception as e:
            self._observe(f"[Orientation Error - Processes] {e}")

    def _observe_python_packages(self):
        try:
            result = subprocess.run(["pip", "list", "--format=freeze"], capture_output=True, text=True)
            packages = result.stdout.strip().split("\n")
            self._observe(f"Python packages installed (first 10): {packages[:10]}...")
        except Exception as e:
            self._observe(f"[Orientation Error - Python Packages] {e}")

    # ------------------------- HEURISTIC FILESYSTEM EXPLORER -------------------------
    def _explore_filesystem(self):
        roots = self._get_dynamic_roots()
        for root in roots:
            self._scan_path(root)

    def _get_dynamic_roots(self):
        roots = [os.path.expanduser("~")]

        if self.os_type == "Windows":
            for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                path = f"{drive}:\\"
                if os.path.exists(path):
                    roots.append(path)
        else:  # macOS / Linux
            for mount in ["/", "/mnt", "/Volumes", "/media", "/tmp"]:
                if os.path.exists(mount):
                    roots.append(mount)
        return roots

    def _scan_path(self, path: str, depth: int = 0, max_depth: int = 5):
        if depth > max_depth or not os.path.exists(path) or path in self.known_paths:
            return
        self.known_paths.add(path)

        try:
            for entry in os.scandir(path):
                obj_type = "dir" if entry.is_dir() else "file"
                obj_size = entry.stat().st_size
                sig = f"FS: {entry.path} | type: {obj_type} | size={obj_size}"
                self._observe(sig)

                # Recursively scan directories
                if entry.is_dir():
                    self._scan_path(entry.path, depth + 1, max_depth)
        except Exception as e:
            self._observe(f"[FS Heuristic Error] {e} at {path}")

